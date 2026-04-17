from datetime import date, datetime
from database import supabase_admin
from services.face_recognition_service import face_service


def get_current_period() -> int:
    """
    Returns period number based on current time.
    Period 1: 9:00 - 10:00
    Period 2: 10:00 - 11:00
    Period 3: 11:00 - 12:00
    Period 4: 12:00 - 13:00
    Period 5: 13:00 - 14:00
    Period 6: 14:00 - 15:00
    Period 7: 15:00 - 16:00
    """
    hour = datetime.now().hour
    if hour < 9:
        return 1
    elif hour < 10:
        return 1
    elif hour < 11:
        return 2
    elif hour < 12:
        return 3
    elif hour < 13:
        return 4
    elif hour < 14:
        return 5
    elif hour < 15:
        return 6
    elif hour < 16:
        return 7
    else:
        return 7


class CameraAttendanceService:

    async def process_frame(self, image_base64: str, class_id: str, faculty_id: str) -> dict:

        # ✅ Validate class_id
        if not class_id or class_id.strip() == "":
            return {
                "success": False,
                "recognized": False,
                "reason": "No class selected. Please select a class before scanning.",
            }

        # ✅ Validate faculty_id
        if not faculty_id or faculty_id.strip() == "":
            return {
                "success": False,
                "recognized": False,
                "reason": "Faculty ID is missing.",
            }

        result = face_service.recognize_face(image_base64)

        if not result.get("recognized"):
            return {
                "success": False,
                "recognized": False,
                "reason": result.get("reason", "Face not recognized"),
            }

        roll_number = result.get("roll_number")
        name = result.get("name")
        confidence = result.get("confidence", 0)

        # Get student from DB
        student_res = supabase_admin.table("students") \
            .select("student_id, student_name") \
            .eq("student_id", roll_number).execute()

        if not student_res.data:
            return {
                "success": False,
                "recognized": True,
                "reason": "Student not found in database",
                "roll_number": roll_number,
            }

        student = student_res.data[0]
        student_id = student["student_id"]
        student_name = student["student_name"]

        # Get subject_id from class
        try:
            class_res = supabase_admin.table("classes").select("subject_id") \
                .eq("id", class_id).execute()
            subject_id = class_res.data[0]["subject_id"] if class_res.data else None
        except Exception:
            subject_id = None

        today = str(date.today())
        now_time = datetime.now().strftime("%H:%M:%S")

        # ✅ Get current period based on time
        current_period = get_current_period()

        # ✅ Check if already marked for THIS period (not whole day)
        existing = supabase_admin.table("attendance").select("id, status") \
            .eq("student_id", student_id) \
            .eq("class_id", class_id) \
            .eq("date", today) \
            .eq("period", current_period) \
            .execute()

        if existing.data:
            return {
                "success": True,
                "recognized": True,
                "already_marked": True,
                "student_id": student_id,
                "name": student_name,
                "roll_number": student_id,
                "confidence": confidence,
                "status": existing.data[0]["status"],
                "period": current_period,
            }

        # ✅ Mark attendance for current period
        att_res = supabase_admin.table("attendance").insert({
            "student_id": student_id,
            "student_name": student_name,
            "class_id": class_id,
            "subject_id": subject_id,
            "faculty_id": faculty_id,
            "date": today,
            "time": now_time,
            "period": current_period,
            "status": "present",
        }).execute()

        if att_res.data:
            return {
                "success": True,
                "recognized": True,
                "already_marked": False,
                "student_id": student_id,
                "name": student_name,
                "roll_number": student_id,
                "confidence": confidence,
                "status": "present",
                "period": current_period,
                "attendance_id": att_res.data[0]["id"],
            }

        return {"success": False, "reason": "Failed to save attendance"}

    async def get_today_summary(self, class_id: str) -> dict:
        today = str(date.today())
        res = supabase_admin.table("attendance").select("*") \
            .eq("class_id", class_id).eq("date", today).execute()
        records = res.data or []
        return {
            "date": today,
            "class_id": class_id,
            "total_marked": len(records),
            "present": len([r for r in records if r.get("status") == "present"]),
            "absent": len([r for r in records if r.get("status") == "absent"]),
            "records": records,
        }


camera_attendance_service = CameraAttendanceService()