package com.suraksha.Setu.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.UUID;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.multipart.MultipartFile;

@Service
public class DocumentStorageService {

    private final Path storageRoot;

    public DocumentStorageService(@Value("${document.storage.root:/tmp/uploads}") String storageRoot) throws IOException {
        this.storageRoot = Paths.get(storageRoot).toAbsolutePath().normalize();
        Files.createDirectories(this.storageRoot);
    }

    public StoredDocument store(MultipartFile multipartFile, UUID userId) throws IOException {
        if (multipartFile == null || multipartFile.isEmpty()) {
            throw new IllegalArgumentException("Uploaded file is required");
        }

        String originalFilename = StringUtils.cleanPath(
                multipartFile.getOriginalFilename() == null ? "document.bin" : multipartFile.getOriginalFilename());
        String extension = extractExtension(originalFilename);
        String storedFilename = UUID.randomUUID() + extension;
        Path userDirectory = this.storageRoot.resolve(userId.toString()).normalize();
        Files.createDirectories(userDirectory);

        Path destination = userDirectory.resolve(storedFilename).normalize();
        if (!destination.startsWith(this.storageRoot)) {
            throw new IllegalArgumentException("Invalid document storage path");
        }

        Files.copy(multipartFile.getInputStream(), destination, StandardCopyOption.REPLACE_EXISTING);
        return new StoredDocument(destination.toString(), multipartFile.getSize());
    }

    public byte[] read(String storedFilePath) throws IOException {
        Path path = Paths.get(storedFilePath).toAbsolutePath().normalize();
        if (!path.startsWith(this.storageRoot)) {
            throw new IllegalArgumentException("Stored file path is outside document storage root");
        }
        if (!Files.exists(path)) {
            throw new IllegalArgumentException("Stored document file is missing. Please re-upload to analyse.");
        }
        return Files.readAllBytes(path);
    }

    private String extractExtension(String filename) {
        int dotIndex = filename.lastIndexOf('.');
        if (dotIndex < 0 || dotIndex == filename.length() - 1) {
            return ".bin";
        }
        return filename.substring(dotIndex);
    }

    public static class StoredDocument {

        private final String path;
        private final long sizeBytes;

        public StoredDocument(String path, long sizeBytes) {
            this.path = path;
            this.sizeBytes = sizeBytes;
        }

        public String getPath() {
            return this.path;
        }

        public long getSizeBytes() {
            return this.sizeBytes;
        }
    }
}
