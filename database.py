from supabase import create_client, Client
from dotenv import load_dotenv
import os
from datetime import date, datetime

load_dotenv()

# ── Direct credentials (fallback if .env not found) ───────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://fosiooudtagavnsgpvhj.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZvc2lvb3VkdGFnYXZuc2dwdmhqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI4NjcwNzEsImV4cCI6MjA4ODQ0MzA3MX0.2UihNi6oyrxjcx1XGsB7HJcYnonbCTT6FKoOsxbPQK0")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZvc2lvb3VkdGFnYXZuc2dwdmhqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Mjg2NzA3MSwiZXhwIjoyMDg4NDQzMDcxfQ.wORJJef2Pq1D8PuI_-TmyWbVtELTMgt-ver-29McNxU")

# Use service key to bypass RLS
db: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def get_all_students() -> list:
    res = db.table("students").select("*").order("student_name").execute()
    return res.data or []


def get_all_faculty() -> list:
    res = db.table("faculty").select("*, departments(department_name), roles(role_name)").execute()
    return res.data or []


def get_all_classes() -> list:
    res = db.table("classes").select("*, subjects(subject_name)").execute()
    return res.data or []


def get_all_departments() -> list:
    res = db.table("departments").select("*").execute()
    return res.data or []


def get_all_roles() -> list:
    res = db.table("roles").select("*").execute()
    return res.data or []


def get_all_subjects() -> list:
    res = db.table("subjects").select("*, departments(department_name)").execute()
    return res.data or []


def mark_attendance(student_id: str, student_name: str, class_id: str,
                    subject_id: str, faculty_id: str,
                    status: str = "present") -> dict:
    today = str(date.today())
    now_time = datetime.now().strftime("%H:%M:%S")

    existing = db.table("attendance").select("id") \
        .eq("student_id", student_id).eq("class_id", class_id).eq("date", today).execute()

    if existing.data:
        res = db.table("attendance").update({"status": status}) \
            .eq("id", existing.data[0]["id"]).execute()
    else:
        res = db.table("attendance").insert({
            "student_id": student_id,
            "student_name": student_name,
            "class_id": class_id,
            "subject_id": subject_id,
            "faculty_id": faculty_id,
            "date": today,
            "time": now_time,
            "period": 1,
            "status": status,
        }).execute()
    return res.data[0] if res.data else {}


def get_student_attendance(student_id: str) -> dict:
    res = db.table("attendance").select("status").eq("student_id", student_id).execute()
    records = res.data or []
    total = len(records)
    present = len([r for r in records if r.get("status") == "present"])
    return {
        "total": total,
        "present": present,
        "absent": total - present,
        "percentage": round(present / total * 100, 1) if total > 0 else 0,
    }


if __name__ == "__main__":
    print("\n📊 Smart Attendance AI — Database Test")
    print("=" * 45)

    students = get_all_students()
    print(f"✅ Students in DB   : {len(students)}")
    if students:
        for s in students[:3]:
            print(f"   → {s.get('student_name')} ({s.get('student_id')})")

    faculty = get_all_faculty()
    print(f"\n✅ Faculty in DB    : {len(faculty)}")
    if faculty:
        for f in faculty:
            role = (f.get("roles") or {}).get("role_name", "faculty")
            dept = (f.get("departments") or {}).get("department_name", "")
            print(f"   → {f.get('faculty_name')} | {dept} | {role}")

    classes = get_all_classes()
    print(f"\n✅ Classes in DB    : {len(classes)}")

    departments = get_all_departments()
    print(f"✅ Departments in DB: {len(departments)}")
    for d in departments:
        print(f"   → {d.get('department_name')}")

    subjects = get_all_subjects()
    print(f"✅ Subjects in DB   : {len(subjects)}")

    print("\n✅ Database connection successful!")
    print("=" * 45)
