package com.suraksha.Setu.Controller;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.suraksha.Setu.Entity.DocumentForensicLog;
import com.suraksha.Setu.Repo.FraudRiskRepository;

@RestController
@RequestMapping("/api/v1/analytics/risk-events")
public class AnalyticsController {

    private final FraudRiskRepository fraudRiskRepository;

    public AnalyticsController(FraudRiskRepository fraudRiskRepository) {
        this.fraudRiskRepository = fraudRiskRepository;
    }

    @GetMapping
    public ResponseEntity<List<DocumentForensicLog>> findRiskEvents(
            @RequestParam("windowStart") @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
                    OffsetDateTime windowStart,
            @RequestParam("windowEnd") @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
                    OffsetDateTime windowEnd) {
        return ResponseEntity.ok(this.fraudRiskRepository.findRiskEventsWithinWindow(windowStart, windowEnd));
    }

    @GetMapping("/high-risk")
    public ResponseEntity<List<DocumentForensicLog>> findHighRiskEvents(
            @RequestParam("windowStart") @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
                    OffsetDateTime windowStart,
            @RequestParam("windowEnd") @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
                    OffsetDateTime windowEnd,
            @RequestParam("minimumRiskScore") BigDecimal minimumRiskScore) {
        return ResponseEntity.ok(this.fraudRiskRepository.findHighRiskEventsWithinWindow(
                windowStart,
                windowEnd,
                minimumRiskScore));
    }

    @GetMapping("/trends/hourly")
    public ResponseEntity<List<Object[]>> sliceHourlySecurityTrends(
            @RequestParam("windowStart") @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
                    OffsetDateTime windowStart,
            @RequestParam("windowEnd") @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
                    OffsetDateTime windowEnd) {
        return ResponseEntity.ok(this.fraudRiskRepository.sliceSecurityTrendsByHour(windowStart, windowEnd));
    }
}
