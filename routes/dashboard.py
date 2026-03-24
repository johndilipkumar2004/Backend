from fastapi import APIRouter, Depends, HTTPException
from database import supabase_admin
from utils.security import get_current_user
from datetime import date

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/admin")
async def admin_dashboard(current_user: dict = Depends(get_current_user)):
    students = supabase_admin.table("students").select("student_id", count="exact").execute()
    faculty = supabase_admin.table("faculty").select("id", count="exact").execute()
    classes = supabase_admin.table("classes").select("id", count="exact").execute()
    attendance = supabase_admin.table("attendance").select("status").execute()

    att_data = attendance.data or []
    present = len([a for a in att_data if a.get("status") == "present"])
    rate = round(present / len(att_data) * 100, 1) if att_data else 0

    return {
        "total_students": students.count or 0,
        "total_faculty": faculty.count or 0,
        "total_classes": classes.count or 0,
        "attendance_rate": rate,
        "total_attendance_records": len(att_data),
    }


@router.get("/faculty/{faculty_id}")
async def faculty_dashboard(faculty_id: str, current_user: dict = Depends(get_current_user)):
    today = str(date.today())

    classes_res = supabase_admin.table("classes") \
        .select("*, subjects(subject_name), sections(section_name)") \
        .eq("faculty_id", faculty_id).execute()
    classes = classes_res.data or []

    today_att = supabase_admin.table("attendance").select("status") \
        .eq("faculty_id", faculty_id).eq("date", today).execute()
    today_records = today_att.data or []

    all_att = supabase_admin.table("attendance").select("status") \
        .eq("faculty_id", faculty_id).execute()
    all_records = all_att.data or []
    present = len([r for r in all_records if r.get("status") == "present"])
    rate = round(present / len(all_records) * 100, 1) if all_records else 0

    result_classes = []
    for c in classes:
        subj = c.pop("subjects", {}) or {}
        sec = c.pop("sections", {}) or {}
        c["name"] = subj.get("subject_name", "Class")
        c["section_name"] = sec.get("section_name", "")
        result_classes.append(c)

    return {
        "todays_classes": len(classes),
        "attendance_rate": rate,
        "today_marked": len(today_records),
        "classes": result_classes,
    }


@router.get("/student/{student_id}")
async def student_dashboard(student_id: str, current_user: dict = Depends(get_current_user)):
    student_res = supabase_admin.table("students").select("*") \
        .eq("student_id", student_id).execute()
    if not student_res.data:
        raise HTTPException(status_code=404, detail="Student not found")

    student = student_res.data[0]

    att_res = supabase_admin.table("attendance").select("status, date, subjects(subject_name)") \
        .eq("student_id", student_id).order("date", desc=True).execute()
    records = att_res.data or []

    total = len(records)
    present = len([r for r in records if r.get("status") == "present"])
    absent = total - present
    percentage = round(present / total * 100, 1) if total > 0 else 0

    return {
        "student": {
            "id": student.get("student_id"),
            "name": student.get("student_name"),
            "rollNumber": student.get("student_id"),
            "department": student.get("department"),
            "year": str(student.get("year", "")),
            "section": student.get("section"),
            "email": student.get("email"),
            "parent_email": student.get("parent_email"),
        },
        "attendance": {
            "total": total,
            "present": present,
            "absent": absent,
            "percentage": percentage,
            "status": "Good Standing" if percentage >= 75 else "At Risk",
        },
        "recent_records": records[:10],
    }
