#!/usr/bin/env python3
import os
import sys
import argparse
import requests

def parse_args():
    parser = argparse.ArgumentParser(
        description="🛡️ SuRaksha-Setu: Document Forensics CLI Tool"
    )
    parser.add_argument(
        "file_path",
        help="Path to the document to scan (PDF, JSON, PNG, JPG, XML, etc.)"
    )
    parser.add_argument(
        "--purpose",
        default="Manual CLI Document Check",
        help="Purpose of the verification (default: Manual CLI Document Check)"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8080",
        help="Backend API URL (default: http://localhost:8080)"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    
    # 1. Validate file path
    if not os.path.exists(args.file_path):
        print(f"❌ Error: File not found at '{args.file_path}'")
        sys.exit(1)
        
    print("=============================================================")
    print("🛡️  SURAKSHA-SETU: FORENSIC SCANNER CLI")
    print("=============================================================")
    
    # 2. Login to local backend
    username = os.getenv("DEMO_USER_USERNAME", "demo_user")
    password = os.getenv("DEMO_USER_PASSWORD", "password123")
    user_credentials = {"username": username, "password": password}
    token = None
    
    print("🔑 Authenticating with local backend...")
    try:
        response = requests.post(f"{args.url}/api/v1/auth/login", json=user_credentials)
        if response.status_code == 200:
            token = response.json().get("accessToken")
            print("✅ Authentication successful!")
        else:
            # Try to register if login failed
            print("⚠️ Login failed. Attempting to register demo account...")
            reg_response = requests.post(f"{args.url}/api/v1/auth/register", json=user_credentials)
            if reg_response.status_code in [200, 201]:
                token = reg_response.json().get("accessToken")
                print("✅ Registration & login successful!")
    except Exception as e:
        print(f"❌ Connection error: Could not reach backend at {args.url}")
        print("Please ensure your local Docker containers are running (`docker ps`).")
        sys.exit(1)

    if not token:
        print("❌ Error: Could not obtain authorization token from backend.")
        sys.exit(1)

    # 3. Detect MIME type
    file_name = os.path.basename(args.file_path)
    ext = os.path.splitext(file_name)[1].lower()
    
    mime_types = {
        ".pdf": "application/pdf",
        ".json": "application/json",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".avif": "image/avif",
        ".xml": "application/xml",
    }
    mime_type = mime_types.get(ext, "application/octet-stream")

    # 4. Perform upload and scan
    print(f"📤 Uploading and scanning: {file_name}...")
    try:
        with open(args.file_path, "rb") as f:
            files = {"file": (file_name, f, mime_type)}
            data = {"purpose": args.purpose}
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.post(
                f"{args.url}/api/v1/documents/upload",
                headers=headers,
                files=files,
                data=data
            )
            
        if response.status_code in [200, 201]:
            res = response.json()
            score = res.get("riskScore", 0.0)
            decision = res.get("riskDecision", "UNKNOWN")
            
            # Color coding status
            color_start = "\033[92m" # Green
            if score >= 0.65:
                color_start = "\033[91m" # Red
            elif score >= 0.4:
                color_start = "\033[93m" # Yellow
            color_end = "\033[0m"
            
            print("\n=============================================================")
            print("📊 SCAN RESULT SUMMARY")
            print("=============================================================")
            print(f"Document ID:       {res.get('id')}")
            print(f"Document Name:     {res.get('documentName')}")
            print(f"Risk Score:        {color_start}{score * 100:.1f}%{color_end}")
            print(f"Risk Decision:     {color_start}{decision}{color_end}")
            
            meta = res.get("metadataSnapshot", {})
            print(f"Diagnostic Report: {meta.get('summary')}")
            print("=============================================================")
        else:
            print(f"❌ Scan failed (HTTP {response.status_code}): {response.text}")
    except Exception as e:
        print(f"❌ Error occurred during upload/scan: {e}")

if __name__ == "__main__":
    main()
