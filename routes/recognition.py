from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import base64
from services.face_recognition_service import face_service
from services.camera_attendance_service import camera_attendance_service
from utils.security import get_current_user, require_faculty, require_admin

router = APIRouter(prefix="/face", tags=["Face Recognition"])


class RecognizeRequest(BaseModel):
    image: str        # base64 encoded image
    class_id: str


class RegisterFaceRequest(BaseModel):
    student_id: str
    name: str
    roll_number: str
    image: str        # base64 encoded image


class CameraFrameRequest(BaseModel):
    image: str        # base64 encoded frame
    class_id: str
    faculty_id: str


@router.post("/recognize")
async def recognize_face(
    req: RecognizeRequest,
    current_user: dict = Depends(require_faculty),
):
    """Recognize a face from a base64 image and return student info."""
    result = face_service.recognize_face(req.image)
    return result


@router.post("/camera/process")
async def process_camera_frame(
    req: CameraFrameRequest,
    current_user: dict = Depends(require_faculty),
):
    """
    Main endpoint used by mobile app AI Camera screen.
    Recognizes face + marks attendance in one call.
    """
    result = await camera_attendance_service.process_frame(
        image_base64=req.image,
        class_id=req.class_id,
        faculty_id=req.faculty_id,
    )
    return result


@router.post("/register")
async def register_face(
    req: RegisterFaceRequest,
    current_user: dict = Depends(require_faculty),
):
    """Register a student's face for recognition."""
    result = face_service.register_face(
        student_id=req.student_id,
        name=req.name,
        roll_number=req.roll_number,
        image_base64=req.image,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result


@router.post("/register/upload/{roll_number}")
async def register_face_upload(
    roll_number: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_faculty),
):
    """Register face via file upload."""
    from database import supabase_admin

    # Get student info
    res = supabase_admin.table("profiles").select("id, name, roll_number") \
        .eq("roll_number", roll_number).single().execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Student not found")

    student = res.data
    image_bytes = await file.read()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    result = face_service.register_face(
        student_id=student["id"],
        name=student["name"],
        roll_number=student["roll_number"],
        image_base64=image_base64,
    )
    return result


@router.post("/train")
async def train_model(current_user: dict = Depends(require_admin)):
    """Re-train face recognition model from dataset folder."""
    result = face_service.train_from_dataset()
    return result


@router.get("/stats")
async def get_face_stats(current_user: dict = Depends(get_current_user)):
    """Get face recognition model statistics."""
    return face_service.get_stats()


@router.get("/camera/summary/{class_id}")
async def get_camera_summary(
    class_id: str,
    current_user: dict = Depends(require_faculty),
):
    """Get today's attendance summary for a class."""
    return await camera_attendance_service.get_today_summary(class_id)
