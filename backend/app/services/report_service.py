"""Report service — upload, digital signature, verification hash."""
import hashlib
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from backend.app.models.report import Report
from backend.app.models.patient import PatientStatusEnum
from backend.app.repositories import patient_repo
from backend.app.services import audit_service, notification_service

REPORTS_DIR = Path("uploads/reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def upload_report(db: Session, patient_id: uuid.UUID, file_bytes: bytes,
                  filename: str, uploader_id: uuid.UUID, background_tasks,
                  reason: Optional[str] = None, force: bool = False) -> dict:
    """FR-7.1 — Upload report PDF, compute hash, update patient status."""
    patient = patient_repo.get_by_id(db, patient_id)
    if not patient:
        raise ValueError("Patient not found")

    # Compute verification hash (SHA-256 of file content)
    verification_hash = hashlib.sha256(file_bytes).hexdigest()

    # Check for identical duplicate file content
    if not force:
        existing = db.query(Report).options(joinedload(Report.uploader)).filter(
            Report.patient_id == patient_id,
            Report.verification_hash == verification_hash
        ).first()
        if existing:
            uploader_name = existing.uploader.name if existing.uploader else "Unknown"
            raise ValueError(f"DUPLICATE_REPORT:An identical report was already uploaded as Version {existing.version} by {uploader_name}.")

    # Mark previous reports as not latest
    db.query(Report).filter(Report.patient_id == patient_id).update({"is_latest": False})

    # Get version number
    version = db.query(Report).filter(Report.patient_id == patient_id).count() + 1

    # Store file outside web root using a randomized unique filename format
    import re
    orig_base, orig_ext = os.path.splitext(filename)
    sanitized_base = re.sub(r'[^a-zA-Z0-9_-]', '_', orig_base)
    safe_filename = f"{patient.patient_code}_v{version}_{uuid.uuid4().hex}_{sanitized_base}{orig_ext}"
    
    file_path = REPORTS_DIR / safe_filename
    file_path.write_bytes(file_bytes)
    try:
        os.chmod(file_path, 0o644) # Read/write for owner, read-only for others (non-executable)
    except Exception:
        pass

    report = Report(
        patient_id=patient_id,
        file_path=str(file_path),
        original_filename=filename,
        signed=False,
        verification_hash=verification_hash,
        version=version,
        uploaded_by=uploader_id,
        is_latest=True,
    )
    db.add(report)
    db.flush()

    # Update patient status
    patient_repo.update_patient(db, patient_id, status=PatientStatusEnum.report_ready)

    # Log report upload in patient status history
    from backend.app.models.patient_status_history import PatientStatusHistory
    history = PatientStatusHistory(
        patient_id=patient_id,
        status="report_ready",
        updated_by=uploader_id,
        extra_info={"version": version, "filename": filename, "reason": reason}
    )
    db.add(history)

    audit_service.log(db, "report.upload", actor_user_id=uploader_id,
                      entity_type="report", entity_id=report.id,
                      after={"patient_code": patient.patient_code, "version": version})
    db.commit()

    # Notify using BackgroundTasks (fire-and-forget) — attach the PDF
    from backend.app.config import settings
    recipient = settings.MAIL_FROM or settings.MAIL_USERNAME or "lab@akriti.com"
    attachment_name = f"report_{patient.patient_code}.pdf"
    background_tasks.add_task(
        notification_service.notify,
        "report_ready",
        recipient,
        {
            "patient_name": patient.name,
            "patient_code": patient.patient_code,
            "attachment_bytes": file_bytes,
            "attachment_name": attachment_name,
        }
    )

    return {
        "id": str(report.id),
        "patient_code": patient.patient_code,
        "version": version,
        "verification_hash": verification_hash,
        "uploaded_at": report.uploaded_at.isoformat(),
    }


def get_patient_reports(db: Session, patient_id: uuid.UUID) -> list:
    reports = (
        db.query(Report)
        .options(joinedload(Report.uploader))
        .filter(Report.patient_id == patient_id)
        .order_by(Report.version.desc())
        .all()
    )
    return [
        {
            "id": str(r.id),
            "version": r.version,
            "filename": r.original_filename,
            "signed": r.signed,
            "verification_hash": r.verification_hash,
            "is_latest": r.is_latest,
            "uploaded_at": r.uploaded_at.isoformat() if r.uploaded_at else None,
            "uploaded_by_name": r.uploader.name if r.uploader else "Unknown",
        }
        for r in reports
    ]


def verify_report(db: Session, report_id: uuid.UUID, short_hash: Optional[str] = None) -> dict:
    """Public verification endpoint — FR-7.1."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        return {"verified": False, "message": "Report not found"}

    if short_hash and not report.verification_hash.startswith(short_hash):
        return {"verified": False, "message": "Hash mismatch — document may have been altered"}

    patient = patient_repo.get_by_id(db, report.patient_id)
    return {
        "verified": True,
        "patient_code": patient.patient_code if patient else "Unknown",
        "issued_on": report.uploaded_at.strftime("%d %B %Y") if report.uploaded_at else "Unknown",
        "message": "Verified authentic — issued by Akriti Diagnostics Center",
    }
