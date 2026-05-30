package com.suraksha.Setu.Security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.Collection;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
public class CustomJwtAuthenticationFilter extends OncePerRequestFilter {

    private static final String BEARER_PREFIX = "Bearer ";

    private final JwtTokenService jwtTokenService;
    private final UserDetailsService userDetailsService;

    public CustomJwtAuthenticationFilter(JwtTokenService jwtTokenService, UserDetailsService userDetailsService) {
        this.jwtTokenService = jwtTokenService;
        this.userDetailsService = userDetailsService;
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest httpServletRequest,
            HttpServletResponse httpServletResponse,
            FilterChain filterChain) throws ServletException, IOException {
        String authorizationHeader = httpServletRequest.getHeader(HttpHeaders.AUTHORIZATION);

        if (StringUtils.hasText(authorizationHeader) && authorizationHeader.startsWith(BEARER_PREFIX)) {
            String token = authorizationHeader.substring(BEARER_PREFIX.length());

            try {
                JwtClaims claims = this.jwtTokenService.decodeAndValidateClaims(token);
                String username = claims.getSubject();

                if (StringUtils.hasText(username) && SecurityContextHolder.getContext().getAuthentication() == null) {
                    UserDetails userDetails = this.userDetailsService.loadUserByUsername(username);
                    Collection<? extends GrantedAuthority> authorities =
                            this.jwtTokenService.extractAuthorities(claims);

                    UsernamePasswordAuthenticationToken authenticationToken =
                            new UsernamePasswordAuthenticationToken(userDetails, null, authorities);
                    authenticationToken.setDetails(
                            new WebAuthenticationDetailsSource().buildDetails(httpServletRequest));

                    SecurityContextHolder.getContext().setAuthentication(authenticationToken);
                }
            } catch (JwtValidationException | IllegalArgumentException exception) {
                SecurityContextHolder.clearContext();
                httpServletResponse.setStatus(HttpStatus.UNAUTHORIZED.value());
                httpServletResponse.setContentType(MediaType.APPLICATION_JSON_VALUE);
                httpServletResponse.getWriter().write(
                        "{\"error\":\"invalid_token\",\"message\":\"JWT validation failed or token expired\"}");
                return;
            }
        }

        filterChain.doFilter(httpServletRequest, httpServletResponse);
    }
}
