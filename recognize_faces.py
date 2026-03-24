"""
recognize_faces.py
Live webcam face recognition test.
Usage: python recognize_faces.py
"""

import cv2
import face_recognition
import numpy as np
import pickle
import os
from dotenv import load_dotenv

load_dotenv()

DATASET_PATH = os.getenv("DATASET_PATH", "dataset")
ENCODINGS_FILE = os.path.join(DATASET_PATH, "encodings.pkl")
TOLERANCE = float(os.getenv("FACE_RECOGNITION_TOLERANCE", "0.45"))


def load_encodings():
    if not os.path.exists(ENCODINGS_FILE):
        print("❌ Encodings file not found. Run training first:")
        print("   python attendance_system.py train")
        return [], [], []

    with open(ENCODINGS_FILE, "rb") as f:
        data = pickle.load(f)
    print(f"✅ Loaded {len(data['encodings'])} face encodings")
    return data["encodings"], data["names"], data["roll_numbers"]


def run_live_recognition():
    known_encodings, known_names, known_rolls = load_encodings()
    if not known_encodings:
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot open camera")
        return

    print("\n🎥 Live face recognition started. Press Q to quit.\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Resize for speed
        small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small)
        face_encodings = face_recognition.face_encodings(rgb_small, face_locations)

        for face_encoding, face_location in zip(face_encodings, face_locations):
            distances = face_recognition.face_distance(known_encodings, face_encoding)
            best_idx = np.argmin(distances) if len(distances) > 0 else -1

            name = "Unknown"
            roll = ""
            color = (0, 0, 255)  # Red for unknown
            confidence = 0

            if best_idx >= 0 and distances[best_idx] <= TOLERANCE:
                name = known_names[best_idx]
                roll = known_rolls[best_idx] if best_idx < len(known_rolls) else ""
                confidence = round((1 - distances[best_idx]) * 100, 1)
                color = (0, 255, 100)  # Green for recognized

            # Scale back up
            top, right, bottom, left = [v * 4 for v in face_location]
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom - 50), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, f"{name} ({roll})",
                        (left + 6, bottom - 28), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            if confidence > 0:
                cv2.putText(frame, f"Conf: {confidence}%",
                            (left + 6, bottom - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

        cv2.putText(frame, "Smart Attendance AI — Live Recognition",
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 255, 200), 2)
        cv2.putText(frame, "Press Q to quit",
                    (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        cv2.imshow("Smart Attendance AI", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("\n✅ Recognition stopped.")


if __name__ == "__main__":
    run_live_recognition()
