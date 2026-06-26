package com.suraksha.Setu.Service;

import java.math.BigDecimal;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.MediaType;
import org.springframework.http.client.MultipartBodyBuilder;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

@Service
public class DocumentAnalysisService {

    private final WebClient webClient;
    private final String scorePath;

    public DocumentAnalysisService(
            WebClient.Builder webClientBuilder,
            @Value("${ml.fastapi.base-url:http://localhost:8000}") String mlBaseUrl,
            @Value("${ml.fastapi.risk-path:/score}") String scorePath) {
        this.webClient = webClientBuilder.baseUrl(mlBaseUrl).build();
        this.scorePath = scorePath;
    }

    public AnalysisResult analyzeDocument(byte[] fileBytes, String filename, String contentType) {
        MultipartBodyBuilder multipartBodyBuilder = new MultipartBodyBuilder();
        multipartBodyBuilder
                .part("file", new NamedByteArrayResource(fileBytes, filename))
                .filename(filename)
                .contentType(resolveContentType(contentType));

        Map<String, Object> response = this.webClient
                .post()
                .uri(this.scorePath)
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .bodyValue(multipartBodyBuilder.build())
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {
                })
                .block();

        if (response == null) {
            throw new IllegalStateException("AI service returned an empty analysis response");
        }

        BigDecimal riskScore = extractRiskScore(response);
        String riskDecision = extractRiskDecision(response, riskScore);
        return new AnalysisResult(riskScore, riskDecision, response);
    }

    private MediaType resolveContentType(String contentType) {
        if (contentType == null || contentType.isBlank()) {
            return MediaType.APPLICATION_OCTET_STREAM;
        }
        return MediaType.parseMediaType(contentType);
    }

    private BigDecimal extractRiskScore(Map<String, Object> response) {
        Object value = firstPresent(response, "riskScore", "risk_score", "score", "fraudScore", "fraud_score");
        if (value instanceof Number number) {
            return BigDecimal.valueOf(number.doubleValue()).setScale(4, java.math.RoundingMode.HALF_UP);
        }
        if (value instanceof String stringValue && !stringValue.isBlank()) {
            return new BigDecimal(stringValue).setScale(4, java.math.RoundingMode.HALF_UP);
        }
        return BigDecimal.ZERO.setScale(4, java.math.RoundingMode.HALF_UP);
    }

    private String extractRiskDecision(Map<String, Object> response, BigDecimal riskScore) {
        Object value = firstPresent(response, "riskDecision", "risk_decision", "decision", "label", "riskLabel");
        if (value != null && !value.toString().isBlank()) {
            return value.toString().toUpperCase();
        }
        if (riskScore.compareTo(new BigDecimal("0.7000")) >= 0) {
            return "HIGH";
        }
        if (riskScore.compareTo(new BigDecimal("0.4000")) >= 0) {
            return "MEDIUM";
        }
        return "LOW";
    }

    private Object firstPresent(Map<String, Object> response, String... keys) {
        for (String key : keys) {
            if (response.containsKey(key)) {
                return response.get(key);
            }
        }
        return null;
    }

    private static class NamedByteArrayResource extends ByteArrayResource {

        private final String filename;

        public NamedByteArrayResource(byte[] byteArray, String filename) {
            super(byteArray);
            this.filename = filename;
        }

        @Override
        public String getFilename() {
            return this.filename;
        }
    }

    public static class AnalysisResult {

        private final BigDecimal riskScore;
        private final String riskDecision;
        private final Map<String, Object> rawResponse;

        public AnalysisResult(BigDecimal riskScore, String riskDecision, Map<String, Object> rawResponse) {
            this.riskScore = riskScore;
            this.riskDecision = riskDecision;
            this.rawResponse = rawResponse;
        }

        public BigDecimal getRiskScore() {
            return this.riskScore;
        }

        public String getRiskDecision() {
            return this.riskDecision;
        }

        public Map<String, Object> getRawResponse() {
            return this.rawResponse;
        }
    }
}
