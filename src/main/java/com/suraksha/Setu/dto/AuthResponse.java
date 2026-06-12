package com.suraksha.Setu.dto;

import java.util.Map;

public class AuthResponse {

    private boolean success;
    private String message;
    private String accessToken;
    private String token;
    private String tokenType;
    private long expiresIn;
    private Map<String, Object> user;

    public AuthResponse() {
    }

    public AuthResponse(String accessToken, String tokenType, long expiresIn) {
        this.success = true;
        this.message = "Authentication successful";
        this.accessToken = accessToken;
        this.token = accessToken;
        this.tokenType = tokenType;
        this.expiresIn = expiresIn;
    }

    public AuthResponse(
            boolean success,
            String message,
            String accessToken,
            String tokenType,
            long expiresIn,
            Map<String, Object> user) {
        this.success = success;
        this.message = message;
        this.accessToken = accessToken;
        this.token = accessToken;
        this.tokenType = tokenType;
        this.expiresIn = expiresIn;
        this.user = user;
    }

    public boolean isSuccess() {
        return this.success;
    }

    public void setSuccess(boolean success) {
        this.success = success;
    }

    public String getMessage() {
        return this.message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public String getAccessToken() {
        return this.accessToken;
    }

    public void setAccessToken(String accessToken) {
        this.accessToken = accessToken;
        this.token = accessToken;
    }

    public String getToken() {
        return this.token;
    }

    public void setToken(String token) {
        this.token = token;
        this.accessToken = token;
    }

    public String getTokenType() {
        return this.tokenType;
    }

    public void setTokenType(String tokenType) {
        this.tokenType = tokenType;
    }

    public long getExpiresIn() {
        return this.expiresIn;
    }

    public void setExpiresIn(long expiresIn) {
        this.expiresIn = expiresIn;
    }

    public Map<String, Object> getUser() {
        return this.user;
    }

    public void setUser(Map<String, Object> user) {
        this.user = user;
    }
}
