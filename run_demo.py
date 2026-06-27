#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path
import urllib.request
import urllib.parse

# We use the virtual environment's packages (requests)
try:
    import requests
except ImportError:
    print("Installing required requests library...")
    os.system("venv/bin/pip install requests")
    import requests

# Base URLs
BACKEND_URL = "http://localhost:8080"
DEFAULT_FILE = "/home/debanshhota/SuRaksha-Setu/docs/screenshots/admin-dashboard.jpeg"

print("=================================================================")
print("🛡️  SuRaksha-Setu — Unified Demo Launcher")
print("=================================================================")

# Check if services are running by pinging the backend health endpoint
try:
    response = requests.get(f"{BACKEND_URL}/actuator/health", timeout=3)
    if response.status_code == 200:
        print("✅ Backend service is running and healthy!")
except Exception:
    print("❌ Backend is not running. Please start the stack first by running:")
    print("   make build")
    sys.exit(1)

# 1. Register / Login
print("\n🔑 Authenticating with backend...")
user_credentials = {"username": "demo_user", "password": "password123"}

token = None
try:
    # Attempt login
    response = requests.post(f"{BACKEND_URL}/api/v1/auth/login", json=user_credentials)
    if response.status_code == 200:
        token = response.json().get("accessToken")
except Exception:
    pass

if not token:
    try:
        # Attempt register
        response = requests.post(f"{BACKEND_URL}/api/v1/auth/register", json=user_credentials)
        if response.status_code in [200, 201]:
            token = response.json().get("accessToken")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        sys.exit(1)

if not token:
    print("❌ Failed to obtain JWT token.")
    sys.exit(1)

print("✅ Authentication successful!")

# 2. File Input
print("=================================================================")
user_input = input(f"Enter the absolute path of the file to verify\n[Press Enter to use default sample: {DEFAULT_FILE}]: ").strip()

file_path = Path(user_input if user_input else DEFAULT_FILE)
if not file_path.exists() or not file_path.is_file():
    print(f"❌ File not found at: {file_path}")
    sys.exit(1)

print(f"\n📤 Uploading and analyzing: {file_path.name}...")

# 3. Perform Upload
try:
    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f, "application/octet-stream")}
        data = {"purpose": "Demo Script Verification"}
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.post(
            f"{BACKEND_URL}/api/v1/documents/upload",
            headers=headers,
            files=files,
            data=data
        )
        
        if response.status_code in [200, 201]:
            report = response.json()
            print("\n=================================================================")
            print("📊 FORENSIC AUDIT REPORT")
            print("=================================================================")
            print(f"Database ID:  {report.get('id')}")
            print(f"Filename:     {report.get('documentName')}")
            print(f"Hash (SHA):   {report.get('sha256Hash')[:20]}...")
            print(f"Risk Score:   {(report.get('riskScore') * 100):.1f}%")
            print(f"Verdict:      {report.get('riskDecision')}")
            print(f"Summary:      {report.get('metadataSnapshot', {}).get('summary')}")
            
            # Print QR/PDF diagnostics if available
            meta = report.get('metadataSnapshot', {})
            if meta.get('qrCodeDetected'):
                print(f"QR Code:      ✅ Detected (Data: {meta.get('qrCodeData')})")
            if meta.get('pdfHasSignature') is not None:
                print(f"Digital Sig:  {'✅ Present (DSC Verified)' if meta.get('pdfHasSignature') else '❌ None Found'}")
            
            print("=================================================================")
            print("🎉 Success! Open http://localhost:3000/dashboard in your browser to view the live dashboard.")
        else:
            print(f"❌ Upload failed with status code {response.status_code}: {response.text}")
except Exception as e:
    print(f"❌ Error performing upload: {e}")
