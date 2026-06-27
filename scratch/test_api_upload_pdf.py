import os
import requests

BACKEND_URL = "http://localhost:8080"
file_path = "/home/debanshhota/SuRaksha-Setu/Aadhar_02.pdf"

print("=============================================")
print("🚀 Testing API Upload on Aadhar_02.pdf")
print("=============================================")

# 1. Login
user_credentials = {"username": "demo_user", "password": "password123"}
token = None

try:
    response = requests.post(f"{BACKEND_URL}/api/v1/auth/login", json=user_credentials)
    if response.status_code == 200:
        token = response.json().get("accessToken")
        print("✅ Logged in successfully!")
except Exception as e:
    print("Could not login:", e)
    exit(1)

if not token:
    print("❌ Token missing.")
    exit(1)

# 2. Upload file
print(f"Uploading file: {os.path.basename(file_path)}...")
with open(file_path, "rb") as f:
    files = {"file": (os.path.basename(file_path), f, "application/pdf")}
    data = {"purpose": "Manual Document Check"}
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{BACKEND_URL}/api/v1/documents/upload",
        headers=headers,
        files=files,
        data=data
    )
    
    print(f"Response Status Code: {response.status_code}")
    if response.status_code in [200, 201]:
        res = response.json()
        print("\n=============================================")
        print("📊 API RESPONSE RESULTS")
        print("=============================================")
        print(f"Document ID:      {res.get('id')}")
        print(f"Document Name:    {res.get('documentName')}")
        print(f"Risk Score:       {res.get('riskScore')}")
        print(f"Risk Decision:    {res.get('riskDecision')}")
        
        meta = res.get('metadataSnapshot', {})
        print(f"Summary findings: {meta.get('summary')}")
        print("=============================================")
    else:
        print(f"❌ Upload failed with: {response.text}")
