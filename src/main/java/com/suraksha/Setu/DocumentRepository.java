package com.suraksha.Setu;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface DocumentRepository extends JpaRepository<DocumentForensicLog, UUID> {

    List<DocumentForensicLog> findByUserIdOrderByCreatedAtDesc(UUID userId);

    List<DocumentForensicLog> findByCreatedAtBetweenOrderByCreatedAtDesc(
            OffsetDateTime windowStart,
            OffsetDateTime windowEnd);
}
