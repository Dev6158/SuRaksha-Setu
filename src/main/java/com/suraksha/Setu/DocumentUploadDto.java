package com.suraksha.Setu;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import org.springframework.web.multipart.MultipartFile;

public class DocumentUploadDto {

    @NotNull
    private MultipartFile file;

    @Size(max = 500)
    private String purpose;

    public DocumentUploadDto() {
    }

    public MultipartFile getFile() {
        return this.file;
    }

    public void setFile(MultipartFile file) {
        this.file = file;
    }

    public String getPurpose() {
        return this.purpose;
    }

    public void setPurpose(String purpose) {
        this.purpose = purpose;
    }
}
