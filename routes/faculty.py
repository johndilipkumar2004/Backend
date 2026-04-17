from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from database import supabase_admin
from utils.security import get_current_user, hash_password

router = APIRouter(prefix="/faculty", tags=["Faculty"])


class FacultyUpdate(BaseModel):
    faculty_name: Optional[str] = None
    email: Optional[str] = None
    department_id: Optional[str] = None


@router.get("")
async def get_all_faculty(current_user: dict = Depends(get_current_user)):
    res = supabase_admin.table("faculty") \
        .select("*, departments(department_name)").order("faculty_name").execute()
    result = []
    for f in (res.data or []):
        dept = f.pop("departments", {}) or {}
        f["department_name"] = dept.get("department_name", "")
        result.append(f)
    return result


@router.get("/{faculty_id}")
async def get_faculty(faculty_id: str, current_user: dict = Depends(get_current_user)):
    res = supabase_admin.table("faculty") \
        .select("*, departments(department_name)") \
        .eq("id", faculty_id).single().execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Faculty not found")
    f = res.data
    dept = f.pop("departments", {}) or {}
    f["department_name"] = dept.get("department_name", "")
    return f


@router.put("/{faculty_id}")
async def update_faculty(
    faculty_id: str,
    data: FacultyUpdate,
    current_user: dict = Depends(get_current_user),
):
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    supabase_admin.table("faculty").update(update_data).eq("id", faculty_id).execute()
    return {"message": "Faculty updated"}


@router.get("/{faculty_id}/classes")
async def get_faculty_classes(faculty_id: str, current_user: dict = Depends(get_current_user)):
    res = supabase_admin.table("classes") \
        .select("*, subjects(subject_name), departments(department_name), years(year_number), sections(section_name)") \
        .eq("faculty_id", faculty_id).execute()
    result = []
    for c in (res.data or []):
        subj = c.pop("subjects", {}) or {}
        dept = c.pop("departments", {}) or {}
        year = c.pop("years", {}) or {}
        sec = c.pop("sections", {}) or {}
        c["subject_name"] = subj.get("subject_name", "")
        c["department_name"] = dept.get("department_name", "")
        c["year_number"] = year.get("year_number", "")
        c["section_name"] = sec.get("section_name", "")
        c["name"] = subj.get("subject_name", "Class")
        result.append(c)
    return result


@router.get("/{faculty_id}/students")
async def get_faculty_students(faculty_id: str, current_user: dict = Depends(get_current_user)):
    # 1. Get all classes taught by this faculty
    classes_res = supabase_admin.table("classes") \
        .select("id, department_id, year_id, section_id") \
        .eq("faculty_id", faculty_id).execute()
    classes = classes_res.data or []

    if not classes:
        return []

    # 2. Get all class IDs for this faculty
    class_ids = [c["id"] for c in classes]

    # 3. Get all students who have attendance records in these classes
    #    (i.e., students enrolled in faculty's classes)
    att_res = supabase_admin.table("attendance") \
        .select("student_id, student_name, status") \
        .in_("class_id", class_ids).execute()
    att_records = att_res.data or []

    if not att_records:
        # Fallback: return all students with 0% attendance
        students_res = supabase_admin.table("students").select("*").execute()
        students = students_res.data or []
        for s in students:
            s["attendance_percentage"] = 0
            s["total_classes"] = 0
            s["present_count"] = 0
            s["absent_count"] = 0
        return students

    # 4. Group attendance by student and calculate percentage
    from collections import defaultdict
    student_att = defaultdict(lambda: {"present": 0, "absent": 0, "name": ""})
    for r in att_records:
        sid = r["student_id"]
        student_att[sid]["name"] = r.get("student_name", "")
        status = (r.get("status") or "").lower()
        if status == "present":
            student_att[sid]["present"] += 1
        else:
            student_att[sid]["absent"] += 1

    # 5. Fetch full student details for these students
    student_ids = list(student_att.keys())
    students_res = supabase_admin.table("students") \
        .select("*").in_("student_id", student_ids).execute()
    students = students_res.data or []

    # 6. Attach attendance stats to each student
    result = []
    for s in students:
        sid = s["student_id"]
        att = student_att.get(sid, {"present": 0, "absent": 0})
        total = att["present"] + att["absent"]
        percentage = round(att["present"] / total * 100, 1) if total > 0 else 0
        s["attendance_percentage"] = percentage
        s["present_count"] = att["present"]
        s["absent_count"] = att["absent"]
        s["total_classes"] = total
        result.append(s)

    return sorted(result, key=lambda x: x["attendance_percentage"])


@router.get("/{faculty_id}/attendance/stats")
async def faculty_attendance_stats(faculty_id: str, current_user: dict = Depends(get_current_user)):
    res = supabase_admin.table("attendance").select("status, date") \
        .eq("faculty_id", faculty_id).execute()
    records = res.data or []
    total = len(records)
    present = len([r for r in records if r.get("status") == "present"])
    return {
        "total": total,
        "present": present,
        "absent": total - present,
        "rate": round(present / total * 100, 1) if total > 0 else 0,
    }