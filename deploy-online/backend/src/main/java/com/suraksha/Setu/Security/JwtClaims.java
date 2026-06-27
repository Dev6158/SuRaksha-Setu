package com.suraksha.Setu.Security;

import java.util.Map;

public class JwtClaims {

    private final String subject;
    private final Map<String, Object> claims;

    public JwtClaims(String subject, Map<String, Object> claims) {
        this.subject = subject;
        this.claims = claims;
    }

    public String getSubject() {
        return this.subject;
    }

    public Object getClaim(String name) {
        return this.claims.get(name);
    }
}
