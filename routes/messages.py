from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from database import supabase_admin
from utils.security import require_faculty
from services.email_service import email_service
from datetime import date

router = APIRouter(prefix="/messages", tags=["Parent Messages"])


class ParentMessageRequest(BaseModel):
    student_id: str
    subject: Optional[str] = None
    body: Optional[str] = None
    class_name: Optional[str] = ""
    send_email: bool = True


class BulkAlertRequest(BaseModel):
    threshold: Optional[float] = 70.0  # send alert if attendance below this %
    class_name: Optional[str] = ""


# ── Send custom message to a student's parent ─────────────────────────────────
@router.post("/parent")
async def send_parent_message(
    req: ParentMessageRequest,
    current_user: dict = Depends(require_faculty),
):
    # 1. Fetch student from DB
    res = supabase_admin.table("students") \
        .select("student_name, student_id, parent_email") \
        .eq("student_id", req.student_id).execute()

    if not res.data:
        raise HTTPException(status_code=404, detail="Student not found")

    student = res.data[0]
    parent_email = student.get("parent_email")

    if not parent_email:
        raise HTTPException(
            status_code=400,
            detail=f"No parent email found for student {req.student_id}"
        )

    # 2. Build subject & body if not provided
    subject = req.subject or f"Attendance Alert - {student['student_name']}"
    body = req.body or f"""Dear Parent/Guardian,

Your child {student['student_name']} (Roll No: {req.student_id}) was marked ABSENT today.

Class   : {req.class_name or 'N/A'}
Faculty : {current_user.get('name', 'Faculty')}
Date    : {date.today()}

Please ensure regular attendance. Minimum 75% attendance is required.

Regards,
Smart Attendance AI System"""

    # 3. Send email
    if req.send_email:
        result = await email_service.send_custom_message(
            to_email=parent_email,
            subject=subject,
            body=body,
        )
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("message"))
        return {
            "success": True,
            "message": f"Email sent to parent ({parent_email})",
            "student": student["student_name"],
            "parent_email": parent_email,
        }
    else:
        return {
            "success": True,
            "message": "Email not sent (send_email=false)",
            "student": student["student_name"],
            "parent_email": parent_email,
        }


# ── Send absence alert using student's stored parent email ────────────────────
@router.post("/parent/alert")
async def send_absence_alert(
    student_id: str,
    class_name: str = "",
    current_user: dict = Depends(require_faculty),
):
    # Fetch student
    res = supabase_admin.table("students") \
        .select("student_name, student_id, parent_email") \
        .eq("student_id", student_id).execute()

    if not res.data:
        raise HTTPException(status_code=404, detail="Student not found")

    student = res.data[0]
    parent_email = student.get("parent_email")

    if not parent_email:
        raise HTTPException(
            status_code=400,
            detail=f"No parent email set for {student_id}"
        )

    result = await email_service.send_parent_alert(
        parent_email=parent_email,
        student_name=student["student_name"],
        roll_number=student["student_id"],
        class_name=class_name or "N/A",
        faculty_name=current_user.get("name", "Faculty"),
        date=str(date.today()),
    )

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message"))

    return {
        "success": True,
        "message": f"Absence alert sent to {parent_email}",
        "student": student["student_name"],
    }


# ── Bulk alert: send to ALL students below attendance threshold ───────────────
@router.post("/parent/bulk-alert")
async def send_bulk_low_attendance_alerts(
    req: BulkAlertRequest,
    current_user: dict = Depends(require_faculty),
):
    # 1. Get all students
    students_res = supabase_admin.table("students") \
        .select("student_id, student_name, parent_email").execute()
    students = students_res.data or []

    sent = []
    failed = []
    skipped = []

    for student in students:
        sid = student["student_id"]
        parent_email = student.get("parent_email")

        if not parent_email:
            skipped.append({"student_id": sid, "reason": "No parent email"})
            continue

        # 2. Calculate attendance percentage
        att_res = supabase_admin.table("attendance") \
            .select("status").eq("student_id", sid).execute()
        records = att_res.data or []
        total = len(records)
        present = len([r for r in records if (r.get("status") or "").lower() == "present"])
        percentage = round(present / total * 100, 1) if total > 0 else 0

        # 3. Only send if below threshold
        if percentage < req.threshold:
            result = await email_service.send_custom_message(
                to_email=parent_email,
                subject=f"Low Attendance Warning - {student['student_name']}",
                body=f"""Dear Parent/Guardian,

Your child {student['student_name']} (Roll No: {sid}) has LOW ATTENDANCE.

Current Attendance : {percentage}%
Required Minimum   : 75%
Class              : {req.class_name or 'All Subjects'}
Date               : {date.today()}

Please ensure your child attends classes regularly.
Failing to maintain 75% attendance may result in exam restrictions.

Regards,
Smart Attendance AI System
{current_user.get('name', 'Faculty')}""",
            )
            if result.get("success"):
                sent.append({"student_id": sid, "name": student["student_name"],
                             "attendance": percentage, "parent_email": parent_email})
            else:
                failed.append({"student_id": sid, "error": result.get("message")})
        else:
            skipped.append({"student_id": sid, "reason": f"Attendance OK ({percentage}%)"})

    return {
        "success": True,
        "summary": {
            "total_students": len(students),
            "emails_sent": len(sent),
            "failed": len(failed),
            "skipped": len(skipped),
        },
        "sent_to": sent,
        "failed": failed,
    }


# ── Get students with low attendance (for faculty to review before sending) ───
@router.get("/low-attendance")
async def get_low_attendance_students(
    threshold: float = 70.0,
    current_user: dict = Depends(require_faculty),
):
    students_res = supabase_admin.table("students") \
        .select("student_id, student_name, parent_email, department, year, section").execute()
    students = students_res.data or []

    low_attendance = []

    for student in students:
        sid = student["student_id"]
        att_res = supabase_admin.table("attendance") \
            .select("status").eq("student_id", sid).execute()
        records = att_res.data or []
        total = len(records)
        present = len([r for r in records if (r.get("status") or "").lower() == "present"])
        percentage = round(present / total * 100, 1) if total > 0 else 0

        if percentage < threshold:
            low_attendance.append({
                **student,
                "attendance_percentage": percentage,
                "total_classes": total,
                "present": present,
                "absent": total - present,
                "has_parent_email": bool(student.get("parent_email")),
            })

    return sorted(low_attendance, key=lambda x: x["attendance_percentage"])