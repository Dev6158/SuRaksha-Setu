package com.suraksha.Setu.Controller;

import com.suraksha.Setu.dto.AuthResponse;
import com.suraksha.Setu.dto.LoginRequest;
import com.suraksha.Setu.Entity.User;
import com.suraksha.Setu.Repo.UserRepository;
import com.suraksha.Setu.Security.JwtTokenService;
import jakarta.validation.Valid;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
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
        AuthResponse authResponse = new AuthResponse(token, "Bearer", 3600L);
        return ResponseEntity.ok(authResponse);
    }

    @PostMapping("/register")
    public ResponseEntity<Map<String, Object>> register(@Valid @RequestBody LoginRequest loginRequest) {
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
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(Map.of("id", savedUser.getId(), "username", savedUser.getUsername()));
    }
}
