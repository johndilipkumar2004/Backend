from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

from routes import (
    auth_router, students_router, faculty_router,
    attendance_router, recognition_router, camera_router,
    analytics_router, dashboard_router, departments_router,
    session_router, admin_router, messages_router,  # ← ADDED messages_router
)

app = FastAPI(
    title="Smart Attendance AI",
    description="AI-powered university attendance management — John Dilip Kumar Vallamreddi",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(students_router)
app.include_router(faculty_router)
app.include_router(attendance_router)
app.include_router(recognition_router)
app.include_router(camera_router)
app.include_router(analytics_router)
app.include_router(dashboard_router)
app.include_router(departments_router)
app.include_router(session_router)
app.include_router(messages_router)  # ← ADDED


@app.get("/", tags=["Health"])
async def root():
    return {
        "app": "Smart Attendance AI",
        "version": "1.0.0",
        "status": "running ✅",
        "developer": "John Dilip Kumar Vallamreddi",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    from database import supabase_admin
    from services.face_recognition_service import face_service
    try:
        supabase_admin.table("students").select("student_id", count="exact").execute()
        db_status = "connected ✅"
    except Exception as e:
        db_status = f"error: {str(e)}"
    return {
        "status": "healthy",
        "database": db_status,
        "face_recognition": face_service.get_stats(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")