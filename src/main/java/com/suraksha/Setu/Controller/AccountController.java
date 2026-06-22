package com.suraksha.Setu.Controller;

import com.suraksha.Setu.Entity.DocumentForensicLog;
import com.suraksha.Setu.Entity.User;
import com.suraksha.Setu.Repo.DocumentRepository;
import com.suraksha.Setu.Repo.UserRepository;
import java.math.BigDecimal;
import java.time.YearMonth;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class AccountController {

    private final UserRepository userRepository;
    private final DocumentRepository documentRepository;

    public AccountController(UserRepository userRepository, DocumentRepository documentRepository) {
        this.userRepository = userRepository;
        this.documentRepository = documentRepository;
    }

    @GetMapping("/api/v1/account/summary")
    public ResponseEntity<Map<String, Object>> getAccountSummary(Authentication authentication) {
        User user = loadCurrentUser(authentication);
        List<DocumentForensicLog> logs = this.documentRepository.findByUserIdOrderByCreatedAtDesc(user.getId());
        long highRiskCount = logs.stream()
                .filter(log -> log.getRiskScore() != null && log.getRiskScore().compareTo(new BigDecimal("0.7000")) >= 0)
                .count();

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("userId", user.getId());
        response.put("username", user.getUsername());
        response.put("email", user.getEmail());
        response.put("roles", user.getRoleList());
        response.put("documentsUploaded", logs.size());
        response.put("highRiskEvents", highRiskCount);
        response.put("accountStatus", user.isEnabled() ? "ACTIVE" : "DISABLED");
        return ResponseEntity.ok(response);
    }

    @GetMapping("/api/v1/transactions")
    public ResponseEntity<List<Map<String, Object>>> getTransactions(Authentication authentication) {
        User user = loadCurrentUser(authentication);
        List<Map<String, Object>> response = this.documentRepository.findByUserIdOrderByCreatedAtDesc(user.getId())
                .stream()
                .map(this::transactionPayload)
                .toList();
        return ResponseEntity.ok(response);
    }

    @GetMapping("/api/v1/account/monthly-stats")
    public ResponseEntity<List<Map<String, Object>>> getMonthlyStats(Authentication authentication) {
        User user = loadCurrentUser(authentication);
        Map<YearMonth, MonthlyStats> monthlyStats = new LinkedHashMap<>();

        for (DocumentForensicLog log : this.documentRepository.findByUserIdOrderByCreatedAtDesc(user.getId())) {
            if (log.getCreatedAt() == null) {
                continue;
            }
            YearMonth yearMonth = YearMonth.from(log.getCreatedAt());
            MonthlyStats stats = monthlyStats.computeIfAbsent(yearMonth, key -> new MonthlyStats());
            stats.incrementTotal();
            if (log.getRiskScore() != null && log.getRiskScore().compareTo(new BigDecimal("0.7000")) >= 0) {
                stats.incrementHighRisk();
            }
        }

        List<Map<String, Object>> response = monthlyStats.entrySet()
                .stream()
                .map(entry -> Map.<String, Object>of(
                        "month", entry.getKey().toString(),
                        "documentsUploaded", entry.getValue().getTotal(),
                        "highRiskEvents", entry.getValue().getHighRisk()))
                .toList();

        return ResponseEntity.ok(response);
    }

    private User loadCurrentUser(Authentication authentication) {
        if (authentication == null || authentication.getName() == null) {
            throw new IllegalArgumentException("Authenticated user is required");
        }

        return this.userRepository.findByUsername(authentication.getName())
                .orElseThrow(() -> new IllegalArgumentException("Authenticated user record is missing"));
    }

    private Map<String, Object> transactionPayload(DocumentForensicLog log) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("id", log.getId());
        payload.put("type", "DOCUMENT_UPLOAD");
        payload.put("documentName", log.getDocumentName());
        payload.put("contentType", log.getContentType());
        payload.put("sha256Hash", log.getSha256Hash());
        payload.put("riskScore", log.getRiskScore());
        payload.put("riskDecision", log.getRiskDecision());
        payload.put("createdAt", log.getCreatedAt());
        return payload;
    }

    private static class MonthlyStats {

        private int total;
        private int highRisk;

        public void incrementTotal() {
            this.total = this.total + 1;
        }

        public void incrementHighRisk() {
            this.highRisk = this.highRisk + 1;
        }

        public int getTotal() {
            return this.total;
        }

        public int getHighRisk() {
            return this.highRisk;
        }
    }
}
