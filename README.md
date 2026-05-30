# Suraksha Setu

AI-Powered Banking Fraud Detection & Document Verification Platform

## Overview

Suraksha Setu is an intelligent fraud detection platform designed for banking institutions to automate document verification, detect inconsistencies across submitted records, and identify potentially fraudulent applications before approval.

The system combines:

* Cross-document entity validation
* Sensitive information masking
* Behavioral anomaly detection
* Machine learning risk scoring
* Explainable fraud assessment

## Problem Statement

Banks process thousands of customer documents daily including:

* PAN Cards
* Aadhaar Cards
* Salary Slips
* Bank Statements
* Loan Documents

Manual verification is time-consuming and prone to errors. Fraudulent applicants often submit manipulated or inconsistent information.

Suraksha Setu automates this verification workflow using AI and Machine Learning.

## Features

### Cross Document Validation

* Extracts Names
* Extracts PAN numbers
* Extracts Employer Information
* Extracts Income Details
* Detects contradictions across documents

### Privacy Protection

* Aadhaar masking before processing
* Sensitive information protection

### Machine Learning Risk Engine

* Isolation Forest based anomaly detection
* Behavioral profile analysis
* Risk scoring pipeline

### Explainable Outputs

* Fraud indicators
* Contradiction reports
* Risk classification

## Project Structure

```text
.
├── cross_document_graph.py
├── schemas.py
├── train_and_persist.py
├── requirements.txt
├── README.md
```

## Installation

```bash
pip install -r requirements.txt
```

## Running Model Training

```bash
python train_and_persist.py
```

## Example Use Case

1. Customer uploads salary slip.
2. Customer uploads bank statement.
3. System extracts entities.
4. System compares employer and income information.
5. Contradictions are flagged.
6. Risk score is generated.
7. Reviewer receives fraud assessment report.

## Technology Stack

* Python
* FastAPI
* Scikit-Learn
* Pandas
* NumPy
* Pydantic

## Future Enhancements

* OCR Integration (EasyOCR)
* Document Forensics (ELA)
* Metadata Analysis
* Moiré Pattern Detection
* LLM-based Fraud Explanations
* Real-time Banking Integration

## Team

Canara Bank Hackathon Team

Project: Suraksha Setu
