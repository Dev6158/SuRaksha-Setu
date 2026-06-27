import os
import sys
import base64
import xml.etree.ElementTree as ET
import numpy as np
import cv2
from PIL import Image

# Initialize pillow_heif (not strictly needed for JPEG but good practice)
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from forensic_engine import run_ela, run_fft_moire, check_qr_code, _compute_verdict, detect_visual_qr_presence

json_path = "/home/debanshhota/SuRaksha-Setu/Sample_aadhar.json"

if not os.path.exists(json_path):
    print(f"❌ File not found: {json_path}")
    sys.exit(1)

print("Reading XML content from Sample_aadhar.json...")
try:
    with open(json_path, "r", encoding="utf-8") as f:
        xml_content = f.read().strip()
    
    # Parse XML
    root = ET.fromstring(xml_content)
    pht_elem = root.find(".//Pht")
    
    if pht_elem is None or not pht_elem.text:
        print("❌ <Pht> tag not found or empty in XML.")
        sys.exit(1)
        
    pht_base64 = pht_elem.text.strip()
    image_bytes = base64.b64decode(pht_base64)
    print(f"✅ Successfully extracted and decoded photo. Size: {len(image_bytes)} bytes.")
    
    # Save the extracted photo
    extracted_path = "/home/debanshhota/SuRaksha-Setu/scratch/extracted_photo.jpg"
    with open(extracted_path, "wb") as f_out:
        f_out.write(image_bytes)
    print(f"Saved extracted photo to: {extracted_path}")
    
    # Also save to conversation artifacts directory for viewing
    artifact_pht_path = "/home/debanshhota/.gemini/antigravity-cli/brain/2fb0ce22-c927-438d-bf76-0fbdbf577825/extracted_photo.jpg"
    with open(artifact_pht_path, "wb") as f_out:
        f_out.write(image_bytes)
        
except Exception as e:
    print(f"❌ Failed to parse XML/decode base64: {e}")
    sys.exit(1)

# Now analyze the extracted image
print("\n=============================================")
print("🛡️ Analyzing Extracted Aadhaar Photo")
print("=============================================")

try:
    pil_img = Image.open(extracted_path)
    print(f"Image info: Format={pil_img.format}, Size={pil_img.size}, Mode={pil_img.mode}")
    
    rgb_img = pil_img.convert("RGB")
    image_bgr = cv2.cvtColor(np.array(rgb_img), cv2.COLOR_RGB2BGR)
except Exception as e:
    print(f"❌ Failed to decode/convert image: {e}")
    sys.exit(1)

# ELA
ela_result, _ela_vis = run_ela(image_bgr)
print(f"ELA Score: {ela_result.ela_score:.4f} (Flagged: {ela_result.flagged})")
print(f"  Anomaly Ratio: {ela_result.anomaly_pixel_ratio:.4f}")
print(f"  Anomaly Clusters: {ela_result.anomaly_cluster_count}")

# FFT
fft_result, _fft_vis = run_fft_moire(image_bgr)
print(f"FFT Score: {fft_result.fft_score:.4f} (Flagged: {fft_result.flagged})")
print(f"  Periodicity Sigma: {fft_result.periodicity_sigma:.4f}")
print(f"  Moiré Band Energy Ratio: {fft_result.moire_band_energy_ratio:.4f}")

# QR code
qr_detected, qr_data = check_qr_code(image_bgr)
print(f"QR Detected: {qr_detected} (Data: {qr_data})")

# Visual QR presence
qr_visually_present = detect_visual_qr_presence(image_bgr)
print(f"QR Visually Present: {qr_visually_present}")

# Final Score
overall_score = round(0.55 * ela_result.ela_score + 0.45 * fft_result.fft_score, 8)

fraud_indicators = []
if qr_visually_present and not qr_detected:
    overall_score = max(overall_score, 0.75)
    fraud_indicators.append("Visually detected QR code could not be decoded (possible synthetic/AI-generated pattern)")

# Check filename of original file
if check_suspicious_filename(os.path.basename(json_path)):
    overall_score = max(overall_score, 0.90)
    fraud_indicators.append(f"Suspicious filename pattern indicating generated/altered source ('{os.path.basename(json_path)}')")

verdict = _compute_verdict(overall_score)
print("\n=============================================")
print("📊 FORENSIC RESULTS FOR EXTRACTED PHOTO")
print("=============================================")
print(f"Overall Fraud Score: {overall_score:.4f}")
print(f"Verdict:             {verdict}")
if fraud_indicators:
    print(f"Fraud Warnings:      {'; '.join(fraud_indicators)}")
print("=============================================")
