"""Patient service — Patient ID generation, create/update, payment logic."""
from datetime import date, datetime, timezone, timedelta
from typing import Optional, List
import uuid

from sqlalchemy.orm import Session

from backend.app.repositories import patient_repo, test_repo
from backend.app.services import audit_service
from backend.app.schemas.patient import PatientCreate, PatientUpdate


def create_patient(db: Session, payload: PatientCreate, current_user_id: uuid.UUID,
                   idempotency_key: Optional[str] = None) -> dict:
    """FR-4.1, FR-4.2 — Create patient with sequence-based ID generation."""
    year = date.today().year

    # Generate Patient ID using PostgreSQL sequence (never MAX+1)
    patient_code = patient_repo.generate_patient_code(db, year)

    # Server-recompute total from current test prices — never trust client total
    price_map = test_repo.get_current_prices(db, payload.test_ids)
    if len(price_map) != len(payload.test_ids):
        missing = [str(tid) for tid in payload.test_ids if str(tid) not in price_map]
        raise ValueError(f"Tests not found: {missing}")

    # Check same-day same-test duplicates for the patient (by contact number)
    sample_date = payload.sample_date or date.today()
    from backend.app.models.patient import Patient
    from backend.app.models.patient_test import PatientTest
    from backend.app.models.test import Test
    
    existing_patients = db.query(Patient).filter(
        Patient.mobile == payload.mobile,
        Patient.sample_date == sample_date,
        Patient.deleted_at.is_(None)
    ).all()
    if existing_patients:
        existing_patient_ids = [p.id for p in existing_patients]
        duplicates = db.query(PatientTest).filter(
            PatientTest.patient_id.in_(existing_patient_ids),
            PatientTest.test_id.in_(payload.test_ids)
        ).all()
        if duplicates:
            dup_test_ids = [d.test_id for d in duplicates]
            dup_tests = db.query(Test).filter(Test.id.in_(dup_test_ids)).all()
            dup_names = ", ".join([t.name for t in dup_tests])
            raise ValueError(f"Patient with mobile {payload.mobile} has already booked test(s) ({dup_names}) on this day")

    total_amount = sum(price_map.values())
    amount_paid = float(payload.amount_paid or 0)
    discount_amount = float(payload.discount_amount or 0)

    if discount_amount < 0:
        raise ValueError("Discount amount cannot be negative")
    if discount_amount > total_amount:
        raise ValueError("Discount cannot exceed total amount")

    effective_total = total_amount - discount_amount
    if amount_paid > effective_total:
        raise ValueError("Amount paid cannot exceed total after discount")

    sample_date = payload.sample_date or date.today()
    if sample_date > date.today():
        raise ValueError("sample_date cannot be in the future")

    estimated_report_date = payload.estimated_report_date or (sample_date + timedelta(days=1))

    commission_pct = 0.0
    commission_amount = 0.0
    if payload.doctor_id:
        from backend.app.models.doctor import Doctor
        doc = db.query(Doctor).filter(Doctor.id == payload.doctor_id).first()
        if doc:
            commission_pct = float(doc.commission_pct)
            commission_amount = float(effective_total) * (commission_pct / 100.0)

    patient = patient_repo.create_patient(
        db,
        patient_code=patient_code,
        name=payload.name,
        age=payload.age,
        gender=payload.gender,
        mobile=payload.mobile,
        doctor_id=payload.doctor_id,
        collected_by=current_user_id,
        collection_type=payload.collection_type,
        sample_date=sample_date,
        estimated_report_date=estimated_report_date,
        total_amount=total_amount,
        discount_amount=discount_amount,
        amount_paid=amount_paid,
        payment_mode=payload.payment_mode if amount_paid > 0 else None,
        referred_doctor_commission_pct=commission_pct,
        referred_doctor_commission_amount=commission_amount,
    )

    # Insert patient_tests with price snapshot
    for test_id in payload.test_ids:
        patient_repo.add_patient_test(db, patient.id, test_id, price_map[str(test_id)])

    audit_service.log(
        db, "patient.create",
        actor_user_id=current_user_id,
        entity_type="patient",
        entity_id=patient.id,
        after={"patient_code": patient_code, "name": payload.name, "total": total_amount},
    )

    db.commit()
    return _patient_to_dict(db, patient)


def update_patient(db: Session, patient_id: uuid.UUID, payload: PatientUpdate,
                   current_user_id: uuid.UUID) -> dict:
    """FR-4.1 — Edit patient. Recomputes total if tests changed."""
    patient = patient_repo.get_by_id(db, patient_id)
    if not patient:
        raise ValueError("Patient not found")

    before = _patient_to_dict(db, patient)
    update_data = payload.model_dump(exclude_none=True)

    # Check same-day same-test duplicates for patient by mobile number on update
    new_mobile = payload.mobile or patient.mobile
    new_sample_date = payload.sample_date or patient.sample_date
    new_test_ids = payload.test_ids if payload.test_ids is not None else [t.id for t in patient.patient_tests]

    if payload.mobile is not None or payload.sample_date is not None or payload.test_ids is not None:
        from backend.app.models.patient import Patient
        from backend.app.models.patient_test import PatientTest
        from backend.app.models.test import Test

        existing_patients = db.query(Patient).filter(
            Patient.mobile == new_mobile,
            Patient.sample_date == new_sample_date,
            Patient.id != patient.id,
            Patient.deleted_at.is_(None)
        ).all()
        if existing_patients:
            existing_patient_ids = [p.id for p in existing_patients]
            duplicates = db.query(PatientTest).filter(
                PatientTest.patient_id.in_(existing_patient_ids),
                PatientTest.test_id.in_(new_test_ids)
            ).all()
            if duplicates:
                dup_test_ids = [d.test_id for d in duplicates]
                dup_tests = db.query(Test).filter(Test.id.in_(dup_test_ids)).all()
                dup_names = ", ".join([t.name for t in dup_tests])
                raise ValueError(f"Patient with mobile {new_mobile} has already booked test(s) ({dup_names}) on this day")

    # If tests changed, recompute total
    if "test_ids" in update_data:
        price_map = test_repo.get_current_prices(db, update_data["test_ids"])
        total_amount = sum(price_map.values())
        patient_repo.delete_patient_tests(db, patient_id)
        for test_id in update_data.pop("test_ids"):
            patient_repo.add_patient_test(db, patient_id, test_id, price_map[str(test_id)])
        update_data["total_amount"] = total_amount

    # Validate payment
    discount_amount = update_data.get("discount_amount", float(patient.discount_amount or 0))
    amount_paid = update_data.get("amount_paid", float(patient.amount_paid or 0))
    total = update_data.get("total_amount", float(patient.total_amount or 0))
    if discount_amount < 0:
        raise ValueError("Discount amount cannot be negative")
    if discount_amount > total:
        raise ValueError("Discount cannot exceed total amount")
    if amount_paid > (total - discount_amount):
        raise ValueError("Amount paid cannot exceed total after discount")

    # Recompute doctor commission if doctor_id, total_amount, or discount_amount changed
    if "doctor_id" in update_data or "total_amount" in update_data or "discount_amount" in update_data:
        new_doc_id = update_data.get("doctor_id") if "doctor_id" in update_data else patient.doctor_id
        new_total = update_data.get("total_amount") if "total_amount" in update_data else patient.total_amount
        new_discount = update_data.get("discount_amount") if "discount_amount" in update_data else patient.discount_amount
        
        commission_pct = 0.0
        commission_amount = 0.0
        if new_doc_id:
            from backend.app.models.doctor import Doctor
            doc = db.query(Doctor).filter(Doctor.id == new_doc_id).first()
            if doc:
                commission_pct = float(doc.commission_pct)
                effective_total = float(new_total or 0) - float(new_discount or 0)
                commission_amount = float(effective_total) * (commission_pct / 100.0)
        
        update_data["referred_doctor_commission_pct"] = commission_pct
        update_data["referred_doctor_commission_amount"] = commission_amount

    patient_repo.update_patient(db, patient_id, **update_data)
    audit_service.log(
        db, "patient.edit",
        actor_user_id=current_user_id,
        entity_type="patient",
        entity_id=patient_id,
        before=before,
        after=update_data,
    )
    db.commit()

    patient = patient_repo.get_by_id(db, patient_id)
    return _patient_to_dict(db, patient)


def get_patient(db: Session, patient_id: uuid.UUID) -> dict:
    patient = patient_repo.get_by_id(db, patient_id)
    if not patient:
        raise ValueError("Patient not found")
    return _patient_to_dict(db, patient)


def list_patients(db: Session, current_user, **kwargs) -> dict:
    """FR-6.1 — view_scope enforcement happens here in the service."""
    from backend.app.models.user import RoleEnum, ViewScopeEnum

    # Server-side scope enforcement — cannot be bypassed
    if current_user.role == RoleEnum.staff and current_user.view_scope == ViewScopeEnum.own:
        kwargs["collected_by"] = current_user.id

    page = kwargs.pop("page", 1)
    page_size = min(kwargs.pop("page_size", 20), 100)

    items, total = patient_repo.list_patients(db, page=page, page_size=page_size, **kwargs)
    total_pages = (total + page_size - 1) // page_size

    return {
        "items": [_patient_to_dict(db, p) for p in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def generate_qr_payload(db: Session, patient_id: uuid.UUID) -> str:
    """FR-4.3 — local UPI deep-link, no external API."""
    from backend.app.config import settings
    patient = patient_repo.get_by_id(db, patient_id)
    if not patient:
        raise ValueError("Patient not found")

    due = float(patient.total_amount or 0) - float(patient.amount_paid or 0)
    if due <= 0:
        due = float(patient.total_amount or 0)

    vpa = settings.LAB_UPI_VPA
    lab_name = settings.LAB_NAME.replace(" ", "%20")
    return (
        f"upi://pay?pa={vpa}&pn={lab_name}"
        f"&am={due:.2f}&cu=INR&tn={patient.patient_code}"
    )


def _patient_to_dict(db: Session, patient) -> dict:
    """Convert Patient ORM object to dict for API response."""
    tests = []
    for pt in (patient.patient_tests or []):
        test_obj = pt.test
        price = float(pt.price_at_booking)
        tests.append({
            "id": str(pt.test_id),           # test UUID
            "test_id": str(pt.test_id),      # alias used by setSelectedTests()
            "name": test_obj.name if test_obj else "Unknown",
            "price": price,                  # alias expected by frontend
            "price_at_booking": price,       # kept for schema compatibility
        })

    return {
        "id": str(patient.id),
        "patient_code": patient.patient_code,
        "name": patient.name,
        "age": patient.age,
        "gender": patient.gender,
        "mobile": patient.mobile,
        "doctor_id": str(patient.doctor_id) if patient.doctor_id else None,
        "doctor_name": patient.doctor.name if patient.doctor else None,
        "collection_type": patient.collection_type,
        "sample_date": str(patient.sample_date) if patient.sample_date else None,
        "estimated_report_date": str(patient.estimated_report_date),
        "total_amount": float(patient.total_amount or 0),
        "discount_amount": float(patient.discount_amount or 0),
        "amount_paid": float(patient.amount_paid or 0),
        "amount_due": patient.amount_due,
        "payment_mode": patient.payment_mode,
        "payment_status": patient.payment_status,
        "referred_doctor_commission_pct": float(patient.referred_doctor_commission_pct or 0.0),
        "referred_doctor_commission_amount": float(patient.referred_doctor_commission_amount or 0.0),
        "status": patient.status,
        "processing_note": patient.processing_note,
        "created_at": patient.created_at.isoformat() if patient.created_at else None,
        "updated_at": patient.updated_at.isoformat() if patient.updated_at else None,
        "tests": tests,
        "collected_by_name": patient.collector.name if patient.collector else None,
    }
