import os
import sys
import numpy as np
from PIL import Image
import cv2

# Initialize pillow_heif to support AVIF
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    print("✅ Registered HEIF opener for AVIF support.")
except ImportError:
    print("❌ pillow_heif not installed!")
    sys.exit(1)

# Add parent directory to path so we can import forensic_engine and utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from forensic_engine import run_ela, run_fft_moire, check_qr_code, _compute_verdict
    from utils import extract_exif_metadata
    print("✅ Successfully imported forensic engine & utils functions.")
except ImportError as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)

# File path
file_path = "/home/debanshhota/SuRaksha-Setu/20250404112835_Aadhaar-card-generated-using-AI.avif"

if not os.path.exists(file_path):
    print(f"❌ File not found: {file_path}")
    sys.exit(1)

print(f"Opening image: {file_path}")
try:
    with open(file_path, "rb") as f:
        raw_bytes = f.read()
    
    pil_img = Image.open(file_path)
    print(f"Image info: Format={pil_img.format}, Size={pil_img.size}, Mode={pil_img.mode}")
    
    # Convert PIL Image to BGR (OpenCV format)
    rgb_img = pil_img.convert("RGB")
    image_bgr = cv2.cvtColor(np.array(rgb_img), cv2.COLOR_RGB2BGR)
    print(f"Converted to BGR array with shape: {image_bgr.shape}")
except Exception as e:
    print(f"❌ Failed to read/convert image: {e}")
    sys.exit(1)

# Run ELA
print("Running Error Level Analysis (ELA)...")
ela_result, _ela_vis = run_ela(image_bgr)
print(f"  ELA Score: {ela_result.ela_score:.4f}")
print(f"  ELA Flagged: {ela_result.flagged}")
print(f"  Anomaly Ratio: {ela_result.anomaly_pixel_ratio:.4f}")
print(f"  Anomaly Clusters: {ela_result.anomaly_cluster_count}")

# Run FFT Moiré
print("Running FFT Moiré/Screen-Recapture Analysis...")
fft_result, _fft_vis = run_fft_moire(image_bgr)
print(f"  FFT Score: {fft_result.fft_score:.4f}")
print(f"  FFT Flagged: {fft_result.flagged}")
print(f"  Periodicity Sigma: {fft_result.periodicity_sigma:.4f}")
print(f"  Moiré Band Energy Ratio: {fft_result.moire_band_energy_ratio:.4f}")

# Check QR code
print("Checking for QR Code...")
qr_detected, qr_data = check_qr_code(image_bgr)
print(f"  QR Detected: {qr_detected}")
print(f"  QR Data: {qr_data}")

# Extract EXIF metadata
print("Extracting EXIF metadata...")
exif_meta = extract_exif_metadata(raw_bytes)
print(f"  Raw EXIF Present: {exif_meta['raw_exif_present']}")
print(f"  Has GPS: {exif_meta['has_gps']}")
print(f"  Editing traces: {exif_meta.get('editing_traces', [])}")
print(f"  Tags: {exif_meta.get('tags', {})}")

# Overall Decision
overall_score = round(0.55 * ela_result.ela_score + 0.45 * fft_result.fft_score, 8)
verdict = _compute_verdict(overall_score)
print("\n=============================================")
print("📊 FORENSIC RESULTS FOR AADHAAR CARD")
print("=============================================")
print(f"Overall Fraud Score: {overall_score:.4f}")
print(f"Verdict:             {verdict}")
print("=============================================")
