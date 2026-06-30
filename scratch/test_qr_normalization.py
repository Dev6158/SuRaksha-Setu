import cv2
import numpy as np

img = cv2.imread("Aadhar_02_img.png")
# Crop QR code area with extra margin (roughly 20 pixels)
qr_crop = img[620:870, 430:690]

# Preprocess
gray = cv2.cvtColor(qr_crop, cv2.COLOR_BGR2GRAY)
norm = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)

# Try decoding
detector = cv2.QRCodeDetector()
data, _, _ = detector.detectAndDecode(norm)
print("Normalized Grayscale decode:", data)

_, binary = cv2.threshold(norm, 127, 255, cv2.THRESH_BINARY)
data, _, _ = detector.detectAndDecode(binary)
print("Binary thresholded decode:", data)
