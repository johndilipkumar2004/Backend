from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from database import supabase_admin
from utils.security import verify_password, hash_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    identifier: str
    password: str
    role: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/login")
async def login(req: LoginRequest):
    if req.role not in ("admin", "faculty", "student"):
        raise HTTPException(status_code=400, detail="Invalid role")

    if req.role == "admin":
        res = supabase_admin.table("admin").select("*").eq("email", req.identifier).execute()
        if not res.data:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        user = res.data[0]
        stored_pw = user.get("password_hash", "")
        try:
            valid = verify_password(req.password, stored_pw)
        except Exception:
            valid = req.password == stored_pw
        if not valid:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_access_token({
            "sub": str(user["id"]), "role": "admin",
            "name": user.get("admin_name"), "email": user.get("email"),
        })
        return {
            "access_token": token, "token_type": "bearer",
            "user": {"id": str(user["id"]), "role": "admin",
                     "name": user.get("admin_name"), "email": user.get("email")}
        }

    elif req.role == "faculty":
        res = supabase_admin.table("faculty") \
            .select("*, departments(department_name)").eq("email", req.identifier).execute()
        if not res.data:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        user = res.data[0]
        stored_pw = user.get("password_hash", "")
        try:
            valid = verify_password(req.password, stored_pw)
        except Exception:
            valid = req.password == stored_pw
        if not valid:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        dept = user.get("departments") or {}
        token = create_access_token({
            "sub": str(user["id"]), "role": "faculty",
            "name": user.get("faculty_name"), "email": user.get("email"),
            "department": dept.get("department_name"),
        })
        return {
            "access_token": token, "token_type": "bearer",
            "user": {"id": str(user["id"]), "role": "faculty",
                     "name": user.get("faculty_name"), "email": user.get("email"),
                     "department": dept.get("department_name")}
        }

    else:
        res = supabase_admin.table("students").select("*").eq("student_id", req.identifier).execute()
        if not res.data:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        user = res.data[0]
        stored_pw = user.get("password_hash", "")
        try:
            valid = verify_password(req.password, stored_pw)
        except Exception:
            valid = req.password == stored_pw
        if not valid:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_access_token({
            "sub": str(user["student_id"]), "role": "student",
            "name": user.get("student_name"), "email": user.get("email"),
            "student_id": user.get("student_id"),
        })
        return {
            "access_token": token, "token_type": "bearer",
            "user": {"id": user.get("student_id"), "role": "student",
                     "name": user.get("student_name"), "email": user.get("email"),
                     "rollNumber": user.get("student_id"),
                     "department": user.get("department"),
                     "year": str(user.get("year", "")),
                     "section": user.get("section"),
                     "parent_email": user.get("parent_email")}
        }


@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    role = current_user.get("role")
    sub = current_user.get("sub")

    if role == "admin":
        res = supabase_admin.table("admin").select("*").eq("id", sub).single().execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Not found")
        u = res.data
        return {"id": str(u["id"]), "role": "admin",
                "name": u.get("admin_name"), "email": u.get("email")}

    elif role == "faculty":
        res = supabase_admin.table("faculty") \
            .select("*, departments(department_name)").eq("id", sub).single().execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Not found")
        u = res.data
        dept = u.get("departments") or {}
        return {"id": str(u["id"]), "role": "faculty",
                "name": u.get("faculty_name"), "email": u.get("email"),
                "department": dept.get("department_name")}
    else:
        res = supabase_admin.table("students").select("*").eq("student_id", sub).single().execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Not found")
        u = res.data
        return {"id": u.get("student_id"), "role": "student",
                "name": u.get("student_name"), "email": u.get("email"),
                "rollNumber": u.get("student_id"), "department": u.get("department"),
                "year": str(u.get("year", "")), "parent_email": u.get("parent_email")}


@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user)
):
    role = current_user.get("role")
    sub = current_user.get("sub")

    if role == "admin":
        res = supabase_admin.table("admin").select("password_hash").eq("id", sub).single().execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Not found")
        stored_pw = res.data.get("password_hash", "")
        try:
            valid = verify_password(req.current_password, stored_pw)
        except Exception:
            valid = req.current_password == stored_pw
        if not valid:
            raise HTTPException(status_code=400, detail="Current password incorrect")
        new_hash = hash_password(req.new_password)
        supabase_admin.table("admin").update({"password_hash": new_hash}).eq("id", sub).execute()

    elif role == "faculty":
        res = supabase_admin.table("faculty").select("password_hash").eq("id", sub).single().execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Not found")
        stored_pw = res.data.get("password_hash", "")
        try:
            valid = verify_password(req.current_password, stored_pw)
        except Exception:
            valid = req.current_password == stored_pw
        if not valid:
            raise HTTPException(status_code=400, detail="Current password incorrect")
        new_hash = hash_password(req.new_password)
        supabase_admin.table("faculty").update({"password_hash": new_hash}).eq("id", sub).execute()

    else:
        res = supabase_admin.table("students").select("password_hash").eq("student_id", sub).single().execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Not found")
        stored_pw = res.data.get("password_hash", "")
        try:
            valid = verify_password(req.current_password, stored_pw)
        except Exception:
            valid = req.current_password == stored_pw
        if not valid:
            raise HTTPException(status_code=400, detail="Current password incorrect")
        new_hash = hash_password(req.new_password)
        supabase_admin.table("students").update({"password_hash": new_hash}).eq("student_id", sub).execute()

    return {"message": "Password updated successfully"}
