import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

// ---------------------------------------------------------------------------
// API configuration
// ---------------------------------------------------------------------------

const String kBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://10.0.2.2:8080',
);

const Duration _kTimeout = Duration(seconds: 20);

// ---------------------------------------------------------------------------
// ApiResponse
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
// AuthTokenStore — persisted via flutter_secure_storage
// ---------------------------------------------------------------------------

class AuthTokenStore {
  static const _storage = FlutterSecureStorage();
  static String? _accessToken;
  static String? _refreshToken;

  static String? get accessToken => _accessToken;
  static String? get refreshToken => _refreshToken;
  static bool get hasToken => _accessToken != null;

  /// Call once at app startup in main() to restore tokens after app restart.
  static Future<void> load() async {
    _accessToken = await _storage.read(key: 'access_token');
    _refreshToken = await _storage.read(key: 'refresh_token');
  }

  /// Call after successful login or register.
  static Future<void> save({
    required String access,
    String? refresh,
  }) async {
    _accessToken = access;
    _refreshToken = refresh;
    await _storage.write(key: 'access_token', value: access);
    if (refresh != null) {
      await _storage.write(key: 'refresh_token', value: refresh);
    }
  }

  /// Call on logout.
  static Future<void> clear() async {
    _accessToken = null;
    _refreshToken = null;
    await _storage.deleteAll();
  }
}

// ---------------------------------------------------------------------------
// ApiService — thin HTTP client built on package:http (web-compatible)
// ---------------------------------------------------------------------------

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  Map<String, String> get _authHeaders => {
        'Content-Type': 'application/json',
        if (AuthTokenStore.hasToken)
          'Authorization': 'Bearer ${AuthTokenStore.accessToken}',
      };

  Future<ApiResponse<Map<String, dynamic>>> _request({
    required String method,
    required String path,
    Map<String, dynamic>? body,
    Map<String, String>? extraHeaders,
  }) async {
    try {
      final uri = Uri.parse('$kBaseUrl$path');
      final headers = {..._authHeaders, ...?extraHeaders};
      final encodedBody = body != null ? jsonEncode(body) : null;

      http.Response response;
      switch (method.toUpperCase()) {
        case 'POST':
          response = await http
              .post(uri, headers: headers, body: encodedBody)
              .timeout(_kTimeout);
          break;
        case 'PUT':
          response = await http
              .put(uri, headers: headers, body: encodedBody)
              .timeout(_kTimeout);
          break;
        case 'PATCH':
          response = await http
              .patch(uri, headers: headers, body: encodedBody)
              .timeout(_kTimeout);
          break;
        case 'DELETE':
          response = await http
              .delete(uri, headers: headers, body: encodedBody)
              .timeout(_kTimeout);
          break;
        default:
          response =
              await http.get(uri, headers: headers).timeout(_kTimeout);
      }

      if (response.statusCode >= 200 && response.statusCode < 300) {
        if (response.body.isEmpty) {
          return const ApiResponse.success(<String, dynamic>{});
        }
        final decoded = jsonDecode(response.body) as Map<String, dynamic>;
        return ApiResponse.success(decoded);
      } else {
        Map<String, dynamic>? decoded;
        try {
          decoded = jsonDecode(response.body) as Map<String, dynamic>;
        } catch (_) {}
        final message = decoded?['message'] as String? ??
            decoded?['error'] as String? ??
            'Request failed (${response.statusCode})';
        return ApiResponse.failure(message, statusCode: response.statusCode);
      }
    } on SocketException {
      return const ApiResponse.failure(
          'No internet connection. Please check your network.');
    } on http.ClientException catch (e) {
      return ApiResponse.failure('Network error: ${e.message}');
    } on FormatException {
      return const ApiResponse.failure(
          'Unexpected server response. Please try again.');
    } catch (e) {
      debugPrint('[ApiService] Unexpected error: $e');
      return ApiResponse.failure('Something went wrong. Please try again.');
    }
  }

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
      final request = http.MultipartRequest('POST', uri);

      if (AuthTokenStore.hasToken) {
        request.headers['Authorization'] =
            'Bearer ${AuthTokenStore.accessToken}';
      }

      fields?.forEach((key, value) {
        request.fields[key] = value;
      });

      request.files
          .add(await http.MultipartFile.fromPath(fieldName, filePath));

      final streamedResponse = await request.send().timeout(_kTimeout);
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode >= 200 && response.statusCode < 300) {
        final decoded = jsonDecode(response.body) as Map<String, dynamic>;
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
