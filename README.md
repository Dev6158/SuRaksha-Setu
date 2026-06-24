<div align="center">

<img src="https://img.shields.io/badge/Canara%20Bank-SuRaksha%20Cyber%20Hackathon%202.0-blue?style=for-the-badge&logo=shield&logoColor=white" alt="Hackathon Badge"/>

# 🛡️ SuRaksha-Setu

### *सुरक्षा-सेतु — Bridging the Gap Between Banking and Cyber Security*

**A next-generation cybersecurity platform for real-time document fraud detection and agentic regulatory compliance in the Indian banking ecosystem.**

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

> *In an era of rapid banking digitization, traditional security and manual compliance processes are proving insufficient to address the scale and sophistication of modern threats.*

SuRaksha-Setu addresses **two critical problem areas** identified by Canara Bank:

### 1. 🔍 Real-Time Anomaly Detection in Financial Documents
Banks process thousands of documents daily — loan applications, land records, income certificates, and financial statements. Manual verification is slow, error-prone, and easily defeated by sophisticated forgeries. The need is for an **automated, real-time system** to detect tampering or forgery in these documents at scale.

### 2. 🤖 Agentic Regulatory Intelligence & Compliance
The Indian banking sector operates under a constantly evolving regulatory landscape (RBI circulars, SEBI guidelines, PMLA amendments, etc.). Tracking these changes and validating departmental compliance manually is a massive operational burden. The need is for an **AI agent** that autonomously monitors, interprets, and validates regulatory changes.

---

## 💡 Our Solution

**SuRaksha-Setu** (Security Bridge) is a unified platform that combines:

- A **Document Intelligence Engine** powered by computer vision and ML to detect forgery, tampering, and inconsistencies in financial documents in real time.
- An **Agentic Compliance Copilot** that autonomously crawls regulatory sources, extracts actionable directives, and verifies departmental compliance status — all without human intervention.

Together, these modules act as a *bridge* (Setu) between raw data and trustworthy, secure banking operations.

---

## ✨ Key Features

### 📄 Document Fraud Detection
- **Real-time tamper detection** — Identifies pixel-level manipulations, font inconsistencies, and metadata anomalies in uploaded documents
- **Multi-document support** — Handles land records, income proofs, bank statements, and financial certificates
- **Confidence scoring** — Each document receives an authenticity score with an explainable risk breakdown
- **Alert & escalation pipeline** — Flags suspicious documents with automated escalation to verification officers

### 🤖 Agentic Regulatory Compliance
- **Autonomous regulatory monitoring** — Continuously tracks RBI, SEBI, MCA, and PMLA regulatory updates
- **Semantic change parsing** — Uses NLP to extract actionable compliance tasks from dense regulatory text
- **Departmental validation** — Checks if each bank department has completed the required compliance actions
- **Audit trail generation** — Maintains a timestamped log of regulatory changes and compliance status

### 🔐 Security & Privacy
- All document analysis happens **on-premise** — sensitive data never leaves the bank's infrastructure
- Role-based access control (RBAC) for compliance dashboards
- End-to-end encryption for all document pipelines

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        SuRaksha-Setu                        │
│                                                             │
│  ┌──────────────┐          ┌───────────────────────────┐   │
│  │   Document   │          │   Regulatory Compliance   │   │
│  │  Upload API  │          │        Agentic Engine     │   │
│  └──────┬───────┘          └──────────────┬────────────┘   │
│         │                                 │                 │
│  ┌──────▼───────┐          ┌──────────────▼────────────┐   │
│  │  Preprocessing│          │  Regulatory Source Crawler│   │
│  │  & OCR Layer │          │  (RBI / SEBI / MCA feeds) │   │
│  └──────┬───────┘          └──────────────┬────────────┘   │
│         │                                 │                 │
│  ┌──────▼───────┐          ┌──────────────▼────────────┐   │
│  │  ML Anomaly  │          │   NLP Directive Extractor │   │
│  │  Detection   │          │   & Action Item Generator │   │
│  └──────┬───────┘          └──────────────┬────────────┘   │
│         │                                 │                 │
│  ┌──────▼───────┐          ┌──────────────▼────────────┐   │
│  │  Risk Score  │          │  Compliance Validator &   │   │
│  │  & Alert     │          │  Audit Trail Logger       │   │
│  └──────┬───────┘          └──────────────┬────────────┘   │
│         └──────────────┬──────────────────┘                │
│                        │                                    │
│               ┌────────▼────────┐                          │
│               │  Unified Dashboard (React Frontend)        │
│               └─────────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React.js, Tailwind CSS |
| **Backend** | Python (FastAPI / Flask) |
| **Document OCR** | Tesseract OCR, OpenCV |
| **ML / AI Models** | Scikit-learn, PyTorch / TensorFlow |
| **NLP (Compliance)** | spaCy, HuggingFace Transformers |
| **Agentic Framework** | LangChain / LlamaIndex |
| **Database** | PostgreSQL, Redis (caching) |
| **Storage** | MinIO (on-premise object storage) |
| **Auth** | JWT + RBAC |
| **DevOps** | Docker, Docker Compose |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Dev6158/SuRaksha-Setu.git
cd SuRaksha-Setu

# 2. Set up backend
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Set up frontend
cd ../frontend
npm install

# 4. Configure environment
cp .env.example .env
# Edit .env with your database and API credentials

# 5. Start all services with Docker
cd ..
docker-compose up --build
```

### Running Locally (without Docker)

```bash
# Start backend
cd backend
uvicorn main:app --reload --port 8000

# Start frontend (new terminal)
cd frontend
npm run dev
```

The app will be available at `http://localhost:3000`

---

## 📁 Project Structure

```
SuRaksha-Setu/
├── backend/
│   ├── api/                    # FastAPI route handlers
│   ├── models/                 # ML model definitions & weights
│   ├── services/
│   │   ├── document_engine/    # OCR, tamper detection pipeline
│   │   └── compliance_agent/   # Regulatory crawler & NLP agent
│   ├── utils/                  # Helpers, preprocessing tools
│   ├── requirements.txt
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── components/         # Reusable React components
│   │   ├── pages/              # Dashboard, Upload, Compliance pages
│   │   └── services/           # API integration layer
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 👥 Team

| Name | Role |
|------|------|
| Procheta | UI/UX & Frontend Development |
| Oishika | Backend Engineering |
| Amrita | DevOps & Integration |
| Shreya | AI/ML Engineering |
| Debansh | Team Lead · Architecture Design · AI/ML Engineering |

---

## 📊 Evaluation Alignment

| Criterion | Our Approach |
|-----------|-------------|
| **Relevance to Theme** | Directly addresses both problem statements issued by Canara Bank |
| **Innovation & Uniqueness** | Combines agentic AI with real-time document forensics in a single platform |
| **Feasibility** | Modular architecture — each component can be deployed independently |
| **Impact** | Targets fraud prevention and compliance automation for a bank serving crores of customers |
| **Technical Execution** | ML + NLP + OCR pipeline with a production-ready REST API and dashboard |
| **Real-World Scalability** | Containerized deployment, horizontally scalable, on-premise data residency |

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

Built with ❤️ for **Canara Bank SuRaksha Cyber Hackathon 2.0**

*सुरक्षित भारत, डिजिटल भारत — Secure India, Digital India*

</div>
