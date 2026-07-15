"""Patient router."""
from fastapi import APIRouter, Depends, Query, Header, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
import uuid

from backend.app.core.db import get_db
from backend.app.dependencies import get_current_user, get_idempotency_key, check_patient_access
from backend.app.schemas.patient import PatientCreate, PatientUpdate
from backend.app.services import patient_service, idempotency_service

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", status_code=201)
def create_patient(
    payload: PatientCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Depends(get_idempotency_key),
):
    if idempotency_key:
        cached = idempotency_service.check_key_exists(idempotency_key, str(current_user.id))
        if cached:
            return cached

    result = patient_service.create_patient(db, payload, current_user.id)

    if idempotency_key:
        idempotency_service.store_result(idempotency_key, str(current_user.id), result)

    return result


@router.get("")
def list_patients(
    q: Optional[str] = None,
    doctor_id: Optional[uuid.UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return patient_service.list_patients(
        db, current_user,
        q=q, doctor_id=doctor_id, date_from=date_from, date_to=date_to,
        status=status, page=page, page_size=page_size,
    )


@router.get("/search")
def search_by_mobile(
    mobile: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from backend.app.repositories import patient_repo
    patients = patient_repo.search_by_mobile(db, mobile)
    return [patient_service._patient_to_dict(db, p) for p in patients]


@router.get("/{patient_id}")
def get_patient(patient_id: uuid.UUID, current_user=Depends(get_current_user),
                db: Session = Depends(get_db)):
    from backend.app.repositories import patient_repo
    patient = patient_repo.get_by_id(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    check_patient_access(current_user, patient)
    return patient_service.get_patient(db, patient_id)


@router.patch("/{patient_id}")
def update_patient(
    patient_id: uuid.UUID,
    payload: PatientUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Depends(get_idempotency_key),
):
    from backend.app.repositories import patient_repo
    patient = patient_repo.get_by_id(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    check_patient_access(current_user, patient)
    return patient_service.update_patient(db, patient_id, payload, current_user.id)


@router.post("/{patient_id}/qr-code")
def get_qr_code(patient_id: uuid.UUID, current_user=Depends(get_current_user),
                db: Session = Depends(get_db)):
    from backend.app.repositories import patient_repo
    patient = patient_repo.get_by_id(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    check_patient_access(current_user, patient)
    upi_string = patient_service.generate_qr_payload(db, patient_id)
    return {"upi_string": upi_string}
