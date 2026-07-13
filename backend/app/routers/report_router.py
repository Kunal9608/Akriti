"""Report router."""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import uuid
import os

from backend.app.core.db import get_db
from backend.app.dependencies import get_current_user
from backend.app.services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/{patient_id}", status_code=201)
async def upload_report(
    patient_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    filename_lower = file.filename.lower()
    
    # All accepted extensions — images + PDF
    image_exts = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif", ".heic", ".heif")
    allowed_extensions = (".pdf",) + image_exts
    
    if not any(filename_lower.endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=422,
            detail="Only PDF or image files (JPG, PNG, WEBP, BMP, TIFF, HEIC) are accepted"
        )

    # Enforce file size limit of 10MB
    max_size = 10 * 1024 * 1024  # 10MB
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > max_size:
        raise HTTPException(
            status_code=413,
            detail="File size exceeds the maximum limit of 10MB"
        )

    file_bytes = await file.read()

    # Convert any image format to PDF
    if any(filename_lower.endswith(ext) for ext in image_exts):
        from PIL import Image
        import io
        try:
            image = Image.open(io.BytesIO(file_bytes))
            # Handle animated GIF/WEBP — take first frame
            try:
                image.seek(0)
            except (EOFError, AttributeError):
                pass
            # Convert to RGB for PDF compatibility
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")
            pdf_io = io.BytesIO()
            image.save(pdf_io, format="PDF")
            file_bytes = pdf_io.getvalue()
            base_name = os.path.splitext(file.filename)[0]
            file.filename = f"{base_name}.pdf"
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to convert image to PDF: {str(e)}"
            )

    return report_service.upload_report(
        db, patient_id, file_bytes, file.filename, current_user.id, background_tasks
    )


@router.get("/{patient_id}")
def list_reports(patient_id: uuid.UUID, current_user=Depends(get_current_user),
                 db: Session = Depends(get_db)):
    return report_service.get_patient_reports(db, patient_id)


@router.get("/download/{report_id}")
def download_report(report_id: uuid.UUID, current_user=Depends(get_current_user),
                    db: Session = Depends(get_db)):
    from backend.app.models.report import Report
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report file not found on disk")
    
    # Use Content-Disposition inline to prevent automatic download
    headers = {
        "Content-Disposition": f"inline; filename=\"{report.original_filename or 'report.pdf'}\""
    }
    return FileResponse(report.file_path, media_type="application/pdf", headers=headers)


@router.get("/verify/{report_id}")
def verify_report(report_id: uuid.UUID, h: str = None, db: Session = Depends(get_db)):
    """Public verification endpoint — no auth required."""
    return report_service.verify_report(db, report_id, h)
