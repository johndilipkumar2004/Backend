from fastapi import APIRouter, Depends, Query
from typing import Optional
from database import supabase_admin
from utils.security import get_current_user
from collections import defaultdict
from datetime import date, timedelta
import calendar

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/weekly")
async def weekly_trend(
    faculty_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    today = date.today()
    days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    query = supabase_admin.table("attendance").select("status, date") \
        .gte("date", str(days[0]))
    if faculty_id:
        query = query.eq("faculty_id", faculty_id)
    res = query.execute()
    records = res.data or []

    by_day = defaultdict(lambda: {"present": 0, "total": 0})
    for r in records:
        by_day[r["date"]]["total"] += 1
        if r.get("status") == "present":
            by_day[r["date"]]["present"] += 1

    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    return [
        {
            "day": day_names[d.weekday()],
            "date": str(d),
            "present": by_day[str(d)]["present"],
            "total": by_day[str(d)]["total"],
            "percentage": round(by_day[str(d)]["present"] / by_day[str(d)]["total"] * 100, 1)
            if by_day[str(d)]["total"] > 0 else 0,
        }
        for d in days
    ]


@router.get("/monthly")
async def monthly_trend(current_user: dict = Depends(get_current_user)):
    res = supabase_admin.table("attendance").select("status, date").execute()
    records = res.data or []

    by_month = defaultdict(lambda: {"present": 0, "total": 0})
    for r in records:
        month = r["date"][:7]
        by_month[month]["total"] += 1
        if r.get("status") == "present":
            by_month[month]["present"] += 1

    months = sorted(by_month.keys(), reverse=True)[:6]
    result = []
    for m in reversed(months):
        year, mon = map(int, m.split("-"))
        data = by_month[m]
        result.append({
            "month": calendar.month_abbr[mon],
            "year": year,
            "present": data["present"],
            "total": data["total"],
            "percentage": round(data["present"] / data["total"] * 100, 1) if data["total"] > 0 else 0,
        })
    return result


@router.get("/departments")
async def department_stats(current_user: dict = Depends(get_current_user)):
    students_res = supabase_admin.table("students").select("student_id, department").execute()
    students = students_res.data or []
    student_dept = {s["student_id"]: s.get("department", "Unknown") for s in students}

    att_res = supabase_admin.table("attendance").select("student_id, status").execute()
    records = att_res.data or []

    by_dept = defaultdict(lambda: {"present": 0, "total": 0})
    for r in records:
        dept = student_dept.get(r["student_id"], "Unknown")
        by_dept[dept]["total"] += 1
        if r.get("status") == "present":
            by_dept[dept]["present"] += 1

    return sorted([
        {
            "department": dept,
            "present": data["present"],
            "total": data["total"],
            "percentage": round(data["present"] / data["total"] * 100, 1) if data["total"] > 0 else 0,
        }
        for dept, data in by_dept.items()
    ], key=lambda x: x["percentage"], reverse=True)


@router.get("/performance")
async def performance_summary(current_user: dict = Depends(get_current_user)):
    students_res = supabase_admin.table("students").select("student_id").execute()
    students = students_res.data or []
    excellent = good = needs_attention = 0

    for student in students:
        sid = student["student_id"]
        att = supabase_admin.table("attendance").select("status").eq("student_id", sid).execute()
        records = att.data or []
        if not records:
            continue
        pct = len([r for r in records if r.get("status") == "present"]) / len(records) * 100
        if pct >= 90:
            excellent += 1
        elif pct >= 75:
            good += 1
        else:
            needs_attention += 1

    return {
        "excellent": excellent,
        "good": good,
        "needs_attention": needs_attention,
        "total": excellent + good + needs_attention,
    }
