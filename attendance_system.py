"""
attendance_system.py
CLI utility for Smart Attendance AI backend management.
Run this to train the model, test recognition, or manage the system.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))


def train():
    """Train face recognition model from dataset folder."""
    print("\n🤖 Training face recognition model...")
    from services.face_recognition_service import face_service
    result = face_service.train_from_dataset()
    if result["success"]:
        print(f"✅ {result['message']}")
    else:
        print(f"❌ {result['message']}")


def test_recognition(image_path: str):
    """Test face recognition on a single image."""
    import base64
    print(f"\n🔍 Testing recognition on: {image_path}")
    from services.face_recognition_service import face_service

    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    result = face_service.recognize_face(encoded)
    if result.get("recognized"):
        print(f"✅ Recognized: {result['name']} ({result['roll_number']})")
        print(f"   Confidence: {result['confidence']}%")
    else:
        print(f"❌ Not recognized: {result.get('reason')}")


def stats():
    """Show face recognition model statistics."""
    print("\n📊 Face Recognition Stats:")
    from services.face_recognition_service import face_service
    s = face_service.get_stats()
    print(f"   Total encodings  : {s['total_encodings']}")
    print(f"   Unique students  : {s['unique_students']}")
    print(f"   Encodings file   : {'✅ Found' if s['encodings_file_exists'] else '❌ Not found'}")


def list_students():
    """List all students in dataset folder."""
    dataset_path = os.getenv("DATASET_PATH", "dataset")
    path = Path(dataset_path)
    if not path.exists():
        print("❌ Dataset folder not found")
        return

    print(f"\n📁 Students in dataset ({dataset_path}):")
    for folder in sorted(path.iterdir()):
        if folder.is_dir():
            imgs = list(folder.glob("*.jpg")) + list(folder.glob("*.png"))
            print(f"   {folder.name} — {len(imgs)} image(s)")


def start_server():
    """Start the FastAPI server."""
    import uvicorn
    print("\n🚀 Starting Smart Attendance AI server...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


def show_help():
    print("""
╔══════════════════════════════════════════════════════╗
║          Smart Attendance AI — CLI Tools             ║
╠══════════════════════════════════════════════════════╣
║  python attendance_system.py train                   ║
║      Train model from dataset/ folder                ║
║                                                      ║
║  python attendance_system.py test <image_path>       ║
║      Test recognition on a single image              ║
║                                                      ║
║  python attendance_system.py stats                   ║
║      Show model statistics                           ║
║                                                      ║
║  python attendance_system.py list                    ║
║      List students in dataset/                       ║
║                                                      ║
║  python attendance_system.py server                  ║
║      Start the FastAPI server                        ║
╚══════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
    elif sys.argv[1] == "train":
        train()
    elif sys.argv[1] == "test" and len(sys.argv) > 2:
        test_recognition(sys.argv[2])
    elif sys.argv[1] == "stats":
        stats()
    elif sys.argv[1] == "list":
        list_students()
    elif sys.argv[1] == "server":
        start_server()
    else:
        show_help()
