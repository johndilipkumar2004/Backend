from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import supabase_admin
from utils.security import get_current_user, require_faculty
from services.email_service import email_service
from datetime import date

router = APIRouter(prefix="/messages", tags=["Parent Messages"])


class ParentMessageRequest(BaseModel):
    student_id: str
    parent_email: str
    subject: str
    body: str
    class_name: Optional[str] = ""
    send_email: bool = True


@router.post("/parent")
async def send_parent_message(
    req: ParentMessageRequest,
    current_user: dict = Depends(require_faculty),
):
    student_res = supabase_admin.table("students").select("student_name, student_id") \
        .eq("student_id", req.student_id).execute()
    if not student_res.data:
        raise HTTPException(status_code=404, detail="Student not found")

    email_result = {"success": True, "message": "Skipped"}
    if req.send_email:
        email_result = await email_service.send_custom_message(
            to_email=req.parent_email,
            subject=req.subject,
            body=req.body,
        )

    return {
        "message": "Parent message sent",
        "email_sent": email_result.get("success"),
        "email_message": email_result.get("message"),
    }


@router.post("/parent/alert")
async def send_absence_alert(
    student_id: str,
    class_name: str = "Class",
    current_user: dict = Depends(require_faculty),
):
    student = supabase_admin.table("students") \
        .select("student_name, student_id, parent_email") \
        .eq("student_id", student_id).execute()

    if not student.data or not student.data[0].get("parent_email"):
        raise HTTPException(status_code=400, detail="Student or parent email not found")

    s = student.data[0]
    faculty_res = supabase_admin.table("faculty").select("faculty_name") \
        .eq("id", current_user.get("sub")).execute()
    faculty_name = faculty_res.data[0]["faculty_name"] if faculty_res.data else "Faculty"

    result = await email_service.send_parent_alert(
        parent_email=s["parent_email"],
        student_name=s["student_name"],
        roll_number=s["student_id"],
        class_name=class_name,
        faculty_name=faculty_name,
        date=str(date.today()),
    )
    return result
