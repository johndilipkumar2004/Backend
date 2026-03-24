from fastapi import APIRouter, Depends
from database import supabase_admin
from utils.security import get_current_user

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("")
async def get_departments(current_user: dict = Depends(get_current_user)):
    res = supabase_admin.table("departments").select("*").execute()
    return res.data or []


@router.get("/{dept_id}/students")
async def get_department_students(dept_id: str, current_user: dict = Depends(get_current_user)):
    res = supabase_admin.table("students").select("*").eq("department_id", dept_id).execute()
    return res.data or []


@router.get("/subjects")
async def get_subjects(current_user: dict = Depends(get_current_user)):
    res = supabase_admin.table("subjects") \
        .select("*, departments(department_name), years(year_number)").execute()
    return res.data or []


@router.get("/years")
async def get_years(current_user: dict = Depends(get_current_user)):
    res = supabase_admin.table("years").select("*").execute()
    return res.data or []


@router.get("/sections")
async def get_sections(current_user: dict = Depends(get_current_user)):
    res = supabase_admin.table("sections").select("*").execute()
    return res.data or []
