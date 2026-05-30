package com.suraksha.Setu.Websocket;

import java.io.IOException;
import java.time.Duration;
import java.time.Instant;
import java.util.Objects;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

@Component
public class TelemetryWebSocketHandler extends TextWebSocketHandler {

    private final ConcurrentHashMap<String, WebSocketSession> activeSessions;
    private final ConcurrentHashMap<String, String> sessionUsers;
    private final RedisTemplate<String, String> redisTemplate;
    private final WebClient webClient;
    private final String riskEvaluationPath;

    public TelemetryWebSocketHandler(
            RedisTemplate<String, String> redisTemplate,
            WebClient.Builder webClientBuilder,
            @Value("${ml.fastapi.base-url:http://localhost:8000}") String fastApiBaseUrl,
            @Value("${ml.fastapi.risk-path:/risk/evaluate}") String riskEvaluationPath) {
        this.activeSessions = new ConcurrentHashMap<>();
        this.sessionUsers = new ConcurrentHashMap<>();
        this.redisTemplate = redisTemplate;
        this.webClient = webClientBuilder.baseUrl(fastApiBaseUrl).build();
        this.riskEvaluationPath = riskEvaluationPath;
    }

    @Override
    public void afterConnectionEstablished(WebSocketSession webSocketSession) throws Exception {
        String accountId = resolveAccountId(webSocketSession);
        this.activeSessions.put(webSocketSession.getId(), webSocketSession);
        this.sessionUsers.put(webSocketSession.getId(), accountId);
    }

    @Override
    protected void handleTextMessage(WebSocketSession webSocketSession, TextMessage textMessage) throws Exception {
        String accountId = this.sessionUsers.getOrDefault(webSocketSession.getId(), "anonymous");
        String trackingMatrix = extractJsonField(textMessage.getPayload(), "trackingMatrix");

        if (trackingMatrix == null || trackingMatrix.isBlank() || "null".equals(trackingMatrix)) {
            sendJson(webSocketSession, "{\"error\":\"invalid_payload\",\"message\":\"trackingMatrix is required\"}");
            return;
        }

        String redisKey = "telemetry:matrix:" + accountId + ":" + Instant.now().toEpochMilli();
        this.redisTemplate.opsForValue().set(redisKey, trackingMatrix, Duration.ofMinutes(10));

        String evaluationPayload = "{"
                + "\"accountId\":\"" + escapeJson(accountId) + "\","
                + "\"sessionId\":\"" + escapeJson(webSocketSession.getId()) + "\","
                + "\"trackingMatrix\":" + trackingMatrix + ","
                + "\"receivedAt\":\"" + Instant.now() + "\""
                + "}";

        CompletableFuture.runAsync(() -> evaluateRiskAndReturnFrame(webSocketSession, evaluationPayload));
    }

    @Override
    public void afterConnectionClosed(WebSocketSession webSocketSession, CloseStatus closeStatus) throws Exception {
        this.activeSessions.remove(webSocketSession.getId());
        this.sessionUsers.remove(webSocketSession.getId());
    }

    @Override
    public void handleTransportError(WebSocketSession webSocketSession, Throwable exception) throws Exception {
        this.activeSessions.remove(webSocketSession.getId());
        this.sessionUsers.remove(webSocketSession.getId());
        if (webSocketSession.isOpen()) {
            webSocketSession.close(CloseStatus.SERVER_ERROR);
        }
    }

    private void evaluateRiskAndReturnFrame(WebSocketSession webSocketSession, String evaluationPayload) {
        try {
            String riskFrame = this.webClient
                    .post()
                    .uri(this.riskEvaluationPath)
                    .contentType(MediaType.APPLICATION_JSON)
                    .accept(MediaType.APPLICATION_JSON)
                    .bodyValue(evaluationPayload)
                    .retrieve()
                    .bodyToMono(String.class)
                    .block(Duration.ofSeconds(3));

            if (riskFrame != null && webSocketSession.isOpen()) {
                try {
                    sendJson(webSocketSession, riskFrame);
                } catch (IOException ioException) {
                    throw new IllegalStateException("Unable to send websocket risk frame", ioException);
                }
            }
        } catch (RuntimeException runtimeException) {
            try {
                if (webSocketSession.isOpen()) {
                    sendJson(webSocketSession,
                            "{\"error\":\"risk_engine_unavailable\",\"message\":\"Risk evaluation timed out\"}");
                }
            } catch (IOException ignored) {
                throw new IllegalStateException("Unable to send websocket risk error frame", ignored);
            }
        }
    }

    private String extractJsonField(String jsonPayload, String fieldName) {
        String fieldToken = "\"" + fieldName + "\"";
        int fieldIndex = jsonPayload.indexOf(fieldToken);
        if (fieldIndex < 0) {
            return null;
        }

        int colonIndex = jsonPayload.indexOf(':', fieldIndex + fieldToken.length());
        if (colonIndex < 0) {
            return null;
        }

        int valueStart = colonIndex + 1;
        while (valueStart < jsonPayload.length() && Character.isWhitespace(jsonPayload.charAt(valueStart))) {
            valueStart++;
        }

        if (valueStart >= jsonPayload.length()) {
            return null;
        }

        char openingCharacter = jsonPayload.charAt(valueStart);
        if (openingCharacter == '{') {
            return readBalancedJsonValue(jsonPayload, valueStart, '{', '}');
        }
        if (openingCharacter == '[') {
            return readBalancedJsonValue(jsonPayload, valueStart, '[', ']');
        }
        if (openingCharacter == '"') {
            return readJsonStringValue(jsonPayload, valueStart);
        }

        int valueEnd = valueStart;
        while (valueEnd < jsonPayload.length()
                && jsonPayload.charAt(valueEnd) != ','
                && jsonPayload.charAt(valueEnd) != '}') {
            valueEnd++;
        }
        return jsonPayload.substring(valueStart, valueEnd).trim();
    }

    private String readBalancedJsonValue(String jsonPayload, int valueStart, char openingCharacter, char closingCharacter) {
        int depth = 0;
        boolean insideString = false;
        boolean escaping = false;

        for (int index = valueStart; index < jsonPayload.length(); index++) {
            char character = jsonPayload.charAt(index);
            if (escaping) {
                escaping = false;
                continue;
            }
            if (character == '\\') {
                escaping = true;
                continue;
            }
            if (character == '"') {
                insideString = !insideString;
                continue;
            }
            if (!insideString && character == openingCharacter) {
                depth++;
            }
            if (!insideString && character == closingCharacter) {
                depth--;
                if (depth == 0) {
                    return jsonPayload.substring(valueStart, index + 1);
                }
            }
        }

        return null;
    }

    private String readJsonStringValue(String jsonPayload, int valueStart) {
        boolean escaping = false;
        for (int index = valueStart + 1; index < jsonPayload.length(); index++) {
            char character = jsonPayload.charAt(index);
            if (escaping) {
                escaping = false;
            } else if (character == '\\') {
                escaping = true;
            } else if (character == '"') {
                return jsonPayload.substring(valueStart, index + 1);
            }
        }
        return null;
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

    private String resolveAccountId(WebSocketSession webSocketSession) {
        Object principal = webSocketSession.getPrincipal();
        if (principal != null && principal.toString() != null) {
            return principal.toString();
        }

        String userId = webSocketSession.getUri() == null ? null : webSocketSession.getUri().getQuery();
        if (userId != null && userId.startsWith("accountId=")) {
            return userId.substring("accountId=".length());
        }

        return "anonymous";
    }

    private void sendJson(WebSocketSession webSocketSession, String jsonPayload) throws IOException {
        Objects.requireNonNull(jsonPayload, "jsonPayload must not be null");
        synchronized (webSocketSession) {
            if (webSocketSession.isOpen()) {
                webSocketSession.sendMessage(new TextMessage(jsonPayload));
            }
        }
    }
}
