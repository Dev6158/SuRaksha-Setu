package com.suraksha.Setu.Service;

import com.suraksha.Setu.dto.AiResponseDto;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.math.BigDecimal;

@Service
public class AiService {

    @Value("${ai.service.url}")
    private String aiServiceUrl;

    private final RestTemplate restTemplate;

    public AiService(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public AiResponseDto analyzeDocument(MultipartFile file) throws IOException {

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();

        body.add("file", new ByteArrayResource(file.getBytes()) {
            @Override
            public String getFilename() {
                return file.getOriginalFilename();
            }
        });

        HttpEntity<MultiValueMap<String, Object>> requestEntity =
                new HttpEntity<>(body, headers);

        try {
            return restTemplate.postForObject(
                   aiServiceUrl + "/api/v1/forensics/analyze",
                   requestEntity,
                   AiResponseDto.class
            );
        } catch (Exception e) {

            e.printStackTrace();
            AiResponseDto response = new AiResponseDto();
            response.setRiskScore(BigDecimal.ZERO);
            response.setDecision("PENDING_REVIEW");
            response.setSummary("AI service unavailable");

            return response;
        }
    }
}