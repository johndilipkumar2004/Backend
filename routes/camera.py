from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from utils.security import require_faculty
from services.camera_attendance_service import camera_attendance_service

router = APIRouter(prefix="/camera", tags=["Camera"])


class StartSessionRequest(BaseModel):
    class_id: str
    faculty_id: str


class FrameRequest(BaseModel):
    image: str        # base64
    class_id: str
    faculty_id: str


@router.post("/start")
async def start_session(
    req: StartSessionRequest,
    current_user: dict = Depends(require_faculty),
):
    """Start a camera attendance session for a class."""
    return {
        "message": "Camera session started",
        "class_id": req.class_id,
        "faculty_id": req.faculty_id,
        "status": "active",
    }


@router.post("/frame")
async def process_frame(
    req: FrameRequest,
    current_user: dict = Depends(require_faculty),
):
    """
    Process a single camera frame — recognize face and mark attendance.
    This is called repeatedly from the mobile app camera screen.
    """
    result = await camera_attendance_service.process_frame(
        image_base64=req.image,
        class_id=req.class_id,
        faculty_id=req.faculty_id,
    )
    return result


@router.get("/summary/{class_id}")
async def get_session_summary(
    class_id: str,
    current_user: dict = Depends(require_faculty),
):
    """Get today's attendance summary for a class."""
    return await camera_attendance_service.get_today_summary(class_id)


@router.post("/stop/{class_id}")
async def stop_session(
    class_id: str,
    current_user: dict = Depends(require_faculty),
):
    """Stop a camera attendance session."""
    summary = await camera_attendance_service.get_today_summary(class_id)
    return {
        "message": "Camera session stopped",
        "class_id": class_id,
        "summary": summary,
    }
