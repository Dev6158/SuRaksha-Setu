package com.suraksha.Setu.Service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

@Service
public class AiService {

    @Value("${ai.service.url}")
    private String aiServiceUrl;

    private final RestTemplate restTemplate;

    public AiService(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

}