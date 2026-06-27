import cv2
import numpy as np

img = cv2.imread('/home/debanshhota/.gemini/antigravity-cli/brain/2fb0ce22-c927-438d-bf76-0fbdbf577825/aadhaar_preview.png')
if img is None:
    print("Could not load image.")
    exit(1)

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
# Try adaptive thresholding or simple binary thresholding
thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

if hierarchy is None:
    print("No contours found.")
    exit(0)

hierarchy = hierarchy[0]
finder_pattern_candidates = 0

for i in range(len(contours)):
    k = i
    c = 0
    # Traverse down the hierarchy tree to find nested contours
    while hierarchy[k][2] != -1:
        k = hierarchy[k][2]
        c += 1
    if c >= 2: # At least 2 levels of nesting (contour inside contour inside contour)
        # Check if the contour is somewhat square/rectangular
        x, y, w, h = cv2.boundingRect(contours[i])
        ratio = w / float(h)
        area = cv2.contourArea(contours[i])
        if 0.7 < ratio < 1.3 and area > 100: # Square-like and not tiny
            finder_pattern_candidates += 1
            print(f"Candidate found at ({x}, {y}, {w}, {h}) with nesting depth {c}, area {area}")

print(f"Total finder pattern candidates: {finder_pattern_candidates}")
