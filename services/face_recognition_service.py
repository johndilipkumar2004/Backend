import face_recognition
import numpy as np
import os
import pickle
import cv2
from pathlib import Path
from typing import Optional
import base64
from PIL import Image
import io
from dotenv import load_dotenv

load_dotenv()

DATASET_PATH = os.getenv("DATASET_PATH", "dataset")
ENCODINGS_FILE = os.path.join(DATASET_PATH, "encodings.pkl")
TOLERANCE = float(os.getenv("FACE_RECOGNITION_TOLERANCE", "0.45"))
MIN_CONFIDENCE = float(os.getenv("MIN_FACE_CONFIDENCE", "0.75"))


class FaceRecognitionService:
    def __init__(self):
        self.known_encodings = []
        self.known_names = []
        self.known_roll_numbers = []
        self.known_student_ids = []
        self._load_encodings()

    def _load_encodings(self):
        """Load pre-trained face encodings from disk."""
        if os.path.exists(ENCODINGS_FILE):
            try:
                with open(ENCODINGS_FILE, "rb") as f:
                    data = pickle.load(f)
                    self.known_encodings = data.get("encodings", [])
                    self.known_names = data.get("names", [])
                    self.known_roll_numbers = data.get("roll_numbers", [])
                    self.known_student_ids = data.get("student_ids", [])
                print(f"✅ Loaded {len(self.known_encodings)} face encodings")
            except Exception as e:
                print(f"⚠️ Error loading encodings: {e}")
        else:
            print("⚠️ No encodings file found. Run training first.")

    def _save_encodings(self):
        """Save face encodings to disk."""
        os.makedirs(DATASET_PATH, exist_ok=True)
        with open(ENCODINGS_FILE, "wb") as f:
            pickle.dump({
                "encodings": self.known_encodings,
                "names": self.known_names,
                "roll_numbers": self.known_roll_numbers,
                "student_ids": self.known_student_ids,
            }, f)

    def decode_base64_image(self, image_base64: str) -> np.ndarray:
        """Convert base64 string to numpy array for face_recognition."""
        # Remove data URL prefix if present
        if "," in image_base64:
            image_base64 = image_base64.split(",")[1]
        image_bytes = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        return np.array(image)

    def recognize_face(self, image_base64: str) -> dict:
        """
        Recognize a face from a base64 image.
        Returns student info if recognized, or unknown if not.
        """
        try:
            img_array = self.decode_base64_image(image_base64)

            # Detect face locations
            face_locations = face_recognition.face_locations(img_array, model="hog")
            if not face_locations:
                return {"recognized": False, "reason": "No face detected in image"}

            # Get face encodings
            face_encodings = face_recognition.face_encodings(img_array, face_locations)
            if not face_encodings:
                return {"recognized": False, "reason": "Could not encode face"}

            if not self.known_encodings:
                return {"recognized": False, "reason": "No trained encodings found"}

            # Compare with known faces
            face_encoding = face_encodings[0]
            distances = face_recognition.face_distance(self.known_encodings, face_encoding)
            best_match_idx = np.argmin(distances)
            best_distance = distances[best_match_idx]
            confidence = round((1 - best_distance) * 100, 2)

            if best_distance <= TOLERANCE and confidence >= (MIN_CONFIDENCE * 100):
                return {
                    "recognized": True,
                    "student_id": self.known_student_ids[best_match_idx] if best_match_idx < len(self.known_student_ids) else None,
                    "name": self.known_names[best_match_idx],
                    "roll_number": self.known_roll_numbers[best_match_idx] if best_match_idx < len(self.known_roll_numbers) else "",
                    "confidence": confidence,
                    "distance": round(float(best_distance), 4),
                }
            else:
                return {
                    "recognized": False,
                    "reason": "Face not recognized",
                    "confidence": confidence,
                }

        except Exception as e:
            return {"recognized": False, "reason": f"Error: {str(e)}"}

    def register_face(self, student_id: str, name: str, roll_number: str, image_base64: str) -> dict:
        """Register a new face encoding for a student."""
        try:
            img_array = self.decode_base64_image(image_base64)
            face_locations = face_recognition.face_locations(img_array)
            if not face_locations:
                return {"success": False, "message": "No face detected in image"}

            face_encodings = face_recognition.face_encodings(img_array, face_locations)
            if not face_encodings:
                return {"success": False, "message": "Could not encode face"}

            # Save image to dataset folder
            student_dir = os.path.join(DATASET_PATH, roll_number)
            os.makedirs(student_dir, exist_ok=True)
            existing = len([f for f in os.listdir(student_dir) if f.endswith('.jpg')])
            img_path = os.path.join(student_dir, f"{existing + 1}.jpg")
            img = Image.fromarray(img_array)
            img.save(img_path)

            # Add encoding
            self.known_encodings.append(face_encodings[0])
            self.known_names.append(name)
            self.known_roll_numbers.append(roll_number)
            self.known_student_ids.append(student_id)
            self._save_encodings()

            return {
                "success": True,
                "message": f"Face registered for {name} ({roll_number})",
                "image_count": existing + 1,
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    def train_from_dataset(self) -> dict:
        """Re-train encodings from all images in the dataset folder."""
        try:
            encodings, names, roll_numbers, student_ids = [], [], [], []
            dataset_dir = Path(DATASET_PATH)

            if not dataset_dir.exists():
                return {"success": False, "message": "Dataset folder not found"}

            count = 0
            for student_folder in dataset_dir.iterdir():
                if not student_folder.is_dir():
                    continue
                roll = student_folder.name
                for img_file in student_folder.glob("*.jpg"):
                    try:
                        img = face_recognition.load_image_file(str(img_file))
                        encs = face_recognition.face_encodings(img)
                        if encs:
                            encodings.append(encs[0])
                            names.append(roll)
                            roll_numbers.append(roll)
                            student_ids.append(roll)
                            count += 1
                    except Exception as e:
                        print(f"Error processing {img_file}: {e}")

            self.known_encodings = encodings
            self.known_names = names
            self.known_roll_numbers = roll_numbers
            self.known_student_ids = student_ids
            self._save_encodings()

            return {
                "success": True,
                "message": f"Training complete. {count} face encodings saved.",
                "count": count,
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_stats(self) -> dict:
        return {
            "total_encodings": len(self.known_encodings),
            "unique_students": len(set(self.known_roll_numbers)),
            "encodings_file_exists": os.path.exists(ENCODINGS_FILE),
        }


# Singleton instance
face_service = FaceRecognitionService()
