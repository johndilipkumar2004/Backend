"""
recognize_faces.py - Smart Attendance AI Live Recognition
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
TOLERANCE = float(os.getenv("FACE_RECOGNITION_TOLERANCE", "0.6"))


def load_encodings():
    if not os.path.exists(ENCODINGS_FILE):
        print("Encodings file not found.")
        return [], [], [], []
    with open(ENCODINGS_FILE, "rb") as f:
        data = pickle.load(f)
    print(f"Loaded {len(data['encodings'])} face encodings")
    return (
        data["encodings"],
        data["names"],
        data["roll_numbers"],
        data.get("student_ids", data["roll_numbers"]),
    )


def draw_rounded_rect(img, pt1, pt2, color, thickness, radius=16):
    x1, y1 = pt1
    x2, y2 = pt2
    cv2.line(img, (x1 + radius, y1), (x2 - radius, y1), color, thickness)
    cv2.line(img, (x1 + radius, y2), (x2 - radius, y2), color, thickness)
    cv2.line(img, (x1, y1 + radius), (x1, y2 - radius), color, thickness)
    cv2.line(img, (x2, y1 + radius), (x2, y2 - radius), color, thickness)
    cv2.ellipse(img, (x1 + radius, y1 + radius), (radius, radius), 180, 0, 90, color, thickness)
    cv2.ellipse(img, (x2 - radius, y1 + radius), (radius, radius), 270, 0, 90, color, thickness)
    cv2.ellipse(img, (x1 + radius, y2 - radius), (radius, radius), 90, 0, 90, color, thickness)
    cv2.ellipse(img, (x2 - radius, y2 - radius), (radius, radius), 0, 0, 90, color, thickness)


def draw_corner_brackets(img, pt1, pt2, color, thickness=3, length=28):
    x1, y1 = pt1
    x2, y2 = pt2
    cv2.line(img, (x1, y1), (x1 + length, y1), color, thickness)
    cv2.line(img, (x1, y1), (x1, y1 + length), color, thickness)
    cv2.line(img, (x2, y1), (x2 - length, y1), color, thickness)
    cv2.line(img, (x2, y1), (x2, y1 + length), color, thickness)
    cv2.line(img, (x1, y2), (x1 + length, y2), color, thickness)
    cv2.line(img, (x1, y2), (x1, y2 - length), color, thickness)
    cv2.line(img, (x2, y2), (x2 - length, y2), color, thickness)
    cv2.line(img, (x2, y2), (x2, y2 - length), color, thickness)


def draw_info_card(img, x1, y2, name, roll, confidence, color):
    card_h = 78
    card_y1 = y2 + 8
    card_y2 = card_y1 + card_h
    card_x2 = x1 + 270
    h, w = img.shape[:2]
    if card_y2 > h - 10:
        card_y1 = y2 - card_h - 8
        card_y2 = card_y1 + card_h
    overlay = img.copy()
    cv2.rectangle(overlay, (x1, card_y1), (card_x2, card_y2), (15, 15, 25), -1)
    cv2.addWeighted(overlay, 0.85, img, 0.15, 0, img)
    draw_rounded_rect(img, (x1, card_y1), (card_x2, card_y2), color, 1, radius=8)
    cv2.putText(img, name, (x1 + 10, card_y1 + 24),
                cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2)
    cv2.putText(img, f"Roll: {roll}", (x1 + 10, card_y1 + 46),
                cv2.FONT_HERSHEY_SIMPLEX, 0.46, (180, 180, 180), 1)
    if confidence > 0:
        bar_x1 = x1 + 10
        bar_x2 = card_x2 - 48
        bar_y = card_y1 + 63
        bar_w = bar_x2 - bar_x1
        filled_w = int(bar_w * min(confidence, 100) / 100)
        cv2.rectangle(img, (bar_x1, bar_y - 5), (bar_x2, bar_y + 5), (50, 50, 50), -1)
        cv2.rectangle(img, (bar_x1, bar_y - 5), (bar_x1 + filled_w, bar_y + 5), color, -1)
        cv2.putText(img, f"{confidence}%", (bar_x2 + 5, bar_y + 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 255, 255), 1)


def run_live_recognition():
    known_encodings, known_names, known_rolls, known_ids = load_encodings()
    if not known_encodings:
        print("No encodings found.")
        return

    # Use DirectShow backend for Windows
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    print("Live face recognition started. Press Q to quit.")

    frame_count = 0
    results = []

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            continue

        frame_count += 1

        if frame_count % 3 == 0:
            small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            face_locs = face_recognition.face_locations(rgb_small)
            face_encs = face_recognition.face_encodings(rgb_small, face_locs)

            results = []
            for enc, loc in zip(face_encs, face_locs):
                distances = face_recognition.face_distance(known_encodings, enc)
                best_idx = int(np.argmin(distances)) if len(distances) > 0 else -1

                if best_idx >= 0 and distances[best_idx] <= TOLERANCE:
                    conf = round((1 - distances[best_idx]) * 100, 1)
                    results.append({
                        "name": known_names[best_idx],
                        "roll": known_rolls[best_idx] if best_idx < len(known_rolls) else "",
                        "confidence": conf,
                        "color": (50, 220, 100),
                        "location": loc,
                        "known": True,
                    })
                else:
                    conf = round((1 - distances[best_idx]) * 100, 1) if best_idx >= 0 else 0
                    results.append({
                        "name": "Unknown Person",
                        "roll": "Not Registered",
                        "confidence": conf,
                        "color": (60, 60, 239),
                        "location": loc,
                        "known": False,
                    })

        h, w = frame.shape[:2]

        # Header
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 45), (10, 10, 20), -1)
        cv2.addWeighted(overlay, 0.82, frame, 0.18, 0, frame)
        cv2.putText(frame, "Smart Attendance AI  |  Live Face Recognition",
                    (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (80, 220, 160), 2)

        for r in results:
            top, right, bottom, left = [v * 4 for v in r["location"]]
            color = r["color"]
            draw_rounded_rect(frame, (left, top), (right, bottom), color, 2, radius=16)
            draw_corner_brackets(frame, (left, top), (right, bottom), color, thickness=3, length=26)
            badge = "RECOGNIZED" if r["known"] else "UNKNOWN"
            badge_color = (40, 160, 70) if r["known"] else (50, 50, 200)
            cv2.rectangle(frame, (left, max(top - 30, 0)), (left + 138, max(top - 5, 0)), badge_color, -1)
            cv2.putText(frame, badge, (left + 6, max(top - 10, 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
            draw_info_card(frame, left, bottom, r["name"], r["roll"], r["confidence"], color)

        # Footer
        overlay2 = frame.copy()
        cv2.rectangle(overlay2, (0, h - 32), (w, h), (10, 10, 20), -1)
        cv2.addWeighted(overlay2, 0.82, frame, 0.18, 0, frame)
        cv2.putText(frame,
                    f"Faces: {len(results)}   |   Tolerance: {TOLERANCE}   |   Press Q to quit",
                    (12, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (160, 160, 160), 1)

        cv2.imshow("Smart Attendance AI", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Recognition stopped.")


if __name__ == "__main__":
    run_live_recognition()