import cv2
import os
import numpy as np

def detect_face_and_flatness(path):
    img = cv2.imread(path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    xml_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(xml_path)
    
    # Detect faces
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=3, minSize=(30, 30))
    if len(faces) == 0:
        print(f"{path}: No face detected")
        return None
        
    for idx, (x, y, w, h) in enumerate(faces):
        # Crop the face
        face_crop = img[y:y+h, x:x+w]
        
        # Calculate flatness
        face_gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
        mean = cv2.blur(face_gray.astype(np.float32), (3, 3))
        mean_sq = cv2.blur((face_gray.astype(np.float32))**2, (3, 3))
        variance = mean_sq - mean**2
        variance[variance < 0] = 0
        std = np.sqrt(variance)
        flat_ratio = np.sum(std < 1.5) / std.size
        print(f"{path}: Face {idx} bbox=({x},{y},{w},{h}), flatness={flat_ratio:.4f}")

detect_face_and_flatness("Aadhar_01_img.png")
detect_face_and_flatness("Aadhar_02_img.png")
