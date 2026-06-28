<div align="center">

<img src="https://img.shields.io/badge/Canara%20Bank-SuRaksha%20Cyber%20Hackathon%202.0-blue?style=for-the-badge&logo=shield&logoColor=white" alt="Hackathon Badge"/>

# 🛡️ SuRaksha-Setu (सुरक्षा-सेतु)
### *Bridging the Gap Between Banking and Cyber Security*

**A next-generation, on-premise cybersecurity platform merging continuous behavioral telemetry on client devices with instant, zero-trust document forensics for bank verification officers.**

[![Hackathon](https://img.shields.io/badge/Canara%20Bank-SuRaksha%202.0-0057A8?style=flat-square)](https://canarabank.hackerearth.com/)
[![Platform](https://img.shields.io/badge/Platform-HackerEarth-blueviolet?style=flat-square)](https://www.hackerearth.com/)
[![Status](https://img.shields.io/badge/Status-Prototype%20Phase-brightgreen?style=flat-square)]()
[![License](https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square)](LICENSE)

</div>

---

## 📌 Table of Contents

- [About the Hackathon](#-about-the-hackathon)
- [Problem Statement](#-problem-statement)
- [Our Solution](#-our-solution)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [Project Structure](#-project-structure)
- [Team](#-team)
- [Evaluation Alignment](#-evaluation-alignment)

---

## 🏦 About the Hackathon

**SuRaksha Cyber Hackathon 2.0** is a national-level campus hackathon organized by **Canara Bank**, one of India's leading public sector banks, hosted on HackerEarth. The hackathon challenges undergraduate teams to build innovative cybersecurity solutions for the fintech domain.

| Detail | Info |
|--------|------|
| 🏆 Prize Pool | ₹11,00,000 (11 Lakhs) |
| 🎯 Focus Area | Cybersecurity in Fintech & Digital Banking |
| 👥 Team Size | 3–5 Members |
| 🗓️ Prototype Phase | June 1 – June 30, 2026 |
| 🌐 Platform | HackerEarth |

---

## ❗ Problem Statement

SuRaksha-Setu addresses **two critical problem areas** identified by Canara Bank:

### 1. 🔍 Real-Time Anomaly Detection in Financial Documents
Banks process thousands of documents daily — loan applications, land records, income certificates, and financial statements. Manual verification is slow, error-prone, and easily defeated by sophisticated forgeries. The need is for an **automated, real-time system** to detect tampering or forgery in these documents at scale.

### 🤳 2. Physical Session Hijacking (Snatching) & Behavioral Verification
Once a user unlocks their mobile banking app, the session remains active. If the phone is physically snatched, an attacker gains immediate access. The system must passively track interaction telemetry (typing rhythms, swipe curvature, hand tremors) to lock the device or request step-up verification if user behavior changes.

---

## 💡 Our Solution

**SuRaksha-Setu** (Security Bridge) is a unified platform that combines:

* **Customer/Client App (Flutter):** Captures touch pressure, keystroke rhythms, and micro-tremors from the gyroscope to run continuous, on-device behavioral authentication.
* **Document Intelligence Engine (FastAPI):** Powered by computer vision and ML to detect ELA compression mismatches, FFT moiré patterns, and metadata anomalies in uploaded documents.
* **Incident Command Dashboard (Next.js):** Provides bank officers with a premium, real-time dark glassmorphic overview of threat alerts, risk distributions, and verification logs.

---

## ✨ Key Features

### 🤳 1. Continuous Behavioral Biometrics (Client App)
* **Touch Dynamics:** Analyzes swipe velocity ($x, y$), touch dwell time (milliseconds), contact area ($mm^2$), and unique **swipe typing curvature**.
* **Micro-Tremor Gyroscope Tracking:** Captures the unique physical wobble and tilt of the user's hands while typing.
* **On-Device ML:** Trains a blended **Isolation Forest** (14 features) and **One-Class SVM** (7 features) locally in the background.
* **Adaptive Lockout:** Instantly locks the app or triggers step-up verification if telemetry patterns deviate.

### 📄 2. Zero-Trust Document Forensics (ML Engine)
* **Error Level Analysis (ELA):** Detects digital copy-paste edits by highlighting pixel-level JPEG compression mismatches.
* **FFT Moiré Analysis:** Ensures the document is a native copy and not a photo taken of a computer screen.
* **Smart Metadata Classification:** 
  * *Consumer Tools (e.g. `ILovePDF`):* Marked as **Authentic** (risk score $\le 35\%$) with minor warnings (handles cases where real users simply compress files).
  * *Programmatic Generators (e.g. `ConvertAPI`):* Automatically flagged as **Fraudulent** (risk score $\ge 75\%$) to block template fabrications.

### 📊 3. Apple-Style Security Command Dashboard (Admin Web)
* **Glassmorphic UI:** Fully customized dark-mode dashboard with translucent acrylic panels for high-contrast viewing.
* **Responsive Visualizations:** Custom **Recharts Area charts** tracking hourly security incidents and glowing risk distribution progress bars.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        SuRaksha-Setu                        │
│                                                             │
│  ┌──────────────┐          ┌───────────────────────────┐   │
│  │   Document   │          │   Behavioral Telemetry    │   │
│  │  Upload API  │          │   (Swipe, Tap, Gyroscope) │   │
│  └──────┬───────┘          └──────────────┬────────────┘   │
│         │                                 │                 │
│  ┌──────▼───────┐          ┌──────────────▼────────────┐   │
│  │  Preprocessing│          │  Isolation Forest &      │   │
│  │  & ELA/FFT   │          │  One-Class SVM Models     │   │
│  └──────┬───────┘          └──────────────┬────────────┘   │
│         │                                 │                 │
│  ┌──────▼───────┐          ┌──────────────▼────────────┐   │
│  │  ML Anomaly  │          │   Continuous Biometric    │   │
│  │  Detection   │          │   Blended Scoring Engine  │   │
│  └──────┬───────┘          └──────────────┬────────────┘   │
│         │                                 │                 │
│  ┌──────▼───────┐          ┌──────────────▼────────────┐   │
│  │  Risk Score  │          │  Adaptive Lockout &       │   │
│  │  & Alert     │          │  Step-up Verification     │   │
│  └──────┬───────┘          └──────────────┬────────────┘   │
│         └──────────────┬──────────────────┘                │
│                        │                                    │
│               ┌────────▼────────┐                          │
│               │  Unified Dashboard (Next.js Frontend)      │
│               └─────────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Mobile/Web Client** | Flutter, Dart |
| **Admin Dashboard** | Next.js, React, Tailwind CSS, Recharts |
| **Backend API** | Spring Boot, Java 21, Spring Security, Hibernate |
| **Forensic ML Engines** | Python 3.11, FastAPI, OpenCV, NumPy, Scikit-Learn |
| **Database** | PostgreSQL 17, Redis 8 (Alpine) |
| **DevOps** | Docker, Docker Compose |

---

## 🚀 Getting Started

All services run **100% locally** with zero external API dependencies.

### Step 1: Start the Local Backend & ML Stack
```bash
# Navigate to the infra directory
cd infra

# Initialize environment variables from example template
cp .env.example .env

# Boot the local container stack
docker compose up -d
```

### Step 2: Start the Next.js Admin Dashboard
```bash
# Navigate to the dashboard directory
cd ../admin-dashboard

# Install packages
npm install

# Start the dev server
npm run dev
```
Open **[http://localhost:3000/dashboard](http://localhost:3000/dashboard)** in your browser. (Or **[http://localhost:3001/dashboard](http://localhost:3001/dashboard)**).

### Step 3: Run the Flutter Client App (Web)
```bash
# Navigate back to the project root
cd /home/debanshhota/SuRaksha-Setu

# Launch the Flutter app in Chrome
flutter run -d chrome
```

### 💻 Developer CLI Tool
If you want to run quick document evaluations directly from your command line:
```bash
./scan.py Aadhar_02.pdf
./scan.py Aadhar_01.pdf
```

---

## 📁 Project Structure

```
SuRaksha-Setu/
├── admin-dashboard/            # Next.js Admin Command Panel
├── lib/                        # Flutter Client App Source (Views, Telemetry)
├── infra/                      # Docker Compose Configuration & Local Setup
│   ├── docker-compose.yml
│   └── .env.example
├── forensic_engine.py          # ELA & FFT Classifier Microservice
├── behavioral_analytics_engine.py # Swipe & Keystroke Biometric Classifier
├── scan.py                     # Local Developer CLI Tool
└── README.md
```

---

## 👥 Team

| Name | Role |
|------|------|
| Debansh | Team Lead · Architecture Design · AI/ML Engineering |
| Procheta | UI/UX & Frontend Development |
| Oishika | Backend Engineering |
| Amrita | DevOps & Integration |
| Shreya | AI/ML Engineering |

---

## 📊 Evaluation Alignment

| Criterion | Our Approach |
|-----------|-------------|
| **Relevance to Theme** | Directly addresses both document spoofing and device session safety statements issued by Canara Bank |
| **Innovation & Uniqueness** | Combines continuous local behavioral biometrics with instant edge document forensics |
| **Feasibility** | Modular containerized architecture — runs fully offline at the edge with zero external API costs |
| **Impact** | Secures active banking sessions from physical snatches and automates KYC document fraud validation |
| **Technical Execution** | Blended ML pipelines (Isolation Forest + OC-SVM) + Computer Vision (ELA/FFT) + Java/Spring REST APIs |
| **Real-World Scalability** | Horizontal microservices scaling, offline-first execution, and secure on-premise data residency |

---

<div align="center">

Built with ❤️ for **Canara Bank SuRaksha Cyber Hackathon 2.0**

*सुरक्षित भारत, डिजिटल भारत — Secure India, Digital India*

</div>
