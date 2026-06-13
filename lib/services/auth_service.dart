import 'api_service.dart';

// ---------------------------------------------------------------------------
// Auth models — these define the SHAPE the rest of the app uses.
// The backend's actual field names may differ; AuthService maps between
// them so the rest of the app never has to know about the backend's
// raw response shape.
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

  /// The backend currently expects `username` + `password`.
  /// We send both `email` and `username` (mirroring email) so it
  /// works regardless of which field the backend reads.
  Map<String, dynamic> toJson() => {
        'email': email,
        'username': email,
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

  /// Send both snake_case and camelCase + a `username` alias so this
  /// works against the current backend without requiring backend changes.
  Map<String, dynamic> toJson() => {
        'first_name': firstName,
        'last_name': lastName,
        'firstName': firstName,
        'lastName': lastName,
        'email': email,
        'username': email,
        'phone': phone,
        'password': password,
      };
}

class AuthResult {
  final String userId;
  final String sessionId;
  final String accessToken;
  final String? refreshToken;
  final String displayName;
  final String maskedAccountNumber;
  final String avatarInitials;

  const AuthResult({
    required this.userId,
    required this.sessionId,
    required this.accessToken,
    this.refreshToken,
    required this.displayName,
    required this.maskedAccountNumber,
    required this.avatarInitials,
  });

  /// Maps the backend's actual response shape into the shape the rest
  /// of the app expects.
  ///
  /// Backend currently returns something like:
  /// ```json
  /// {
  ///   "token": "...",
  ///   "accessToken": "...",
  ///   "user": {
  ///     "id": "...",
  ///     "username": "...",
  ///     "email": "...",
  ///     "firstName": "...",
  ///     "lastName": "..."
  ///   }
  /// }
  /// ```
  ///
  /// This factory reads from BOTH the new contract field names
  /// (snake_case, top-level) AND the backend's current field names
  /// (camelCase, nested under "user"), so it works either way without
  /// requiring backend changes first.
  factory AuthResult.fromJson(Map<String, dynamic> json) {
    // Nested user object, if present (current backend shape)
    final Map<String, dynamic> user =
        (json['user'] as Map<String, dynamic>?) ?? const {};

    // ---- access token --------------------------------------------------
    final String accessToken = (json['access_token'] ??
            json['accessToken'] ??
            json['token'] ??
            '') as String;

    // ---- refresh token (optional) --------------------------------------
    final String? refreshToken =
        (json['refresh_token'] ?? json['refreshToken']) as String?;

    // ---- user id ----------------------------------------------------------
    final String userId = (json['user_id'] ??
            json['userId'] ??
            user['id'] ??
            user['user_id'] ??
            user['userId'] ??
            '') as String;

    // ---- session id --------------------------------------------------------
    // Falls back to userId if backend doesn't issue a separate session id.
    final String sessionId = (json['session_id'] ??
            json['sessionId'] ??
            user['session_id'] ??
            userId) as String;

    // ---- display name --------------------------------------------------------
    String displayName = (json['display_name'] ?? json['displayName']) as String? ??
        '';
    if (displayName.isEmpty) {
      final String firstName =
          (user['first_name'] ?? user['firstName'] ?? '') as String;
      final String lastName =
          (user['last_name'] ?? user['lastName'] ?? '') as String;
      final String combined = [firstName, lastName]
          .where((s) => s.isNotEmpty)
          .join(' ')
          .trim();
      displayName = combined.isNotEmpty
          ? combined
          : (user['username'] ?? user['email'] ?? 'User') as String;
    }

    // ---- masked account number --------------------------------------------------------
    final String maskedAccountNumber = (json['masked_account_number'] ??
            json['maskedAccountNumber'] ??
            user['masked_account_number'] ??
            user['maskedAccountNumber'] ??
            '---- ---- ---- ----') as String;

    // ---- avatar initials --------------------------------------------------------
    String avatarInitials = (json['avatar_initials'] ??
            json['avatarInitials']) as String? ??
        '';
    if (avatarInitials.isEmpty) {
      avatarInitials = _deriveInitials(displayName);
    }

    return AuthResult(
      userId: userId,
      sessionId: sessionId,
      accessToken: accessToken,
      refreshToken: refreshToken,
      displayName: displayName,
      maskedAccountNumber: maskedAccountNumber,
      avatarInitials: avatarInitials,
    );
  }

  static String _deriveInitials(String name) {
    final parts = name.trim().split(' ').where((p) => p.isNotEmpty).toList();
    if (parts.isEmpty) return '?';
    if (parts.length == 1) return parts.first[0].toUpperCase();
    return '${parts.first[0]}${parts.last[0]}'.toUpperCase();
  }
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
      if (result.accessToken.isEmpty) {
        return const ApiResponse.failure(
            'Login succeeded but no access token was returned.');
      }
      await AuthTokenStore.save(
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
      if (result.accessToken.isEmpty) {
        return const ApiResponse.failure(
            'Registration succeeded but no access token was returned.');
      }
      await AuthTokenStore.save(
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
      await AuthTokenStore.clear();
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

    final newAccess = (response.data?['access_token'] ??
        response.data?['accessToken'] ??
        response.data?['token']) as String?;
    final newRefresh = (response.data?['refresh_token'] ??
        response.data?['refreshToken']) as String?;

    if (newAccess == null) return false;

    await AuthTokenStore.save(access: newAccess, refresh: newRefresh);
    return true;
  }
}
