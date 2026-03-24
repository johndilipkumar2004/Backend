"""
capture_faces.py
Capture face images from webcam for training the recognition model.
Usage: python capture_faces.py <roll_number> <student_name>
"""

import cv2
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATASET_PATH = os.getenv("DATASET_PATH", "dataset")
IMAGES_PER_STUDENT = 20


def capture_faces(roll_number: str, student_name: str):
    save_dir = Path(DATASET_PATH) / roll_number
    save_dir.mkdir(parents=True, exist_ok=True)

    existing = len(list(save_dir.glob("*.jpg")))
    print(f"\n📸 Capturing faces for: {student_name} ({roll_number})")
    print(f"   Save path : {save_dir}")
    print(f"   Target    : {IMAGES_PER_STUDENT} images")
    print(f"   Existing  : {existing} images")
    print("\n   Press SPACE to capture | Press Q to quit\n")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot open camera")
        return

    # Load face detector
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    count = existing
    target = existing + IMAGES_PER_STUDENT

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 100), 2)

        # Overlay info
        cv2.putText(frame, f"Student: {student_name} ({roll_number})",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 100), 2)
        cv2.putText(frame, f"Captured: {count - existing}/{IMAGES_PER_STUDENT}",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
        cv2.putText(frame, "SPACE = Capture  |  Q = Quit",
                    (10, frame.shape[0] - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        cv2.imshow("Smart Attendance AI — Face Capture", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or count >= target:
            break
        elif key == ord(' ') and len(faces) > 0:
            img_path = save_dir / f"{count + 1}.jpg"
            cv2.imwrite(str(img_path), frame)
            count += 1
            print(f"   ✅ Saved image {count - existing}/{IMAGES_PER_STUDENT}")

    cap.release()
    cv2.destroyAllWindows()

    total = len(list(save_dir.glob("*.jpg")))
    print(f"\n✅ Done! Total images for {student_name}: {total}")
    print("   Run 'python attendance_system.py train' to retrain the model.\n")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python capture_faces.py <roll_number> <student_name>")
        print("Example: python capture_faces.py 21CS045 'Arjun Reddy'")
        sys.exit(1)

    roll = sys.argv[1]
    name = " ".join(sys.argv[2:])
    capture_faces(roll, name)
