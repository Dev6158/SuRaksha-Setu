package com.suraksha.Setu.dto;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.math.BigDecimal;

public class AiResponseDto {

    @JsonProperty("riskScore")
    @JsonAlias({"overall_fraud_score", "risk_score"})
    private BigDecimal riskScore;

    @JsonProperty("decision")
    @JsonAlias({"verdict", "risk_decision"})
    private String decision;

    private String summary;

    public BigDecimal getRiskScore() {
        return riskScore;
    }

    public void setRiskScore(BigDecimal riskScore) {
        this.riskScore = riskScore;
    }

    public String getDecision() {
        return decision;
    }

    public void setDecision(String decision) {
        this.decision = decision;
    }

    public String getSummary() {
        return summary;
    }

    public void setSummary(String summary) {
        this.summary = summary;
    }
}