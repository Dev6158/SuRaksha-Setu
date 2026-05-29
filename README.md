# SuRaksha Setu

## AI-Powered Banking Fraud Intelligence & Continuous Authentication Platform

SuRaksha Setu is a next-generation cybersecurity platform designed to protect digital banking systems against both document fraud and account takeover attacks.

Unlike conventional fraud detection systems that focus on a single stage of the banking lifecycle, SuRaksha Setu provides end-to-end protection through:

* Multimodal Document Forensics
* Continuous Behavioral Authentication
* Real-Time Risk Evaluation
* Adaptive Security Responses
* Explainable AI-Based Fraud Intelligence
* Enterprise Security Monitoring Dashboards

The platform combines computer vision, machine learning, behavioral biometrics, digital forensics, and real-time threat analytics into a unified security ecosystem.

---

# Problem Statement

Modern banking systems face two critical attack surfaces:

## Fraudulent Onboarding

Attackers frequently submit forged:

* Salary Slips
* Bank Statements
* Identity Documents
* Property Records
* KYC Documents

Traditional verification systems often fail to detect sophisticated manipulation techniques.

## Session Hijacking & Account Takeover

Even after successful authentication, attackers can:

* Hijack active sessions
* Use stolen credentials
* Operate from compromised devices
* Mimic legitimate user behavior

Most banking systems authenticate users only during login and remain blind to malicious activity afterward.

---

# Our Solution

SuRaksha Setu implements a Zero-Trust Banking Security Architecture.

## Onboarding Security Layer

Uploaded documents undergo advanced forensic analysis using:

* OCR-Based Text Extraction
* Error Level Analysis (ELA)
* Metadata Forensics
* FFT/Moiré Pattern Detection
* CNN-Based Tampering Detection
* Vision-Language Models (VLMs)
* Cross-Document Consistency Analysis

## Runtime Security Layer

After login, the platform continuously evaluates:

* Typing Rhythm
* Swipe Behavior
* Touch Pressure
* Device Motion Patterns
* Accelerometer Data
* Gyroscope Signatures
* Geolocation Consistency
* Navigation Behavior

This enables passive continuous authentication without disrupting legitimate users.

---

# Key Features

## Multimodal Forensic Intelligence

Detects:

* Photoshop Traces
* Image Tampering
* Synthetic Identities
* Metadata Inconsistencies
* Screen Recapture Attacks
* Cross-Document Contradictions

## Behavioral Authentication Engine

Uses:

* Isolation Forest
* One-Class SVM
* Statistical Baselines

to identify abnormal user activity in real time.

## Risk Evaluation Engine

Combines:

* Document Fraud Scores
* Behavioral Anomaly Scores
* Device Trust Metrics
* Geolocation Anomalies
* Transaction Risk Indicators

into a unified dynamic trust score.

## Adaptive Security Responses

| Risk Score | Action                               |
| ---------- | ------------------------------------ |
| 0-30       | Trusted Session                      |
| 31-60      | OTP Verification                     |
| 61-80      | Biometric Challenge                  |
| 81-100     | Session Freeze & Security Escalation |

## Explainable AI

Every security decision includes:

* Risk Reasoning
* Behavioral Deviations
* Fraud Indicators
* Security Recommendations

making the platform suitable for enterprise banking and regulatory environments.

---

# System Architecture

```text
Flutter Mobile Client
        │
        ▼
Spring Boot Orchestrator
        │
 ┌──────┴──────┐
 ▼             ▼
Redis      PostgreSQL
 │
 ▼
FastAPI AI Services
 │
 ├── Document Forensics
 ├── Behavioral Analytics
 ├── Risk Evaluation
 └── Cross-Document Intelligence
        │
        ▼
Next.js Security Dashboard
```

---

# Technology Stack

## Frontend

* Flutter
* Next.js
* TailwindCSS
* Recharts

## Backend

* Spring Boot
* Spring Security
* JWT Authentication
* REST APIs
* WebSockets

## Artificial Intelligence & Machine Learning

* FastAPI
* Scikit-Learn
* OpenCV
* EfficientNet
* ResNet
* Qwen2-VL
* LLaVA
* PaddleOCR

## Database & Infrastructure

* PostgreSQL
* Redis
* Docker
* GitHub Actions

---

# Repository Structure

```text
suraksha-setu-root/
│
├── mobile-client/
├── orchestrator-backend/
├── ai-ml-service/
├── admin-dashboard/
├── infra/
├── integration-tests/
└── .github/workflows/
```

---

# Demonstration Workflow

## Scenario 1: Forged Document Detection

1. User uploads a salary slip.
2. ELA highlights suspicious regions.
3. Metadata analysis detects anomalies.
4. Risk score increases.
5. Explainable forensic report is generated.

## Scenario 2: Session Hijack Detection

1. Legitimate user logs in.
2. Behavioral baseline is established.
3. Attacker simulation is performed.
4. Swipe rhythm and motion patterns deviate.
5. Trust score decreases.
6. OTP or biometric challenge is triggered.
7. Session is frozen if risk continues to escalate.

---

# Why SuRaksha Setu?

Most cybersecurity solutions focus on a single attack surface.

SuRaksha Setu unifies:

* Document Fraud Detection
* Behavioral Biometrics
* Continuous Authentication
* Explainable AI
* Adaptive Security Controls
* Real-Time Risk Intelligence
* Enterprise Security Monitoring

into one integrated banking cybersecurity ecosystem.

---

# Competitive Advantage

| Traditional Fraud Systems        | SuRaksha Setu                 |
| -------------------------------- | ----------------------------- |
| Login-only authentication        | Continuous authentication     |
| Rule-based detection             | AI-powered adaptive detection |
| Single attack surface protection | End-to-end protection         |
| Black-box alerts                 | Explainable AI decisions      |
| Static security controls         | Dynamic risk-based responses  |
| Reactive monitoring              | Proactive threat intelligence |

---

# Future Roadmap

* Federated Learning for privacy-preserving model training
* Real-Time Threat Intelligence Integration
* Advanced Insider Threat Detection
* Multi-Bank Risk Intelligence Sharing
* Graph-Based Fraud Relationship Analysis
* GenAI-Powered Fraud Investigation Assistant
* Regulatory Compliance Reporting Automation

---

# Team

## AI & Machine Learning

- Debansh Hota
- Shreya Pankaj

## Backend & Security

- Debansh Hota
- Oishika Dey
- Amrita Neogi

## Frontend, Dashboard & DevOps

- Procheta Ray
- Amrita Neogi

---

# Vision

To build an intelligent, adaptive, and explainable banking security platform capable of protecting users throughout the entire banking lifecycle, from onboarding verification to real-time transaction monitoring.

---

# License

Developed for cybersecurity innovation, research, and hackathon deployment purposes.

