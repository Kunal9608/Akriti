"""Staff router."""
from fastapi import APIRouter, Depends, UploadFile, File, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional

from backend.app.core.db import get_db
from backend.app.dependencies import get_current_user, require_admin
from backend.app.schemas.staff import StaffCreate, StaffUpdate
from backend.app.services import staff_service, face_service

router = APIRouter(prefix="/staff", tags=["staff"])


@router.get("")
def list_staff(
    include_inactive: bool = False,
    q: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return staff_service.list_staff(
        db, include_inactive=include_inactive, q=q,
        is_active=is_active, page=page, page_size=page_size,
    )


@router.post("")
def create_staff(payload: StaffCreate, background_tasks: BackgroundTasks, admin=Depends(require_admin),
                 db: Session = Depends(get_db)):
    return staff_service.create_staff(db, payload, admin.id, background_tasks)


@router.get("/{staff_id}")
def get_staff(staff_id: str, current_user=Depends(get_current_user),
              db: Session = Depends(get_db)):
    import uuid
    return staff_service.get_staff(db, uuid.UUID(staff_id))


@router.patch("/{staff_id}")
def update_staff(staff_id: str, payload: StaffUpdate,
                 admin=Depends(require_admin), db: Session = Depends(get_db)):
    import uuid
    return staff_service.update_staff(db, uuid.UUID(staff_id), payload, admin.id)


@router.delete("/{staff_id}")
def deactivate_staff(staff_id: str, admin=Depends(require_admin),
                     db: Session = Depends(get_db)):
    import uuid
    return staff_service.deactivate_staff(db, uuid.UUID(staff_id), admin.id)


@router.post("/{staff_id}/face-enroll")
async def face_enroll(staff_id: str, image: UploadFile = File(...),
                      current_user=Depends(get_current_user),
                      db: Session = Depends(get_db)):
    import uuid
    image_bytes = await image.read()
    return face_service.enroll_sample(db, uuid.UUID(staff_id), image_bytes)
