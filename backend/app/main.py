"""
FastAPI application — wires all routers, middleware, static file serving.
This file does NOT contain business logic — only app assembly.
"""
import os
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded
from backend.app.core.limiter import limiter

from backend.app.config import settings
from backend.app.dependencies import require_admin
from backend.app.middleware.error_handler import (
    validation_exception_handler,
    value_error_handler,
    permission_error_handler,
    generic_exception_handler,
)
from backend.app.routers import (
    auth_router, staff_router, attendance_router,
    patient_router, test_router, report_router,
    finance_router, security_router,
)
from backend.app.core.db import init_db

ROOT = Path(__file__).parent.parent.parent  # project root
FRONTEND_DIR = ROOT / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialize DB tables if they don't exist (fallback for no Alembic)."""
    try:
        init_db()
    except Exception as e:
        print(f"  [WARN] DB init: {e}")
    yield


app = FastAPI(
    title="Akriti Diagnostics Center — Lab Management System",
    description="Pathology lab management API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please try again later.", "message": "Rate limit exceeded"}
    )

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Web Security Headers Middleware ──────────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # 1. Content Security Policy (CSP)
    # Allows self, Google Fonts, flatpickr, ChartJS, cloudflare QRcode.js, and Google reCAPTCHA
    csp_directives = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://www.google.com/recaptcha/ https://www.gstatic.com/recaptcha/; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: blob:; "
        "connect-src 'self' https://www.google.com/recaptcha/; "
        "frame-src 'self' https://www.google.com/recaptcha/ https://recaptcha.google.com/recaptcha/; "
        "frame-ancestors 'none';"
    )
    response.headers["Content-Security-Policy"] = csp_directives
    
    # 2. Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # 3. Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # 4. Cross-Site Scripting protection
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # 5. Referrer Policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # 6. HTTP Strict Transport Security (HSTS) - only in production
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
    return response


# ── Exception handlers ────────────────────────────────────────────────────────
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValueError, value_error_handler)
app.add_exception_handler(PermissionError, permission_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# ── API routers ───────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"
app.include_router(auth_router.router, prefix=API_PREFIX)
app.include_router(staff_router.router, prefix=API_PREFIX)
app.include_router(attendance_router.router, prefix=API_PREFIX)
app.include_router(patient_router.router, prefix=API_PREFIX)
app.include_router(test_router.router, prefix=API_PREFIX)
app.include_router(report_router.router, prefix=API_PREFIX)
app.include_router(finance_router.router, prefix=API_PREFIX)
app.include_router(security_router.router, prefix=API_PREFIX)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "service": "Akriti Lab Management System"}


# ── Settings API (lab config) ─────────────────────────────────────────────────
# In-memory overlay for lab settings (persists for process lifetime)
_lab_settings_overlay: dict = {}


@app.get("/api/v1/settings/lab")
def get_lab_settings():
    from backend.app.services import notification_service
    return {
        "lab_name":     _lab_settings_overlay.get("lab_name",     settings.LAB_NAME),
        "lab_upi_vpa":  _lab_settings_overlay.get("lab_upi_vpa",  settings.LAB_UPI_VPA),
        "lab_phone":    _lab_settings_overlay.get("lab_phone",    settings.LAB_PHONE),
        "lab_address":  _lab_settings_overlay.get("lab_address",  settings.LAB_ADDRESS),
        "lab_gstin":    _lab_settings_overlay.get("lab_gstin",    settings.LAB_GSTIN),
        "report_footer": _lab_settings_overlay.get("report_footer", ""),
        "email_notifications_enabled": notification_service.EMAIL_NOTIFICATIONS_ENABLED,
        "recaptcha_site_key": settings.RECAPTCHA_SITE_KEY,
        "recaptcha_enabled": settings.ENABLE_RECAPTCHA,
    }


from pydantic import BaseModel as PydanticBaseModel


class LabSettingsPatchSchema(PydanticBaseModel):
    lab_name: Optional[str] = None
    lab_address: Optional[str] = None
    lab_phone: Optional[str] = None
    lab_upi_vpa: Optional[str] = None
    lab_gstin: Optional[str] = None
    report_footer: Optional[str] = None
    email_notifications_enabled: Optional[bool] = None


@app.patch("/api/v1/settings/lab")
def patch_lab_settings(
    payload: LabSettingsPatchSchema,
    current_user=Depends(require_admin),
):
    global _lab_settings_overlay
    update = payload.model_dump(exclude_none=True)
    if "email_notifications_enabled" in update:
        from backend.app.services import notification_service
        notification_service.EMAIL_NOTIFICATIONS_ENABLED = update["email_notifications_enabled"]
    _lab_settings_overlay.update(update)
    return get_lab_settings()


class DeleteEverythingSchema(PydanticBaseModel):
    safety_password: str


@app.post("/api/v1/settings/delete-everything")
def delete_everything(
    payload: DeleteEverythingSchema,
    current_user=Depends(require_admin),
):
    if payload.safety_password != "Kunal123":
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Incorrect safety password")

    # Clean report files from disk
    import glob
    for f in glob.glob("uploads/reports/*"):
        try:
            os.remove(f)
        except Exception:
            pass

    from backend.app.core.db import SessionLocal
    # Hard delete all data from tables except users
    from backend.app.models.patient import Patient
    from backend.app.models.patient_test import PatientTest
    from backend.app.models.report import Report
    from backend.app.models.login_history import LoginHistory
    from backend.app.models.active_session import ActiveSession
    from backend.app.models.audit_log import AuditLog
    from backend.app.models.expense import Expense
    from backend.app.models.attendance_event import AttendanceEvent

    db = SessionLocal()
    try:
        db.query(Report).delete()
        db.query(PatientTest).delete()
        db.query(Patient).delete()
        db.query(ActiveSession).delete()
        db.query(LoginHistory).delete()
        db.query(AuditLog).delete()
        db.query(Expense).delete()
        db.query(AttendanceEvent).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Database wipe failed: {e}")
    finally:
        db.close()

    return {"message": "All database records have been deleted successfully"}


# ── Static frontend (served at /) ─────────────────────────────────────────────
if FRONTEND_DIR.exists():
    # Serve specific subdirectories
    for sub in ["assets", "admin", "staff"]:
        sub_dir = FRONTEND_DIR / sub
        if sub_dir.exists():
            app.mount(f"/{sub}", StaticFiles(directory=str(sub_dir)), name=sub)

    # Serve root-level HTML pages and service worker
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {"message": "Frontend not built yet. API is running at /api/v1/"}
