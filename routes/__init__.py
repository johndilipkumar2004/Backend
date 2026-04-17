from .auth import router as auth_router
from .students import router as students_router
from .faculty import router as faculty_router
from .attendance import router as attendance_router
from .recognition import router as recognition_router
from .camera import router as camera_router
from .analytics import router as analytics_router
from .dashboard import router as dashboard_router
from .departments import router as departments_router
from .session import router as session_router
from .admin import router as admin_router
from .messages import router as messages_router  # ← NEW

__all__ = [
    "auth_router", "students_router", "faculty_router",
    "attendance_router", "recognition_router", "camera_router",
    "analytics_router", "dashboard_router", "departments_router",
    "session_router", "admin_router", "messages_router",  # ← NEW
]