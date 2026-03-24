from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
from database import supabase_admin
from utils.security import get_current_user, require_faculty, hash_password

router = APIRouter(prefix="/students", tags=["Students"])

class StudentUpdate(BaseModel):
    student_name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    year: Optional[int] = None
    section: Optional[str] = None
    parent_email: Optional[str] = None

@router.get("")
async def get_all_students(
    department: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: dict = Depends(require_faculty),
):
    res = supabase_admin.table("students").select("*").order("student_name").execute()
    students = res.data or []
    if department:
        students = [s for s in students if s.get("department") == department]
    if search:
        s = search.lower()
        students = [st for st in students if
                    s in (st.get("student_name") or "").lower() or
                    s in (st.get("student_id") or "").lower()]
    return students

@router.get("/{student_id}")
async def get_student(student_id: str, current_user: dict = Depends(get_current_user)):
    res = supabase_admin.table("students").select("*").eq("student_id", student_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Student not found")
    return res.data[0]

@router.put("/{student_id}")
async def update_student(
    student_id: str,
    data: StudentUpdate,
    current_user: dict = Depends(get_current_user),
):
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    supabase_admin.table("students").update(update_data).eq("student_id", student_id).execute()
    return {"message": "Student updated"}

@router.get("/{student_id}/attendance")
async def get_student_attendance(
    student_id: str,
    current_user: dict = Depends(get_current_user),
):
    # ✅ No foreign key join — query attendance directly
    res = supabase_admin.table("attendance") \
        .select("*") \
        .eq("student_id", student_id) \
        .order("date", desc=True).execute()
    records = res.data or []

    # Enrich with subject names manually
    subject_cache = {}
    for r in records:
        sid = r.get("subject_id")
        if sid and sid not in subject_cache:
            try:
                s_res = supabase_admin.table("subjects") \
                    .select("subject_name").eq("id", sid).execute()
                subject_cache[sid] = s_res.data[0]["subject_name"] if s_res.data else "Unknown"
            except:
                subject_cache[sid] = "Unknown"
        r["subject_name"] = subject_cache.get(sid, "Class") if sid else "Class"

        # Enrich with faculty name
        fid = r.get("faculty_id")
        if fid:
            try:
                f_res = supabase_admin.table("faculty") \
                    .select("faculty_name").eq("id", fid).execute()
                r["faculty_name"] = f_res.data[0]["faculty_name"] if f_res.data else "Faculty"
            except:
                r["faculty_name"] = "Faculty"
        else:
            r["faculty_name"] = "Faculty"

    total = len(records)
    present = len([r for r in records if (r.get("status") or "").lower() == "present"])
    percentage = round(present / total * 100, 1) if total > 0 else 0

    return {
        "student_id": student_id,
        "total": total,
        "present": present,
        "absent": total - present,
        "percentage": percentage,
        "records": records,
    }

@router.get("/{student_id}/attendance/subjects")
async def get_subject_attendance(
    student_id: str,
    current_user: dict = Depends(get_current_user),
):
    # ✅ No foreign key join — query attendance directly
    res = supabase_admin.table("attendance") \
        .select("status, subject_id") \
        .eq("student_id", student_id).execute()
    records = res.data or []

    # Get all unique subject IDs
    subject_ids = list(set(r.get("subject_id") for r in records if r.get("subject_id")))

    # Fetch subject names
    subject_names = {}
    for sid in subject_ids:
        try:
            s_res = supabase_admin.table("subjects") \
                .select("subject_name").eq("id", sid).execute()
            subject_names[sid] = s_res.data[0]["subject_name"] if s_res.data else "Unknown"
        except:
            subject_names[sid] = "Unknown"

    subjects = {}
    for r in records:
        sid = r.get("subject_id", "unknown")
        name = subject_names.get(sid, "Unknown Subject")
        if sid not in subjects:
            subjects[sid] = {"subject": name, "total": 0, "present": 0}
        subjects[sid]["total"] += 1
        if (r.get("status") or "").lower() == "present":
            subjects[sid]["present"] += 1

    result = []
    for s in subjects.values():
        s["absent"] = s["total"] - s["present"]
        s["percentage"] = round(s["present"] / s["total"] * 100, 1) if s["total"] > 0 else 0
        result.append(s)

    return sorted(result, key=lambda x: x["percentage"])