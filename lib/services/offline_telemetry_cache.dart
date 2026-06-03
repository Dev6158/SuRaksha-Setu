import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'api_service.dart';

// ---------------------------------------------------------------------------
// Hive box constants
// ---------------------------------------------------------------------------

const String _kBoxName = 'telemetry_cache';
const String _kPayloadKey = 'payload';
const String _kTimestampKey = 'ts';
const String _kSessionKey = 'session_id';
const String _kSyncedKey = 'synced';

// ---------------------------------------------------------------------------
// CachedPacket
// ---------------------------------------------------------------------------

class CachedPacket {
  final String id;
  final String sessionId;
  final String payload;
  final int timestamp;
  bool synced;

  CachedPacket({
    required this.id,
    required this.sessionId,
    required this.payload,
    required this.timestamp,
    this.synced = false,
  });

  Map<String, dynamic> toMap() => {
        _kPayloadKey: payload,
        _kTimestampKey: timestamp,
        _kSessionKey: sessionId,
        _kSyncedKey: synced ? 1 : 0,
      };

  factory CachedPacket.fromMap(String id, Map map) => CachedPacket(
        id: id,
        sessionId: map[_kSessionKey] as String? ?? '',
        payload: map[_kPayloadKey] as String? ?? '{}',
        timestamp: map[_kTimestampKey] as int? ?? 0,
        synced: (map[_kSyncedKey] as int? ?? 0) == 1,
      );
}

// ---------------------------------------------------------------------------
// OfflineTelemetryCache
// ---------------------------------------------------------------------------

/// Stores telemetry packets locally using Hive when the network is unavailable,
/// then automatically flushes the backlog to the backend once connectivity
/// is restored.
///
/// The batch upload endpoint is derived from [kBaseUrl] in api_service.dart,
/// so there is no hardcoded URL here.
class OfflineTelemetryCache extends ChangeNotifier {
  // ---- config --------------------------------------------------------------
  static String get _batchEndpoint =>
      '$kBaseUrl/api/v1/telemetry/batch';

  static const int _maxCachedPackets = 2000;
  static const Duration _syncInterval = Duration(seconds: 10);
  static const int _batchSize = 50;

  // ---- state ---------------------------------------------------------------
  late Box<Map> _box;
  bool _initialized = false;
  bool _isSyncing = false;
  int _pendingCount = 0;
  Timer? _syncTimer;
  StreamSubscription<List<InternetAddress>>? _connectivitySub;

  int get pendingCount => _pendingCount;
  bool get isSyncing => _isSyncing;

  // ---- initialization ------------------------------------------------------

  /// Must be called once at app startup after [Hive.initFlutter()].
  Future<void> init() async {
    if (_initialized) return;

    await Hive.initFlutter();

    // Production note: encrypt this box with a key from flutter_secure_storage.
    // See the commented block in the architecture doc for the exact key
    // derivation pattern using HiveAesCipher.
    _box = await Hive.openBox<Map>(_kBoxName);

    _pendingCount = _countPending();
    _initialized = true;

    _startSyncTimer();
    _listenForConnectivity();

    notifyListeners();
    debugPrint('[OfflineTelemetryCache] Initialized — pending: $_pendingCount');
  }

  // ---- public API ----------------------------------------------------------

  Future<void> savePacket({
    required String sessionId,
    required String payload,
  }) async {
    _assertInitialized();

    final String id =
        '${sessionId}_${DateTime.now().millisecondsSinceEpoch}';
    final CachedPacket packet = CachedPacket(
      id: id,
      sessionId: sessionId,
      payload: payload,
      timestamp: DateTime.now().millisecondsSinceEpoch,
    );

    await _box.put(id, packet.toMap());
    _pendingCount++;

    if (_box.length > _maxCachedPackets) {
      await _pruneOldest();
    }

    notifyListeners();
    debugPrint(
        '[OfflineTelemetryCache] Saved packet $id — total pending: $_pendingCount');
  }

  Future<void> forceSync() async => _flushPendingPackets();

  Future<void> clearAll() async {
    _assertInitialized();
    await _box.clear();
    _pendingCount = 0;
    notifyListeners();
    debugPrint('[OfflineTelemetryCache] All records cleared');
  }

  List<CachedPacket> getPendingPackets() {
    _assertInitialized();
    final List<CachedPacket> pending = [];
    for (final String key in _box.keys.cast<String>()) {
      final Map? raw = _box.get(key);
      if (raw == null) continue;
      final CachedPacket packet = CachedPacket.fromMap(key, raw);
      if (!packet.synced) pending.add(packet);
    }
    pending.sort((a, b) => a.timestamp.compareTo(b.timestamp));
    return pending;
  }

  // ---- sync logic ----------------------------------------------------------

  void _startSyncTimer() {
    _syncTimer?.cancel();
    _syncTimer = Timer.periodic(
        _syncInterval, (_) async => _flushPendingPackets());
  }

  void _listenForConnectivity() {
    _connectivitySub = Stream.periodic(const Duration(seconds: 5))
        .asyncMap((_) => InternetAddress.lookup('google.com'))
        .where((List<InternetAddress> addresses) =>
            addresses.isNotEmpty && addresses.first.rawAddress.isNotEmpty)
        .listen((List<InternetAddress> _) async {
      if (_pendingCount > 0 && !_isSyncing) {
        debugPrint('[OfflineTelemetryCache] Connectivity detected — flushing backlog');
        await _flushPendingPackets();
      }
    }, onError: (_) {
      // No connectivity — silently ignore
    });
  }

  Future<void> _flushPendingPackets() async {
    if (_isSyncing || !_initialized) return;

    final List<CachedPacket> pending = getPendingPackets();
    if (pending.isEmpty) return;

    _isSyncing = true;
    notifyListeners();
    debugPrint(
        '[OfflineTelemetryCache] Flushing ${pending.length} packets in batches of $_batchSize');

    int successCount = 0;

    for (int i = 0; i < pending.length; i += _batchSize) {
      final int end = (i + _batchSize < pending.length)
          ? i + _batchSize
          : pending.length;
      final List<CachedPacket> batch = pending.sublist(i, end);

      final bool batchOk = await _postBatch(batch);
      if (batchOk) {
        for (final CachedPacket packet in batch) {
          await _box.delete(packet.id);
          successCount++;
        }
      } else {
        debugPrint(
            '[OfflineTelemetryCache] Batch POST failed — will retry next cycle');
        break;
      }
    }

    _pendingCount = _countPending();
    _isSyncing = false;
    notifyListeners();
    debugPrint(
        '[OfflineTelemetryCache] Flush complete — synced $successCount, remaining: $_pendingCount');
  }

  Future<bool> _postBatch(List<CachedPacket> batch) async {
    try {
      final HttpClient client = HttpClient()
        ..connectionTimeout = const Duration(seconds: 8);

      final HttpClientRequest request =
          await client.postUrl(Uri.parse(_batchEndpoint));

      request.headers.set(HttpHeaders.contentTypeHeader, 'application/json');

      // Forward the auth token if available
      if (AuthTokenStore.hasToken) {
        request.headers.set(
          HttpHeaders.authorizationHeader,
          'Bearer ${AuthTokenStore.accessToken}',
        );
      }

      final List<Map<String, dynamic>> payloads = batch
          .map((p) => jsonDecode(p.payload) as Map<String, dynamic>)
          .toList();

      request.write(jsonEncode({'packets': payloads}));

      final HttpClientResponse response = await request.close();
      await response.drain<void>();
      client.close();

      debugPrint(
          '[OfflineTelemetryCache] Batch POST → HTTP ${response.statusCode}');
      return response.statusCode >= 200 && response.statusCode < 300;
    } on SocketException catch (e) {
      debugPrint('[OfflineTelemetryCache] Network unreachable: $e');
      return false;
    } on HttpException catch (e) {
      debugPrint('[OfflineTelemetryCache] HTTP error: $e');
      return false;
    } catch (e) {
      debugPrint('[OfflineTelemetryCache] Unexpected error during POST: $e');
      return false;
    }
  }

  // ---- helpers -------------------------------------------------------------

  int _countPending() {
    if (!_initialized) return 0;
    int count = 0;
    for (final String key in _box.keys.cast<String>()) {
      final Map? raw = _box.get(key);
      if (raw != null && (raw[_kSyncedKey] as int? ?? 0) == 0) count++;
    }
    return count;
  }

  Future<void> _pruneOldest() async {
    final List<String> keys = _box.keys.cast<String>().toList();
    if (keys.isEmpty) return;

    final List<MapEntry<String, int>> timestamped = [];
    for (final String k in keys) {
      final Map? raw = _box.get(k);
      if (raw != null) {
        timestamped
            .add(MapEntry(k, raw[_kTimestampKey] as int? ?? 0));
      }
    }
    timestamped.sort((a, b) => a.value.compareTo(b.value));

    final int deleteCount = (timestamped.length * 0.1).ceil();
    for (int i = 0; i < deleteCount && i < timestamped.length; i++) {
      await _box.delete(timestamped[i].key);
    }
    debugPrint('[OfflineTelemetryCache] Pruned $deleteCount old records');
  }

  void _assertInitialized() {
    if (!_initialized) {
      throw StateError(
          '[OfflineTelemetryCache] init() must be called before use.');
    }
  }

  @override
  void dispose() {
    _syncTimer?.cancel();
    _connectivitySub?.cancel();
    _box.close();
    super.dispose();
  }
}