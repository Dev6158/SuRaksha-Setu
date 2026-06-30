import cv2
import numpy as np

for name in ["Aadhar_01_img.png", "Aadhar_02_img.png"]:
    img = cv2.imread(name)
    print(f"--- {name} ---")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if hierarchy is not None:
        hierarchy = hierarchy[0]
        for i in range(len(contours)):
            k = i
            d = 0
            while hierarchy[k][2] != -1:
                k = hierarchy[k][2]
                d += 1
            if d >= 2:
                x, y, w, h = cv2.boundingRect(contours[i])
                ratio = w / float(h)
                area = cv2.contourArea(contours[i])
                print(f"Index {i}: bbox=({x},{y},{w},{h}), ratio={ratio:.2f}, area={area:.1f}")
