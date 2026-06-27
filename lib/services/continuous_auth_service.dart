import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:sensors_plus/sensors_plus.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:web_socket_channel/io.dart';

import 'api_service.dart';

// ---------------------------------------------------------------------------
// WebSocket endpoint — resolved from the same base URL as the REST API.
// ws:// or wss:// is inferred automatically from http/https.
// ---------------------------------------------------------------------------

String _telemetryWsUrl() {
  final base = kBaseUrl
      .replaceFirst('https://', 'wss://')
      .replaceFirst('http://', 'ws://');
  return '$base/api/v1/telemetry/stream';
}

// ---------------------------------------------------------------------------
// Data models — internal to this file
// ---------------------------------------------------------------------------

class _AccelSample {
  final double x, y, z;
  final int timestamp;
  _AccelSample(this.x, this.y, this.z, this.timestamp);
  Map<String, dynamic> toJson() => {'x': x, 'y': y, 'z': z, 'ts': timestamp};
}

class _GyroSample {
  final double x, y, z;
  final int timestamp;
  _GyroSample(this.x, this.y, this.z, this.timestamp);
  Map<String, dynamic> toJson() => {'x': x, 'y': y, 'z': z, 'ts': timestamp};
}

class _SwipeVector {
  final double startX, startY, endX, endY;
  final int durationMs;
  final double velocity;
  _SwipeVector({
    required this.startX,
    required this.startY,
    required this.endX,
    required this.endY,
    required this.durationMs,
    required this.velocity,
  });
  Map<String, dynamic> toJson() => {
        'start_x': startX,
        'start_y': startY,
        'end_x': endX,
        'end_y': endY,
        'duration_ms': durationMs,
        'velocity': velocity,
      };
}

class _TapEvent {
  final double x, y;
  final int timestamp;
  _TapEvent(this.x, this.y, this.timestamp);
  Map<String, dynamic> toJson() => {'x': x, 'y': y, 'ts': timestamp};
}

class _KeyInterval {
  final int intervalMs;
  final int timestamp;
  _KeyInterval(this.intervalMs, this.timestamp);
  Map<String, dynamic> toJson() => {'interval_ms': intervalMs, 'ts': timestamp};
}

// ---------------------------------------------------------------------------
// TelemetryPacket
// ---------------------------------------------------------------------------

class TelemetryPacket {
  final String sessionId;
  final String userId;
  final int packetTimestamp;
  final List<_AccelSample> accelSamples;
  final List<_GyroSample> gyroSamples;
  final List<_SwipeVector> swipeVectors;
  final List<_TapEvent> tapEvents;
  final List<_KeyInterval> keyIntervals;

  TelemetryPacket({
    required this.sessionId,
    required this.userId,
    required this.packetTimestamp,
    required this.accelSamples,
    required this.gyroSamples,
    required this.swipeVectors,
    required this.tapEvents,
    required this.keyIntervals,
  });

  Map<String, dynamic> toJson() => {
        'session_id': sessionId,
        'user_id': userId,
        'packet_ts': packetTimestamp,
        'accel': accelSamples.map((s) => s.toJson()).toList(),
        'gyro': gyroSamples.map((s) => s.toJson()).toList(),
        'swipes': swipeVectors.map((s) => s.toJson()).toList(),
        'taps': tapEvents.map((t) => t.toJson()).toList(),
        'key_intervals': keyIntervals.map((k) => k.toJson()).toList(),
      };

  String toJsonString() => jsonEncode(toJson());
}

// ---------------------------------------------------------------------------
// ContinuousAuthService
// ---------------------------------------------------------------------------

/// Silent background service that:
///  1. Reads accelerometer + gyroscope via sensors_plus
///  2. Tracks swipe trajectories, tap coordinates, and keystroke intervals
///  3. Maintains a persistent WebSocket connection to the backend
///  4. Bundles collected data into [TelemetryPacket]s every 100 ms
///
/// Accepts [sessionId] and [userId] from the login response — never
/// hardcoded. The WebSocket URL is derived from [kBaseUrl] defined in
/// api_service.dart.
class ContinuousAuthService extends ChangeNotifier {
  // ---- config --------------------------------------------------------------
  static const Duration _pollInterval = Duration(milliseconds: 100);
  static const Duration _reconnectDelay = Duration(seconds: 3);

  // ---- public state --------------------------------------------------------
  bool get isConnected => _channel != null && !_isClosed;
  String get sessionId => _sessionId;

  // ---- private fields ------------------------------------------------------
  final String _sessionId;
  final String _userId;

  // sensor buffers
  final List<_AccelSample> _accelBuffer = [];
  final List<_GyroSample> _gyroBuffer = [];

  // interaction buffers
  final List<_SwipeVector> _swipeBuffer = [];
  final List<_TapEvent> _tapBuffer = [];
  final List<_KeyInterval> _keyBuffer = [];

  // gesture tracking
  Offset? _pointerDownPosition;
  int _pointerDownTime = 0;
  int _lastKeyUpTime = 0;

  // sensor subscriptions
  StreamSubscription<AccelerometerEvent>? _accelSub;
  StreamSubscription<GyroscopeEvent>? _gyroSub;

  // websocket
  WebSocketChannel? _channel;
  bool _isClosed = false;
  bool _isReconnecting = false;

  // timers
  Timer? _pollTimer;
  Timer? _reconnectTimer;

  // ---- constructor ---------------------------------------------------------

  ContinuousAuthService({
    required String sessionId,
    required String userId,
  })  : _sessionId = sessionId,
        _userId = userId;

  // ---- lifecycle -----------------------------------------------------------

  Future<void> start() async {
    _isClosed = false;
    _bindSensors();
    await _connectWebSocket();
    _startPolling();
  }

  void stop() {
    _isClosed = true;
    _pollTimer?.cancel();
    _reconnectTimer?.cancel();
    _accelSub?.cancel();
    _gyroSub?.cancel();
    _channel?.sink.close(WebSocketStatus.normalClosure);
    _channel = null;
    notifyListeners();
  }

  // ---- sensor binding ------------------------------------------------------

  void _bindSensors() {
    _accelSub = accelerometerEventStream(
      samplingPeriod: SensorInterval.gameInterval,
    ).listen(
      (AccelerometerEvent event) {
        _accelBuffer.add(_AccelSample(
          event.x,
          event.y,
          event.z,
          DateTime.now().millisecondsSinceEpoch,
        ));
      },
      onError: (Object error) =>
          debugPrint('[ContinuousAuthService] Accelerometer error: $error'),
      cancelOnError: false,
    );

    _gyroSub = gyroscopeEventStream(
      samplingPeriod: SensorInterval.gameInterval,
    ).listen(
      (GyroscopeEvent event) {
        _gyroBuffer.add(_GyroSample(
          event.x,
          event.y,
          event.z,
          DateTime.now().millisecondsSinceEpoch,
        ));
      },
      onError: (Object error) =>
          debugPrint('[ContinuousAuthService] Gyroscope error: $error'),
      cancelOnError: false,
    );
  }

  // ---- interaction tracking ------------------------------------------------

  void onPointerDown(PointerDownEvent event) {
    _pointerDownPosition = event.position;
    _pointerDownTime = DateTime.now().millisecondsSinceEpoch;
    _tapBuffer.add(_TapEvent(
      event.position.dx,
      event.position.dy,
      _pointerDownTime,
    ));
  }

  void onPointerUp(PointerUpEvent event) {
    if (_pointerDownPosition == null) return;

    final int now = DateTime.now().millisecondsSinceEpoch;
    final int durationMs = now - _pointerDownTime;
    final Offset start = _pointerDownPosition!;
    final Offset end = event.position;
    final double distance = (end - start).distance;

    if (distance > 10.0) {
      final double velocity =
          durationMs > 0 ? distance / durationMs * 1000 : 0;
      _swipeBuffer.add(_SwipeVector(
        startX: start.dx,
        startY: start.dy,
        endX: end.dx,
        endY: end.dy,
        durationMs: durationMs,
        velocity: velocity,
      ));
    }

    _pointerDownPosition = null;
  }

  void onKeystroke() {
    final int now = DateTime.now().millisecondsSinceEpoch;
    if (_lastKeyUpTime > 0) {
      final int interval = now - _lastKeyUpTime;
      if (interval < 5000) {
        _keyBuffer.add(_KeyInterval(interval, now));
      }
    }
    _lastKeyUpTime = now;
  }

  // ---- websocket -----------------------------------------------------------

  Future<void> _connectWebSocket() async {
    if (_isClosed) return;
    try {
      _channel = IOWebSocketChannel.connect(
        Uri.parse(_telemetryWsUrl()),
        connectTimeout: const Duration(seconds: 5),
        headers: {
          'X-Session-Id': _sessionId,
          'X-User-Id': _userId,
          if (AuthTokenStore.hasToken)
            'Authorization': 'Bearer ${AuthTokenStore.accessToken}',
        },
      );

      _channel!.stream.listen(
        _onServerMessage,
        onError: _onWebSocketError,
        onDone: _onWebSocketClosed,
        cancelOnError: false,
      );

      debugPrint('[ContinuousAuthService] WebSocket connected to ${_telemetryWsUrl()}');
      notifyListeners();
    } catch (e) {
      debugPrint('[ContinuousAuthService] WebSocket connect failed: $e');
      _scheduleReconnect();
    }
  }

  void _onServerMessage(dynamic raw) {
    // Backend may push risk-score updates; downstream listeners handle these.
    debugPrint('[ContinuousAuthService] Server message: $raw');
  }

  void _onWebSocketError(Object error) {
    debugPrint('[ContinuousAuthService] WebSocket error: $error');
    _scheduleReconnect();
  }

  void _onWebSocketClosed() {
    debugPrint('[ContinuousAuthService] WebSocket closed');
    if (!_isClosed) _scheduleReconnect();
  }

  void _scheduleReconnect() {
    if (_isClosed || _isReconnecting) return;
    _isReconnecting = true;
    _channel = null;
    notifyListeners();
    _reconnectTimer = Timer(_reconnectDelay, () async {
      _isReconnecting = false;
      await _connectWebSocket();
    });
  }

  // ---- polling loop --------------------------------------------------------

  void _startPolling() {
    _pollTimer = Timer.periodic(_pollInterval, (_) => _flushPacket());
  }

  void _flushPacket() {
    if (_channel == null || _isClosed) return;

    final List<_AccelSample> accel = List.from(_accelBuffer);
    final List<_GyroSample> gyro = List.from(_gyroBuffer);
    final List<_SwipeVector> swipes = List.from(_swipeBuffer);
    final List<_TapEvent> taps = List.from(_tapBuffer);
    final List<_KeyInterval> keys = List.from(_keyBuffer);

    _accelBuffer.clear();
    _gyroBuffer.clear();
    _swipeBuffer.clear();
    _tapBuffer.clear();
    _keyBuffer.clear();

    final bool hasData = accel.isNotEmpty ||
        gyro.isNotEmpty ||
        swipes.isNotEmpty ||
        taps.isNotEmpty ||
        keys.isNotEmpty;

    if (!hasData) return;

    final TelemetryPacket packet = TelemetryPacket(
      sessionId: _sessionId,
      userId: _userId,
      packetTimestamp: DateTime.now().millisecondsSinceEpoch,
      accelSamples: accel,
      gyroSamples: gyro,
      swipeVectors: swipes,
      tapEvents: taps,
      keyIntervals: keys,
    );

    try {
      _channel!.sink.add(packet.toJsonString());
    } catch (e) {
      debugPrint('[ContinuousAuthService] Send failed: $e');
      _scheduleReconnect();
    }
  }

  // ---- tracker widget wrapper ----------------------------------------------

  Widget buildTrackerWrapper({required Widget child}) {
    return Listener(
      behavior: HitTestBehavior.translucent,
      onPointerDown: onPointerDown,
      onPointerUp: onPointerUp,
      child: child,
    );
  }
}