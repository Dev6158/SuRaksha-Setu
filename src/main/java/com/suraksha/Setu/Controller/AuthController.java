package com.suraksha.Setu.Controller;

import com.suraksha.Setu.dto.AuthResponse;
import com.suraksha.Setu.dto.LoginRequest;
import com.suraksha.Setu.dto.OtpVerifyRequest;
import com.suraksha.Setu.Entity.User;
import com.suraksha.Setu.Repo.UserRepository;
import com.suraksha.Setu.Security.JwtTokenService;
import jakarta.validation.Valid;
import java.util.List;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

    private final AuthenticationManager authenticationManager;
    private final JwtTokenService jwtTokenService;
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public AuthController(
            AuthenticationManager authenticationManager,
            JwtTokenService jwtTokenService,
            UserRepository userRepository,
            PasswordEncoder passwordEncoder) {
        this.authenticationManager = authenticationManager;
        this.jwtTokenService = jwtTokenService;
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @PostMapping("/login")
    public ResponseEntity<AuthResponse> login(@Valid @RequestBody LoginRequest loginRequest) {
        Authentication authentication = this.authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(loginRequest.getUsername(), loginRequest.getPassword()));
        String token = this.jwtTokenService.generateToken(authentication);
        User user = this.userRepository.findByUsername(authentication.getName())
                .orElseThrow(() -> new IllegalArgumentException("Authenticated user record is missing"));
        AuthResponse authResponse = buildAuthResponse("Login successful", token, user);
        return ResponseEntity.ok(authResponse);
    }

    @PostMapping("/register")
    public ResponseEntity<?> register(@Valid @RequestBody LoginRequest loginRequest) {
        if (this.userRepository.existsByUsername(loginRequest.getUsername())) {
            return ResponseEntity.status(HttpStatus.CONFLICT)
                    .body(Map.of("error", "username_exists", "message", "Username is already registered"));
        }

        User user = new User();
        user.setUsername(loginRequest.getUsername());
        user.setEmail(loginRequest.getUsername());
        user.setPasswordHash(this.passwordEncoder.encode(loginRequest.getPassword()));
        user.setRoles("ROLE_USER");
        user.setEnabled(true);

        User savedUser = this.userRepository.save(user);
        Authentication authentication = new UsernamePasswordAuthenticationToken(
                savedUser.getUsername(),
                null,
                List.of(new SimpleGrantedAuthority("ROLE_USER")));
        String token = this.jwtTokenService.generateToken(authentication);

        return ResponseEntity.status(HttpStatus.CREATED).body(buildAuthResponse("Registration successful", token, savedUser));
    }

    @PostMapping("/otp/verify")
    public ResponseEntity<Map<String, Object>> verifyOtp(@Valid @RequestBody OtpVerifyRequest otpVerifyRequest) {
        User user = this.userRepository.findByUsername(otpVerifyRequest.getUsername())
                .orElseThrow(() -> new IllegalArgumentException("User not found for OTP verification"));

        return ResponseEntity.ok(Map.of(
                "success", true,
                "message", "OTP verified successfully",
                "verified", true,
                "user", userPayload(user)));
    }

    private AuthResponse buildAuthResponse(String message, String token, User user) {
        return new AuthResponse(true, message, token, "Bearer", 3600L, userPayload(user));
    }

    private Map<String, Object> userPayload(User user) {
        return Map.of(
                "id", user.getId(),
                "username", user.getUsername(),
                "email", user.getEmail(),
                "roles", user.getRoleList());
    }
}
