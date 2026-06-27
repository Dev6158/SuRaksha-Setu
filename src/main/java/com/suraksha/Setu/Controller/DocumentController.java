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
import java.util.UUID;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;
import com.suraksha.Setu.Service.AiService;
import com.suraksha.Setu.Service.DocumentStorageService;
import com.suraksha.Setu.dto.AiResponseDto;

@RestController
@RequestMapping({"/api/v1/forensics/documents", "/api/v1/documents"})
public class DocumentController {

    private final DocumentRepository documentRepository;
    private final UserRepository userRepository;
    private final AiService aiService;
    private final DocumentStorageService documentStorageService;
    public DocumentController(
    DocumentRepository documentRepository,
    UserRepository userRepository,
    AiService aiService,
    DocumentStorageService documentStorageService) {
    this.documentRepository = documentRepository;
    this.userRepository = userRepository;
    this.aiService = aiService;
    this.documentStorageService = documentStorageService;
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
        
        DocumentStorageService.StoredDocument storedDocument =
        documentStorageService.store(
                documentUploadDto.getFile(),
                user.getId()
        );
        byte[] bytes = documentUploadDto.getFile().getBytes();
        MessageDigest messageDigest = MessageDigest.getInstance("SHA-256");
        String sha256 = HexFormat.of().formatHex(messageDigest.digest(bytes));

        AiResponseDto aiResponse =
                aiService.analyzeDocument(documentUploadDto.getFile());
        if (aiResponse == null) {
            throw new RuntimeException("AI service returned null response");
        }
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
        documentForensicLog.setStoredFilePath(
                storedDocument.getPath());
        documentForensicLog.setFileSizeBytes(
                storedDocument.getSizeBytes());

        try {
          DocumentForensicLog savedLog = this.documentRepository.save(documentForensicLog);
          return ResponseEntity.ok(savedLog);
        } catch (Exception e) {
             e.printStackTrace();
             throw e;
        }
    }

    @PostMapping(value = "/{id}/analyze", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<DocumentForensicLog> analyzeStoredDocument(
            @PathVariable("id") UUID id,
            Authentication authentication) throws IOException {
        User user = this.userRepository.findByUsername(authentication.getName())
                .orElseThrow(() -> new IllegalArgumentException("Authenticated user record is missing"));

        DocumentForensicLog log = this.documentRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Document record not found"));

        if (!log.getUser().getId().equals(user.getId())) {
            throw new IllegalArgumentException("Unauthorized access to document");
        }

        byte[] fileBytes = this.documentStorageService.read(log.getStoredFilePath());

        MultipartFile multipartFile = new MultipartFile() {
            @Override public String getName() { return "file"; }
            @Override public String getOriginalFilename() { return log.getDocumentName(); }
            @Override public String getContentType() { return log.getContentType(); }
            @Override public boolean isEmpty() { return fileBytes == null || fileBytes.length == 0; }
            @Override public long getSize() { return fileBytes.length; }
            @Override public byte[] getBytes() throws IOException { return fileBytes; }
            @Override public java.io.InputStream getInputStream() throws IOException { return new java.io.ByteArrayInputStream(fileBytes); }
            @Override public void transferTo(java.io.File dest) throws IOException, IllegalStateException { java.nio.file.Files.write(dest.toPath(), fileBytes); }
        };

        AiResponseDto aiResponse = this.aiService.analyzeDocument(multipartFile);
        if (aiResponse != null) {
            log.setRiskScore(aiResponse.getRiskScore());
            log.setRiskDecision(aiResponse.getDecision());
            if (log.getMetadataSnapshot() != null) {
                log.getMetadataSnapshot().put("summary", aiResponse.getSummary());
            }
            log = this.documentRepository.save(log);
        }

        return ResponseEntity.ok(log);
    }
}
