import 'api_service.dart';

// ---------------------------------------------------------------------------
// Auth models
// ---------------------------------------------------------------------------

class LoginRequest {
  final String email;
  final String password;
  final bool rememberMe;

  const LoginRequest({
    required this.email,
    required this.password,
    this.rememberMe = false,
  });

  Map<String, dynamic> toJson() => {
        'email': email,
        'password': password,
        'remember_me': rememberMe,
      };
}

class RegisterRequest {
  final String firstName;
  final String lastName;
  final String email;
  final String phone;
  final String password;

  const RegisterRequest({
    required this.firstName,
    required this.lastName,
    required this.email,
    required this.phone,
    required this.password,
  });

  Map<String, dynamic> toJson() => {
        'first_name': firstName,
        'last_name': lastName,
        'email': email,
        'phone': phone,
        'password': password,
      };
}

class AuthResult {
  final String userId;
  final String sessionId;
  final String accessToken;
  final String refreshToken;
  final String displayName;
  final String maskedAccountNumber;

  const AuthResult({
    required this.userId,
    required this.sessionId,
    required this.accessToken,
    required this.refreshToken,
    required this.displayName,
    required this.maskedAccountNumber,
  });

  factory AuthResult.fromJson(Map<String, dynamic> json) => AuthResult(
        userId: json['user_id'] as String,
        sessionId: json['session_id'] as String,
        accessToken: json['access_token'] as String,
        refreshToken: json['refresh_token'] as String,
        displayName: json['display_name'] as String,
        maskedAccountNumber: json['masked_account_number'] as String,
      );
}

// ---------------------------------------------------------------------------
// AuthService
// ---------------------------------------------------------------------------

class AuthService {
  static final AuthService _instance = AuthService._internal();
  factory AuthService() => _instance;
  AuthService._internal();

  final _api = ApiService();

  // ---- login ---------------------------------------------------------------

  Future<ApiResponse<AuthResult>> login(LoginRequest request) async {
    final response = await _api.post(
      '/api/v1/auth/login',
      body: request.toJson(),
    );

    if (!response.isSuccess) {
      return ApiResponse.failure(response.error, statusCode: response.statusCode);
    }

    try {
      final result = AuthResult.fromJson(response.data!);
      AuthTokenStore.save(
        access: result.accessToken,
        refresh: result.refreshToken,
      );
      return ApiResponse.success(result);
    } catch (_) {
      return const ApiResponse.failure('Unexpected response from server.');
    }
  }

  // ---- register ------------------------------------------------------------

  Future<ApiResponse<AuthResult>> register(RegisterRequest request) async {
    final response = await _api.post(
      '/api/v1/auth/register',
      body: request.toJson(),
    );

    if (!response.isSuccess) {
      return ApiResponse.failure(response.error, statusCode: response.statusCode);
    }

    try {
      final result = AuthResult.fromJson(response.data!);
      AuthTokenStore.save(
        access: result.accessToken,
        refresh: result.refreshToken,
      );
      return ApiResponse.success(result);
    } catch (_) {
      return const ApiResponse.failure('Unexpected response from server.');
    }
  }

  // ---- logout --------------------------------------------------------------

  Future<void> logout() async {
    try {
      await _api.post('/api/v1/auth/logout');
    } catch (_) {
      // Best-effort; always clear tokens locally
    } finally {
      AuthTokenStore.clear();
    }
  }

  // ---- token refresh -------------------------------------------------------

  Future<bool> refreshAccessToken() async {
    final refreshToken = AuthTokenStore.refreshToken;
    if (refreshToken == null) return false;

    final response = await _api.post(
      '/api/v1/auth/refresh',
      body: {'refresh_token': refreshToken},
    );

    if (!response.isSuccess) return false;

    final newAccess = response.data?['access_token'] as String?;
    final newRefresh = response.data?['refresh_token'] as String?;

    if (newAccess == null || newRefresh == null) return false;

    AuthTokenStore.save(access: newAccess, refresh: newRefresh);
    return true;
  }
}