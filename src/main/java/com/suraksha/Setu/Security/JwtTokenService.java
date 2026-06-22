package com.suraksha.Setu.Security;

import java.nio.charset.StandardCharsets;
import java.security.InvalidKeyException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Base64;
import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

@Service
public class JwtTokenService {

    private static final String HMAC_SHA_256 = "HmacSHA256";
    private static final Base64.Encoder BASE64_URL_ENCODER = Base64.getUrlEncoder().withoutPadding();
    private static final Base64.Decoder BASE64_URL_DECODER = Base64.getUrlDecoder();

    private final byte[] secretKey;
    private final long tokenTtlSeconds;

    public JwtTokenService(
            @Value("${security.jwt.secret}") String jwtSecret,
            @Value("${security.jwt.ttl-seconds:3600}") long tokenTtlSeconds) {
        this.secretKey = jwtSecret.getBytes(StandardCharsets.UTF_8);
        this.tokenTtlSeconds = tokenTtlSeconds;
    }

    public String generateToken(Authentication authentication) {
        Instant issuedAt = Instant.now();
        Instant expiresAt = issuedAt.plusSeconds(this.tokenTtlSeconds);
        List<String> roles = authentication.getAuthorities()
                .stream()
                .map(GrantedAuthority::getAuthority)
                .toList();

        String headerJson = "{\"typ\":\"JWT\",\"alg\":\"HS256\"}";
        String payloadJson = buildPayloadJson(
                authentication.getName(),
                roles,
                issuedAt.getEpochSecond(),
                expiresAt.getEpochSecond());
        String encodedHeader = base64UrlEncode(headerJson.getBytes(StandardCharsets.UTF_8));
        String encodedPayload = base64UrlEncode(payloadJson.getBytes(StandardCharsets.UTF_8));
        String signingInput = encodedHeader + "." + encodedPayload;
        String encodedSignature = base64UrlEncode(sign(signingInput));
        return signingInput + "." + encodedSignature;
    }

    public JwtClaims decodeAndValidateClaims(String token) {
        String[] tokenSegments = token.split("\\.");
        if (tokenSegments.length != 3) {
            throw new JwtValidationException("JWT must contain header, payload, and signature segments");
        }

        String signingInput = tokenSegments[0] + "." + tokenSegments[1];
        byte[] expectedSignature = sign(signingInput);
        byte[] actualSignature = base64UrlDecode(tokenSegments[2]);

        if (!MessageDigest.isEqual(expectedSignature, actualSignature)) {
            throw new JwtValidationException("JWT signature validation failed");
        }

        String headerJson = new String(base64UrlDecode(tokenSegments[0]), StandardCharsets.UTF_8);
        String algorithm = extractStringClaim(headerJson, "alg");
        if (!"HS256".equals(algorithm)) {
            throw new JwtValidationException("JWT algorithm must be HS256");
        }

        String payloadJson = new String(base64UrlDecode(tokenSegments[1]), StandardCharsets.UTF_8);
        String subject = extractStringClaim(payloadJson, "sub");
        Long expiresAtEpochSeconds = extractLongClaim(payloadJson, "exp");
        List<String> roles = extractStringArrayClaim(payloadJson, "roles");

        if (!StringUtils.hasText(subject)) {
            throw new JwtValidationException("JWT subject is missing");
        }

        if (expiresAtEpochSeconds == null || expiresAtEpochSeconds <= Instant.now().getEpochSecond()) {
            throw new JwtValidationException("JWT expiration footprint is invalid");
        }

        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("sub", subject);
        payload.put("exp", expiresAtEpochSeconds);
        payload.put("roles", roles);
        return new JwtClaims(subject, payload);
    }

    public Collection<? extends GrantedAuthority> extractAuthorities(JwtClaims claims) {
        Object rolesClaim = claims.getClaim("roles");
        List<GrantedAuthority> authorities = new ArrayList<>();

        if (rolesClaim instanceof Collection<?> roles) {
            for (Object role : roles) {
                if (role != null && StringUtils.hasText(role.toString())) {
                    authorities.add(new SimpleGrantedAuthority(role.toString()));
                }
            }
        }

        return authorities;
    }

    private byte[] sign(String signingInput) {
        try {
            Mac mac = Mac.getInstance(HMAC_SHA_256);
            mac.init(new SecretKeySpec(this.secretKey, HMAC_SHA_256));
            return mac.doFinal(signingInput.getBytes(StandardCharsets.UTF_8));
        } catch (NoSuchAlgorithmException | InvalidKeyException exception) {
            throw new JwtValidationException("Unable to calculate JWT signature", exception);
        }
    }

    private String base64UrlEncode(byte[] bytes) {
        return BASE64_URL_ENCODER.encodeToString(bytes);
    }

    private byte[] base64UrlDecode(String value) {
        try {
            return BASE64_URL_DECODER.decode(value);
        } catch (IllegalArgumentException exception) {
            throw new JwtValidationException("JWT contains invalid Base64URL data", exception);
        }
    }

    private String buildPayloadJson(String subject, List<String> roles, long issuedAt, long expiresAt) {
        StringBuilder stringBuilder = new StringBuilder();
        stringBuilder.append("{");
        stringBuilder.append("\"sub\":\"").append(escapeJson(subject)).append("\",");
        stringBuilder.append("\"roles\":[");
        for (int index = 0; index < roles.size(); index++) {
            if (index > 0) {
                stringBuilder.append(",");
            }
            stringBuilder.append("\"").append(escapeJson(roles.get(index))).append("\"");
        }
        stringBuilder.append("],");
        stringBuilder.append("\"iat\":").append(issuedAt).append(",");
        stringBuilder.append("\"exp\":").append(expiresAt);
        stringBuilder.append("}");
        return stringBuilder.toString();
    }

    private String extractStringClaim(String json, String claimName) {
        int start = findClaimValueStart(json, claimName, '"');
        if (start < 0) {
            return null;
        }

        StringBuilder value = new StringBuilder();
        boolean escaping = false;
        for (int index = start; index < json.length(); index++) {
            char character = json.charAt(index);
            if (escaping) {
                value.append(unescapeJsonCharacter(character));
                escaping = false;
            } else if (character == '\\') {
                escaping = true;
            } else if (character == '"') {
                return value.toString();
            } else {
                value.append(character);
            }
        }

        throw new JwtValidationException("JWT string claim is malformed: " + claimName);
    }

    private Long extractLongClaim(String json, String claimName) {
        int start = findClaimValueStart(json, claimName, null);
        if (start < 0) {
            return null;
        }

        int end = start;
        while (end < json.length() && Character.isDigit(json.charAt(end))) {
            end++;
        }
        if (end == start) {
            return null;
        }

        return Long.parseLong(json.substring(start, end));
    }

    private List<String> extractStringArrayClaim(String json, String claimName) {
        int start = findClaimValueStart(json, claimName, '[');
        if (start < 0) {
            return List.of();
        }

        List<String> values = new ArrayList<>();
        int index = start;
        while (index < json.length()) {
            char character = json.charAt(index);
            if (character == ']') {
                return values;
            }
            if (character == '"') {
                StringBuilder value = new StringBuilder();
                boolean escaping = false;
                index++;
                while (index < json.length()) {
                    char valueCharacter = json.charAt(index);
                    if (escaping) {
                        value.append(unescapeJsonCharacter(valueCharacter));
                        escaping = false;
                    } else if (valueCharacter == '\\') {
                        escaping = true;
                    } else if (valueCharacter == '"') {
                        values.add(value.toString());
                        break;
                    } else {
                        value.append(valueCharacter);
                    }
                    index++;
                }
            }
            index++;
        }

        throw new JwtValidationException("JWT array claim is malformed: " + claimName);
    }

    private int findClaimValueStart(String json, String claimName, Character expectedOpeningCharacter) {
        String claimToken = "\"" + claimName + "\"";
        int claimIndex = json.indexOf(claimToken);
        if (claimIndex < 0) {
            return -1;
        }

        int colonIndex = json.indexOf(':', claimIndex + claimToken.length());
        if (colonIndex < 0) {
            return -1;
        }

        int valueStart = colonIndex + 1;
        while (valueStart < json.length() && Character.isWhitespace(json.charAt(valueStart))) {
            valueStart++;
        }

        if (expectedOpeningCharacter != null) {
            if (valueStart >= json.length() || json.charAt(valueStart) != expectedOpeningCharacter.charValue()) {
                return -1;
            }
            return valueStart + 1;
        }

        return valueStart;
    }

    private String escapeJson(String value) {
        return value
                .replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\b", "\\b")
                .replace("\f", "\\f")
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t");
    }

    private char unescapeJsonCharacter(char character) {
        return switch (character) {
            case '"' -> '"';
            case '\\' -> '\\';
            case '/' -> '/';
            case 'b' -> '\b';
            case 'f' -> '\f';
            case 'n' -> '\n';
            case 'r' -> '\r';
            case 't' -> '\t';
            default -> character;
        };
    }
}
