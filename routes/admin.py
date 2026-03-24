from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from database import supabase_admin
from utils.security import get_current_user, require_admin, hash_password

router = APIRouter(prefix="/admin", tags=["Admin"])


class FacultyCreate(BaseModel):
    faculty_name: str
    email: str
    department_id: str
    password: str


class FacultyUpdate(BaseModel):
    faculty_name: Optional[str] = None
    email: Optional[str] = None
    department_id: Optional[str] = None


class StudentCreate(BaseModel):
    student_name: str
    student_id: str
    email: str
    department: str
    department_id: str
    year: int
    year_id: str
    section: str
    section_id: str
    parent_email: Optional[str] = None
    password: str


class StudentUpdate(BaseModel):
    student_name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    year: Optional[int] = None
    section: Optional[str] = None
    parent_email: Optional[str] = None


class ClassCreate(BaseModel):
    faculty_id: str
    subject_id: str
    department_id: str
    year_id: str
    section_id: str


class AnnouncementRequest(BaseModel):
    subject: str
    message: str
    target: str = "all"  # all | students | faculty


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_admin_stats(current_user: dict = Depends(get_current_user)):
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
        "total_records": len(att_data),
    }


# ── Faculty Management ────────────────────────────────────────────────────────

@router.get("/faculty")
async def get_all_faculty(current_user: dict = Depends(get_current_user)):
    res = supabase_admin.table("faculty") \
        .select("*, departments(department_name)").order("faculty_name").execute()
    faculty = res.data or []
    result = []
    for f in faculty:
        dept = f.pop("departments", {}) or {}
        f["department_name"] = dept.get("department_name", "")
        result.append(f)
    return result


@router.post("/faculty")
async def add_faculty(
    data: FacultyCreate,
    current_user: dict = Depends(get_current_user),
):
    existing = supabase_admin.table("faculty").select("id").eq("email", data.email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Email already exists")

    res = supabase_admin.table("faculty").insert({
        "faculty_name": data.faculty_name,
        "email": data.email,
        "department_id": data.department_id,
        "password_hash": hash_password(data.password),
    }).execute()

    return {"message": "Faculty added successfully", "faculty": res.data[0] if res.data else {}}


@router.put("/faculty/{faculty_id}")
async def update_faculty(
    faculty_id: str,
    data: FacultyUpdate,
    current_user: dict = Depends(get_current_user),
):
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    supabase_admin.table("faculty").update(update_data).eq("id", faculty_id).execute()
    return {"message": "Faculty updated successfully"}


@router.delete("/faculty/{faculty_id}")
async def delete_faculty(
    faculty_id: str,
    current_user: dict = Depends(get_current_user),
):
    supabase_admin.table("faculty").delete().eq("id", faculty_id).execute()
    return {"message": "Faculty removed successfully"}


# ── Student Management ────────────────────────────────────────────────────────

@router.get("/students")
async def get_all_students(current_user: dict = Depends(get_current_user)):
    res = supabase_admin.table("students").select("*").order("student_name").execute()
    return res.data or []


@router.post("/students")
async def add_student(
    data: StudentCreate,
    current_user: dict = Depends(get_current_user),
):
    existing = supabase_admin.table("students").select("student_id") \
        .eq("student_id", data.student_id).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Student ID already exists")

    res = supabase_admin.table("students").insert({
        "student_name": data.student_name,
        "student_id": data.student_id,
        "email": data.email,
        "department": data.department,
        "department_id": data.department_id,
        "year": data.year,
        "year_id": data.year_id,
        "section": data.section,
        "section_id": data.section_id,
        "parent_email": data.parent_email,
        "password_hash": hash_password(data.password),
    }).execute()

    return {"message": "Student added successfully", "student": res.data[0] if res.data else {}}


@router.put("/students/{student_id}")
async def update_student(
    student_id: str,
    data: StudentUpdate,
    current_user: dict = Depends(get_current_user),
):
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    supabase_admin.table("students").update(update_data).eq("student_id", student_id).execute()
    return {"message": "Student updated successfully"}


@router.delete("/students/{student_id}")
async def delete_student(
    student_id: str,
    current_user: dict = Depends(get_current_user),
):
    supabase_admin.table("students").delete().eq("student_id", student_id).execute()
    return {"message": "Student deleted successfully"}


# ── Class Management ──────────────────────────────────────────────────────────

@router.get("/classes")
async def get_all_classes(current_user: dict = Depends(get_current_user)):
    res = supabase_admin.table("classes") \
        .select("*, subjects(subject_name), faculty(faculty_name), departments(department_name), years(year_number), sections(section_name)") \
        .execute()
    classes = res.data or []
    result = []
    for c in classes:
        subj = c.pop("subjects", {}) or {}
        fac = c.pop("faculty", {}) or {}
        dept = c.pop("departments", {}) or {}
        year = c.pop("years", {}) or {}
        sec = c.pop("sections", {}) or {}
        c["subject_name"] = subj.get("subject_name", "")
        c["faculty_name"] = fac.get("faculty_name", "")
        c["department_name"] = dept.get("department_name", "")
        c["year_number"] = year.get("year_number", "")
        c["section_name"] = sec.get("section_name", "")
        c["name"] = subj.get("subject_name", "Class")
        result.append(c)
    return result


@router.post("/classes")
async def create_class(
    data: ClassCreate,
    current_user: dict = Depends(get_current_user),
):
    res = supabase_admin.table("classes").insert({
        "faculty_id": data.faculty_id,
        "subject_id": data.subject_id,
        "department_id": data.department_id,
        "year_id": data.year_id,
        "section_id": data.section_id,
    }).execute()
    return {"message": "Class created successfully", "class": res.data[0] if res.data else {}}


@router.delete("/classes/{class_id}")
async def delete_class(
    class_id: str,
    current_user: dict = Depends(get_current_user),
):
    supabase_admin.table("classes").delete().eq("id", class_id).execute()
    return {"message": "Class deleted successfully"}


# ── Assign Faculty to Class ───────────────────────────────────────────────────

@router.put("/classes/{class_id}/assign-faculty")
async def assign_faculty(
    class_id: str,
    faculty_id: str,
    current_user: dict = Depends(get_current_user),
):
    supabase_admin.table("classes").update({"faculty_id": faculty_id}).eq("id", class_id).execute()
    return {"message": "Faculty assigned successfully"}


# ── Recent Activity ───────────────────────────────────────────────────────────

@router.get("/activity")
async def recent_activity(current_user: dict = Depends(get_current_user)):
    res = supabase_admin.table("attendance") \
        .select("student_id, student_name, class_id, status, date, time, subjects(subject_name)") \
        .order("date", desc=True).order("time", desc=True).limit(20).execute()
    return res.data or []


# ── Announcement ──────────────────────────────────────────────────────────────

@router.post("/announcement")
async def send_announcement(
    data: AnnouncementRequest,
    current_user: dict = Depends(get_current_user),
):
    from services.email_service import email_service

    emails = []
    if data.target in ("all", "students"):
        res = supabase_admin.table("students").select("email").execute()
        emails += [s["email"] for s in (res.data or []) if s.get("email")]

    if data.target in ("all", "faculty"):
        res = supabase_admin.table("faculty").select("email").execute()
        emails += [f["email"] for f in (res.data or []) if f.get("email")]

    sent = 0
    for email in emails:
        result = await email_service.send_custom_message(
            to_email=email,
            subject=data.subject,
            body=data.message,
        )
        if result.get("success"):
            sent += 1

    return {"message": f"Announcement sent to {sent} recipients", "total": len(emails)}


# ── Attendance Reports ────────────────────────────────────────────────────────

@router.get("/reports/attendance")
async def attendance_report(current_user: dict = Depends(get_current_user)):
    res = supabase_admin.table("attendance") \
        .select("*, subjects(subject_name), faculty(faculty_name)") \
        .order("date", desc=True).limit(100).execute()
    return res.data or []


@router.get("/reports/low-attendance")
async def low_attendance_report(current_user: dict = Depends(get_current_user)):
    students_res = supabase_admin.table("students").select("student_id, student_name, department, email, parent_email").execute()
    students = students_res.data or []

    low_attendance = []
    for student in students:
        sid = student["student_id"]
        att = supabase_admin.table("attendance").select("status").eq("student_id", sid).execute()
        records = att.data or []
        if not records:
            continue
        total = len(records)
        present = len([r for r in records if r.get("status") == "present"])
        pct = round(present / total * 100, 1)
        if pct < 75:
            low_attendance.append({
                "student_id": sid,
                "student_name": student.get("student_name"),
                "department": student.get("department"),
                "email": student.get("email"),
                "parent_email": student.get("parent_email"),
                "total": total,
                "present": present,
                "absent": total - present,
                "percentage": pct,
            })

    return sorted(low_attendance, key=lambda x: x["percentage"])
