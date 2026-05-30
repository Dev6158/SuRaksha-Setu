package com.suraksha.Setu;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.Ordered;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.web.filter.OncePerRequestFilter;

@Configuration
public class RateLimiterConfig {

    @Bean
    public FilterRegistrationBean<TokenBucketRateLimiterFilter> tokenBucketRateLimiterFilterRegistration() {
        FilterRegistrationBean<TokenBucketRateLimiterFilter> filterRegistrationBean = new FilterRegistrationBean<>();
        filterRegistrationBean.setFilter(new TokenBucketRateLimiterFilter());
        filterRegistrationBean.setOrder(Ordered.HIGHEST_PRECEDENCE + 10);
        filterRegistrationBean.addUrlPatterns("/api/v1/*", "/ws/telemetry/*");
        return filterRegistrationBean;
    }

    public static class TokenBucketRateLimiterFilter extends OncePerRequestFilter {

        private final Map<String, InMemoryTokenBucket> securityBuckets;
        private final Map<String, InMemoryTokenBucket> telemetryBuckets;

        public TokenBucketRateLimiterFilter() {
            this.securityBuckets = new ConcurrentHashMap<>();
            this.telemetryBuckets = new ConcurrentHashMap<>();
        }

        @Override
        protected void doFilterInternal(
                HttpServletRequest httpServletRequest,
                HttpServletResponse httpServletResponse,
                FilterChain filterChain) throws ServletException, IOException {
            String requestUri = httpServletRequest.getRequestURI();
            String clientIp = resolveClientIp(httpServletRequest);
            InMemoryTokenBucket bucket = requestUri.startsWith("/ws/telemetry")
                    ? this.telemetryBuckets.computeIfAbsent(clientIp, key -> newBucket(100))
                    : this.securityBuckets.computeIfAbsent(clientIp, key -> newBucket(20));

            if (bucket.tryConsume()) {
                filterChain.doFilter(httpServletRequest, httpServletResponse);
                return;
            }

            httpServletResponse.setStatus(HttpStatus.TOO_MANY_REQUESTS.value());
            httpServletResponse.setContentType(MediaType.APPLICATION_JSON_VALUE);
            httpServletResponse.getWriter().write(
                    "{\"error\":\"rate_limit_exceeded\",\"message\":\"Request throughput exceeded token bucket policy\"}");
        }

        private InMemoryTokenBucket newBucket(long tokensPerMinute) {
            return new InMemoryTokenBucket(tokensPerMinute);
        }

        private String resolveClientIp(HttpServletRequest httpServletRequest) {
            String forwardedFor = httpServletRequest.getHeader("X-Forwarded-For");
            if (forwardedFor != null && !forwardedFor.isBlank()) {
                return forwardedFor.split(",")[0].trim();
            }

            String realIp = httpServletRequest.getHeader("X-Real-IP");
            if (realIp != null && !realIp.isBlank()) {
                return realIp.trim();
            }

            return httpServletRequest.getRemoteAddr();
        }
    }

    public static class InMemoryTokenBucket {

        private final long capacity;
        private final long refillTokensPerMinute;
        private long availableTokens;
        private long lastRefillTimestampMillis;

        public InMemoryTokenBucket(long refillTokensPerMinute) {
            this.capacity = refillTokensPerMinute;
            this.refillTokensPerMinute = refillTokensPerMinute;
            this.availableTokens = refillTokensPerMinute;
            this.lastRefillTimestampMillis = System.currentTimeMillis();
        }

        public synchronized boolean tryConsume() {
            refill();
            if (this.availableTokens <= 0L) {
                return false;
            }

            this.availableTokens = this.availableTokens - 1L;
            return true;
        }

        private void refill() {
            long currentTimestampMillis = System.currentTimeMillis();
            long elapsedMillis = currentTimestampMillis - this.lastRefillTimestampMillis;
            if (elapsedMillis <= 0L) {
                return;
            }

            long tokensToAdd = (elapsedMillis * this.refillTokensPerMinute) / 60_000L;
            if (tokensToAdd <= 0L) {
                return;
            }

            this.availableTokens = Math.min(this.capacity, this.availableTokens + tokensToAdd);
            this.lastRefillTimestampMillis = currentTimestampMillis;
        }
    }
}
