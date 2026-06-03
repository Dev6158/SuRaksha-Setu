import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';

// ---------------------------------------------------------------------------
// API configuration
// ---------------------------------------------------------------------------

/// Replace with your actual backend base URL.
/// On Android emulator: http://10.0.2.2:8080
/// On iOS simulator:    http://127.0.0.1:8080
const String kBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://10.0.2.2:8080',
);

const Duration _kConnectTimeout = Duration(seconds: 10);
const Duration _kReceiveTimeout = Duration(seconds: 20);

// ---------------------------------------------------------------------------
// ApiResponse — typed wrapper around every HTTP call
// ---------------------------------------------------------------------------

class ApiResponse<T> {
  final T? data;
  final String? error;
  final int? statusCode;

  bool get isSuccess => error == null && data != null;

  const ApiResponse.success(this.data)
      : error = null,
        statusCode = null;

  const ApiResponse.failure(this.error, {this.statusCode}) : data = null;
}

// ---------------------------------------------------------------------------
// AuthTokenStore — in-memory token holder (swap for flutter_secure_storage)
// ---------------------------------------------------------------------------

class AuthTokenStore {
  static String? _accessToken;
  static String? _refreshToken;

  static String? get accessToken => _accessToken;
  static String? get refreshToken => _refreshToken;

  static void save({required String access, required String refresh}) {
    _accessToken = access;
    _refreshToken = refresh;
  }

  static void clear() {
    _accessToken = null;
    _refreshToken = null;
  }

  static bool get hasToken => _accessToken != null;
}

// ---------------------------------------------------------------------------
// ApiService — thin HTTP client
// ---------------------------------------------------------------------------

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  // ---- internal helpers ----------------------------------------------------

  Map<String, String> get _authHeaders => {
        HttpHeaders.contentTypeHeader: 'application/json',
        if (AuthTokenStore.hasToken)
          HttpHeaders.authorizationHeader: 'Bearer ${AuthTokenStore.accessToken}',
      };

  Future<HttpClient> _client() async {
    final client = HttpClient()
      ..connectionTimeout = _kConnectTimeout
      ..idleTimeout = _kReceiveTimeout;
    return client;
  }

  Future<ApiResponse<Map<String, dynamic>>> _request({
    required String method,
    required String path,
    Map<String, dynamic>? body,
    Map<String, String>? extraHeaders,
  }) async {
    try {
      final uri = Uri.parse('$kBaseUrl$path');
      final client = await _client();
      late HttpClientRequest request;

      switch (method.toUpperCase()) {
        case 'POST':
          request = await client.postUrl(uri);
          break;
        case 'PUT':
          request = await client.putUrl(uri);
          break;
        case 'PATCH':
          request = await client.patchUrl(uri);
          break;
        case 'DELETE':
          request = await client.deleteUrl(uri);
          break;
        default:
          request = await client.getUrl(uri);
      }

      _authHeaders.forEach(request.headers.set);
      extraHeaders?.forEach(request.headers.set);

      if (body != null) {
        request.write(jsonEncode(body));
      }

      final response = await request.close();
      final responseBody = await response.transform(utf8.decoder).join();
      client.close();

      if (response.statusCode >= 200 && response.statusCode < 300) {
        final decoded = jsonDecode(responseBody) as Map<String, dynamic>;
        return ApiResponse.success(decoded);
      } else {
        Map<String, dynamic>? decoded;
        try {
          decoded = jsonDecode(responseBody) as Map<String, dynamic>;
        } catch (_) {}
        final message = decoded?['message'] as String? ??
            decoded?['error'] as String? ??
            'Request failed (${response.statusCode})';
        return ApiResponse.failure(message, statusCode: response.statusCode);
      }
    } on SocketException {
      return const ApiResponse.failure('No internet connection. Please check your network.');
    } on HttpException catch (e) {
      return ApiResponse.failure('Network error: ${e.message}');
    } on FormatException {
      return const ApiResponse.failure('Unexpected server response. Please try again.');
    } catch (e) {
      debugPrint('[ApiService] Unexpected error: $e');
      return ApiResponse.failure('Something went wrong. Please try again.');
    }
  }

  // ---- public API ----------------------------------------------------------

  Future<ApiResponse<Map<String, dynamic>>> get(String path) =>
      _request(method: 'GET', path: path);

  Future<ApiResponse<Map<String, dynamic>>> post(
    String path, {
    Map<String, dynamic>? body,
  }) =>
      _request(method: 'POST', path: path, body: body);

  Future<ApiResponse<Map<String, dynamic>>> put(
    String path, {
    Map<String, dynamic>? body,
  }) =>
      _request(method: 'PUT', path: path, body: body);

  Future<ApiResponse<Map<String, dynamic>>> patch(
    String path, {
    Map<String, dynamic>? body,
  }) =>
      _request(method: 'PATCH', path: path, body: body);

  Future<ApiResponse<Map<String, dynamic>>> delete(String path) =>
      _request(method: 'DELETE', path: path);

  // ---- multipart (for file uploads) ----------------------------------------

  Future<ApiResponse<Map<String, dynamic>>> uploadFile({
    required String path,
    required String filePath,
    required String fieldName,
    Map<String, String>? fields,
  }) async {
    try {
      final uri = Uri.parse('$kBaseUrl$path');
      final client = await _client();
      final request = await client.postUrl(uri);

      if (AuthTokenStore.hasToken) {
        request.headers.set(
          HttpHeaders.authorizationHeader,
          'Bearer ${AuthTokenStore.accessToken}',
        );
      }

      final boundary = 'boundary${DateTime.now().millisecondsSinceEpoch}';
      request.headers.set(
        HttpHeaders.contentTypeHeader,
        'multipart/form-data; boundary=$boundary',
      );

      final file = File(filePath);
      final fileBytes = await file.readAsBytes();
      final fileName = file.path.split('/').last;

      final buffer = StringBuffer();

      // Add extra fields
      fields?.forEach((key, value) {
        buffer.write('--$boundary\r\n');
        buffer.write('Content-Disposition: form-data; name="$key"\r\n\r\n');
        buffer.write('$value\r\n');
      });

      // File part header
      buffer.write('--$boundary\r\n');
      buffer.write(
        'Content-Disposition: form-data; name="$fieldName"; filename="$fileName"\r\n',
      );
      buffer.write('Content-Type: application/octet-stream\r\n\r\n');

      request.write(buffer.toString());
      request.add(fileBytes);
      request.write('\r\n--$boundary--\r\n');

      final response = await request.close();
      final responseBody = await response.transform(utf8.decoder).join();
      client.close();

      if (response.statusCode >= 200 && response.statusCode < 300) {
        final decoded = jsonDecode(responseBody) as Map<String, dynamic>;
        return ApiResponse.success(decoded);
      } else {
        return ApiResponse.failure(
          'Upload failed (${response.statusCode})',
          statusCode: response.statusCode,
        );
      }
    } on SocketException {
      return const ApiResponse.failure('No internet connection.');
    } catch (e) {
      return ApiResponse.failure('Upload error: $e');
    }
  }
}