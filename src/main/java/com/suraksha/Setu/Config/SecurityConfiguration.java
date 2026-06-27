package com.suraksha.Setu.Config;

import com.suraksha.Setu.Security.CustomJwtAuthenticationFilter;
import java.util.List;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.dao.DaoAuthenticationProvider;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.AuthenticationEntryPoint;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.access.AccessDeniedHandler;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

@Configuration
@EnableWebSecurity
@EnableMethodSecurity
public class SecurityConfiguration {

    private final CustomJwtAuthenticationFilter customJwtAuthenticationFilter;
    private final UserDetailsService userDetailsService;
    private final AccessDeniedHandler accessDeniedHandler;
    private final AuthenticationEntryPoint authenticationEntryPoint;

    public SecurityConfiguration(
            CustomJwtAuthenticationFilter customJwtAuthenticationFilter,
            UserDetailsService userDetailsService,
            AccessDeniedHandler accessDeniedHandler,
            AuthenticationEntryPoint authenticationEntryPoint) {
        this.customJwtAuthenticationFilter = customJwtAuthenticationFilter;
        this.userDetailsService = userDetailsService;
        this.accessDeniedHandler = accessDeniedHandler;
        this.authenticationEntryPoint = authenticationEntryPoint;
    }

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity httpSecurity) throws Exception {
        httpSecurity
                .csrf(csrfConfigurer -> csrfConfigurer.disable())
                .cors(corsConfigurer -> corsConfigurer.configurationSource(corsConfigurationSource()))
                .sessionManagement(sessionManagementConfigurer ->
                        sessionManagementConfigurer.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authenticationProvider(daoAuthenticationProvider())
                .exceptionHandling(exceptionHandlingConfigurer -> exceptionHandlingConfigurer
                        .accessDeniedHandler(this.accessDeniedHandler)
                        .authenticationEntryPoint(this.authenticationEntryPoint))
                .authorizeHttpRequests(authorizationManagerRequestMatcherRegistry ->
                        authorizationManagerRequestMatcherRegistry
                                .requestMatchers(HttpMethod.OPTIONS, "/**").permitAll()
                                .requestMatchers("/api/v1/auth/register","/api/v1/auth/login","/api/v1/auth/otp/verify","/api/v1/ai/**","/swagger-ui/**","/swagger-ui.html","/v3/api-docs/**","/api/v1/documents/types","/api/v1/forensics/documents/types").permitAll()
                                .requestMatchers("/actuator/health", "/actuator/info").permitAll()
                                .requestMatchers("/api/v1/admin/**").hasRole("ADMIN")
                                .requestMatchers("/api/v1/analytics/**").hasRole("ADMIN")
                                .requestMatchers("/api/v1/forensics/documents/**").authenticated()
                                .requestMatchers("/api/v1/documents/**").authenticated()
                                .requestMatchers("/api/v1/account/**").authenticated()
                                .requestMatchers("/api/v1/transactions").authenticated()
                                .requestMatchers("/ws/telemetry/**").authenticated()
                                .anyRequest().authenticated())
                .addFilterBefore(this.customJwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);

        return httpSecurity.build();
    }

    @Bean
    public DaoAuthenticationProvider daoAuthenticationProvider() {
        DaoAuthenticationProvider daoAuthenticationProvider = new DaoAuthenticationProvider(this.userDetailsService);
        daoAuthenticationProvider.setPasswordEncoder(passwordEncoder());
        return daoAuthenticationProvider;
    }

    @Bean
    public AuthenticationManager authenticationManager(AuthenticationConfiguration authenticationConfiguration)
            throws Exception {
        return authenticationConfiguration.getAuthenticationManager();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder(12);
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration corsConfiguration = new CorsConfiguration();
        corsConfiguration.setAllowedOriginPatterns(List.of("https://*.example.com", "http://localhost:*"));
        corsConfiguration.setAllowedMethods(List.of("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"));
        corsConfiguration.setAllowedHeaders(List.of(
                HttpHeaders.AUTHORIZATION,
                HttpHeaders.CONTENT_TYPE,
                HttpHeaders.ACCEPT,
                "X-Requested-With",
                "X-Correlation-Id"));
        corsConfiguration.setExposedHeaders(List.of("X-Correlation-Id"));
        corsConfiguration.setAllowCredentials(false);
        corsConfiguration.setMaxAge(3600L);

        UrlBasedCorsConfigurationSource urlBasedCorsConfigurationSource = new UrlBasedCorsConfigurationSource();
        urlBasedCorsConfigurationSource.registerCorsConfiguration("/**", corsConfiguration);
        return urlBasedCorsConfigurationSource;
    }
}
