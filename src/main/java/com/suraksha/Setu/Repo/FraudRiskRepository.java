package com.suraksha.Setu.Repo;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import com.suraksha.Setu.Entity.DocumentForensicLog;

@Repository
public interface FraudRiskRepository extends JpaRepository<DocumentForensicLog, UUID> {

    @Query(
            value = """
                    SELECT *
                    FROM document_forensic_logs dfl
                    WHERE dfl.created_at >= :windowStart
                      AND dfl.created_at < :windowEnd
                    ORDER BY dfl.created_at DESC
                    """,
            nativeQuery = true)
    List<DocumentForensicLog> findRiskEventsWithinWindow(
            @Param("windowStart") OffsetDateTime windowStart,
            @Param("windowEnd") OffsetDateTime windowEnd);

    @Query(
            value = """
                    SELECT *
                    FROM document_forensic_logs dfl
                    WHERE dfl.created_at >= :windowStart
                      AND dfl.created_at < :windowEnd
                      AND dfl.risk_score >= :minimumRiskScore
                    ORDER BY dfl.risk_score DESC, dfl.created_at DESC
                    """,
            nativeQuery = true)
    List<DocumentForensicLog> findHighRiskEventsWithinWindow(
            @Param("windowStart") OffsetDateTime windowStart,
            @Param("windowEnd") OffsetDateTime windowEnd,
            @Param("minimumRiskScore") java.math.BigDecimal minimumRiskScore);

    @Query(
            value = """
                    SELECT date_trunc('hour', dfl.created_at) AS bucket_start,
                           dfl.risk_decision AS risk_decision,
                           COUNT(*) AS event_count,
                           AVG(dfl.risk_score) AS average_risk_score
                    FROM document_forensic_logs dfl
                    WHERE dfl.created_at >= :windowStart
                      AND dfl.created_at < :windowEnd
                    GROUP BY bucket_start, dfl.risk_decision
                    ORDER BY bucket_start ASC
                    """,
            nativeQuery = true)
    List<Object[]> sliceSecurityTrendsByHour(
            @Param("windowStart") OffsetDateTime windowStart,
            @Param("windowEnd") OffsetDateTime windowEnd);
}
