package com.suraksha.Setu.Controller;

import java.io.IOException;
import java.math.BigDecimal;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.OffsetDateTime;
import java.util.HexFormat;
import java.util.Map;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.suraksha.Setu.Entity.DocumentForensicLog;
import com.suraksha.Setu.Entity.User;
import com.suraksha.Setu.Repo.DocumentRepository;
import com.suraksha.Setu.Repo.UserRepository;
import com.suraksha.Setu.dto.DocumentUploadDto;

@RestController
@RequestMapping("/api/v1/forensics/documents")
public class DocumentController {

    private final DocumentRepository documentRepository;
    private final UserRepository userRepository;

    public DocumentController(DocumentRepository documentRepository, UserRepository userRepository) {
        this.documentRepository = documentRepository;
        this.userRepository = userRepository;
    }

    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE, produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<DocumentForensicLog> uploadDocument(
            @ModelAttribute DocumentUploadDto documentUploadDto,
            Authentication authentication) throws IOException, NoSuchAlgorithmException {
        User user = this.userRepository.findByUsername(authentication.getName())
                .orElseThrow(() -> new IllegalArgumentException("Authenticated user record is missing"));

        byte[] bytes = documentUploadDto.getFile().getBytes();
        MessageDigest messageDigest = MessageDigest.getInstance("SHA-256");
        String sha256 = HexFormat.of().formatHex(messageDigest.digest(bytes));

        BigDecimal defaultRiskScore = BigDecimal.ZERO;
        String decision = "PENDING_REVIEW";
        Map<String, Object> metadata = Map.of(
                "originalFilename", documentUploadDto.getFile().getOriginalFilename(),
                "declaredPurpose", documentUploadDto.getPurpose(),
                "byteSize", documentUploadDto.getFile().getSize(),
                "uploadedAt", OffsetDateTime.now().toString());

        DocumentForensicLog documentForensicLog = new DocumentForensicLog();
        documentForensicLog.setUser(user);
        documentForensicLog.setDocumentName(documentUploadDto.getFile().getOriginalFilename());
        documentForensicLog.setContentType(documentUploadDto.getFile().getContentType());
        documentForensicLog.setSha256Hash(sha256);
        documentForensicLog.setRiskScore(defaultRiskScore);
        documentForensicLog.setRiskDecision(decision);
        documentForensicLog.setMetadataSnapshot(metadata);

        DocumentForensicLog savedLog = this.documentRepository.save(documentForensicLog);
        return ResponseEntity.ok(savedLog);
    }
}
