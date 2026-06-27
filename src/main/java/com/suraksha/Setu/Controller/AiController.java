package com.suraksha.Setu.Controller;

import com.suraksha.Setu.Service.AiService;
import com.suraksha.Setu.dto.AiResponseDto;

import java.io.IOException;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping({"/api/v1/ai", ""})
public class AiController {

    private final AiService aiService;

    @Autowired
    public AiController(AiService aiService) {
        this.aiService = aiService;
    }

    @PostMapping(
            value = {"/analyze", "/analyze-document"},
            consumes = MediaType.MULTIPART_FORM_DATA_VALUE
    )
    public AiResponseDto analyzeDocument(
        @RequestParam("file") MultipartFile file) throws IOException {
        return aiService.analyzeDocument(file);
    }
}