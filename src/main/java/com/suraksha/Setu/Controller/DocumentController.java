package com.suraksha.Setu.Controller;

import com.suraksha.Setu.dto.DocumentUploadDto;
import com.suraksha.Setu.Entity.DocumentForensicLog;
import com.suraksha.Setu.Entity.User;
import com.suraksha.Setu.Repo.DocumentRepository;
import com.suraksha.Setu.Repo.UserRepository;
import java.io.IOException;
import java.math.BigDecimal;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.HexFormat;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import com.suraksha.Setu.Service.AiService;
import com.suraksha.Setu.dto.AiResponseDto;

@RestController
@RequestMapping({"/api/v1/forensics/documents", "/api/v1/documents"})
public class DocumentController {

    private final DocumentRepository documentRepository;
    private final UserRepository userRepository;
    private final AiService aiService;
    public DocumentController(
        DocumentRepository documentRepository,
        UserRepository userRepository,
        AiService aiService) {

      this.documentRepository = documentRepository;
      this.userRepository = userRepository;
      this.aiService = aiService;
}

    @GetMapping(value = "/types", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<List<Map<String, Object>>> getDocumentTypes() {
        return ResponseEntity.ok(List.of(
                Map.of("code", "AADHAAR", "label", "Aadhaar Card", "allowedMimeTypes", List.of("application/pdf", "image/jpeg", "image/png")),
                Map.of("code", "PAN", "label", "PAN Card", "allowedMimeTypes", List.of("application/pdf", "image/jpeg", "image/png")),
                Map.of("code", "BANK_STATEMENT", "label", "Bank Statement", "allowedMimeTypes", List.of("application/pdf")),
                Map.of("code", "OTHER", "label", "Other Document", "allowedMimeTypes", List.of("application/pdf", "image/jpeg", "image/png"))));
    }

    @PostMapping(
            value = {"", "/upload"},
            consumes = MediaType.MULTIPART_FORM_DATA_VALUE,
            produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<DocumentForensicLog> uploadDocument(
            @ModelAttribute DocumentUploadDto documentUploadDto,
            Authentication authentication) throws IOException, NoSuchAlgorithmException {
        User user = this.userRepository.findByUsername(authentication.getName())
                .orElseThrow(() -> new IllegalArgumentException("Authenticated user record is missing"));

        byte[] bytes = documentUploadDto.getFile().getBytes();
        MessageDigest messageDigest = MessageDigest.getInstance("SHA-256");
        String sha256 = HexFormat.of().formatHex(messageDigest.digest(bytes));

        AiResponseDto aiResponse =
                aiService.analyzeDocument(documentUploadDto.getFile());

        BigDecimal defaultRiskScore =
                aiResponse.getRiskScore();

        String decision =
                aiResponse.getDecision();
        Map<String, Object> metadata = Map.of(
                "originalFilename", documentUploadDto.getFile().getOriginalFilename(),
                "declaredPurpose", documentUploadDto.getPurpose(),
                "byteSize", documentUploadDto.getFile().getSize(),
                "uploadedAt", OffsetDateTime.now().toString(),
                "summary", aiResponse.getSummary()
        );

        DocumentForensicLog documentForensicLog = new DocumentForensicLog();
        documentForensicLog.setUser(user);
        documentForensicLog.setDocumentName(documentUploadDto.getFile().getOriginalFilename());
        documentForensicLog.setContentType(documentUploadDto.getFile().getContentType());
        documentForensicLog.setSha256Hash(sha256);
        documentForensicLog.setRiskScore(defaultRiskScore);
        documentForensicLog.setRiskDecision(decision);
        documentForensicLog.setMetadataSnapshot(metadata);
        System.out.println("File: " + documentUploadDto.getFile().getOriginalFilename());
        System.out.println("Purpose: " + documentUploadDto.getPurpose());
        System.out.println("Content Type: " + documentUploadDto.getFile().getContentType());

        try {
          DocumentForensicLog savedLog = this.documentRepository.save(documentForensicLog);
          System.out.println("Saved ID: " + savedLog.getId());
          return ResponseEntity.ok(savedLog);
        } catch (Exception e) {
          e.printStackTrace();
          throw e;
        }
    }
}
