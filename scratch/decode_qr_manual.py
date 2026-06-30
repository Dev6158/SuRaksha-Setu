import cv2
import numpy as np

img = cv2.imread("Aadhar_02_img.png")
# Crop QR code area
qr_crop = img[600:900, 420:720]
cv2.imwrite("qr_crop.png", qr_crop)

# Try decoding on various preprocessed versions
detector = cv2.QRCodeDetector()

# 1. Raw crop
data, _, _ = detector.detectAndDecode(qr_crop)
print("Raw crop:", data)

# 2. Grayscale & Resize
gray = cv2.cvtColor(qr_crop, cv2.COLOR_BGR2GRAY)
for scale in [1.5, 2.0, 3.0, 4.0]:
    resized = cv2.resize(gray, (0,0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # Simple thresholding
    _, thresh1 = cv2.threshold(resized, 127, 255, cv2.THRESH_BINARY)
    data, _, _ = detector.detectAndDecode(thresh1)
    if data:
        print(f"Scale {scale} Threshold: {data[:100]}")
        break

    # Otsu thresholding
    _, thresh2 = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    data, _, _ = detector.detectAndDecode(thresh2)
    if data:
        print(f"Scale {scale} Otsu: {data[:100]}")
        break

    # Adaptive thresholding
    thresh3 = cv2.adaptiveThreshold(resized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    data, _, _ = detector.detectAndDecode(thresh3)
    if data:
        print(f"Scale {scale} Adaptive: {data[:100]}")
        break
else:
    print("Could not decode cropped QR code")
