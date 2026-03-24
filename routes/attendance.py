from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from database import supabase_admin
from utils.security import get_current_user, require_faculty

router = APIRouter(prefix="/attendance", tags=["Attendance"])


class MarkAttendanceRequest(BaseModel):
    student_id: str
    student_name: str
    class_id: str
    subject_id: str
    faculty_id: str
    status: str = "present"
    period: Optional[int] = 1
    confidence_score: Optional[int] = None
    date: Optional[str] = None


class BulkMarkRequest(BaseModel):
    class_id: str
    subject_id: str
    faculty_id: str
    records: list[dict]
    date: Optional[str] = None


@router.post("/mark")
async def mark_attendance(
    req: MarkAttendanceRequest,
    current_user: dict = Depends(require_faculty),
):
    today = req.date or str(date.today())
    now_time = datetime.now().strftime("%H:%M:%S")

    # Check duplicate
    existing = supabase_admin.table("attendance").select("id") \
        .eq("student_id", req.student_id) \
        .eq("class_id", req.class_id) \
        .eq("date", today) \
        .eq("period", req.period or 1).execute()

    if existing.data:
        res = supabase_admin.table("attendance").update({
            "status": req.status,
        }).eq("id", existing.data[0]["id"]).execute()
        return {"message": "Attendance updated", "record": res.data[0] if res.data else {}}

    res = supabase_admin.table("attendance").insert({
        "student_id": req.student_id,
        "student_name": req.student_name,
        "class_id": req.class_id,
        "subject_id": req.subject_id,
        "faculty_id": req.faculty_id,
        "date": today,
        "time": now_time,
        "period": req.period or 1,
        "status": req.status,
    }).execute()

    return {"message": "Attendance marked", "record": res.data[0] if res.data else {}}


@router.post("/mark/bulk")
async def mark_bulk(req: BulkMarkRequest, current_user: dict = Depends(require_faculty)):
    today = req.date or str(date.today())
    now_time = datetime.now().strftime("%H:%M:%S")
    results = []

    for record in req.records:
        student_id = record.get("student_id")
        student_name = record.get("student_name", "")
        status = record.get("status", "present")

        existing = supabase_admin.table("attendance").select("id") \
            .eq("student_id", student_id).eq("class_id", req.class_id) \
            .eq("date", today).execute()

        if existing.data:
            supabase_admin.table("attendance").update({"status": status}) \
                .eq("id", existing.data[0]["id"]).execute()
        else:
            supabase_admin.table("attendance").insert({
                "student_id": student_id,
                "student_name": student_name,
                "class_id": req.class_id,
                "subject_id": req.subject_id,
                "faculty_id": req.faculty_id,
                "date": today,
                "time": now_time,
                "period": 1,
                "status": status,
            }).execute()
        results.append({"student_id": student_id, "status": status})

    return {"message": f"{len(results)} records saved", "results": results}


@router.get("/class/{class_id}")
async def get_class_attendance(
    class_id: str,
    attendance_date: Optional[str] = Query(None, alias="date"),
    current_user: dict = Depends(require_faculty),
):
    query = supabase_admin.table("attendance") \
        .select("*, subjects(subject_name), faculty(faculty_name)") \
        .eq("class_id", class_id)

    if attendance_date:
        query = query.eq("date", attendance_date)

    res = query.order("date", desc=True).execute()
    records = res.data or []
    present = [r for r in records if r.get("status") == "present"]
    absent = [r for r in records if r.get("status") == "absent"]

    return {
        "class_id": class_id,
        "date": attendance_date or "all",
        "total": len(records),
        "present_count": len(present),
        "absent_count": len(absent),
        "records": records,
    }


@router.get("/stats")
async def get_attendance_stats(current_user: dict = Depends(get_current_user)):
    res = supabase_admin.table("attendance").select("status, date").execute()
    records = res.data or []
    total = len(records)
    present = len([r for r in records if r.get("status") == "present"])
    rate = round(present / total * 100, 1) if total > 0 else 0

    from collections import defaultdict
    by_date = defaultdict(lambda: {"present": 0, "absent": 0})
    for r in records:
        by_date[r["date"]][r["status"]] += 1

    trend = [
        {
            "date": d,
            "present": v["present"],
            "absent": v["absent"],
            "percentage": round(v["present"] / (v["present"] + v["absent"]) * 100, 1)
            if (v["present"] + v["absent"]) > 0 else 0,
        }
        for d, v in sorted(by_date.items(), reverse=True)[:30]
    ]

    return {
        "total_records": total,
        "present": present,
        "absent": total - present,
        "attendance_rate": rate,
        "daily_trend": trend,
    }


@router.get("/today")
async def get_today(
    class_id: Optional[str] = Query(None),
    current_user: dict = Depends(require_faculty),
):
    today = str(date.today())
    query = supabase_admin.table("attendance").select("*").eq("date", today)
    if class_id:
        query = query.eq("class_id", class_id)
    res = query.execute()
    records = res.data or []
    return {
        "date": today,
        "total": len(records),
        "present": len([r for r in records if r.get("status") == "present"]),
        "records": records,
    }
