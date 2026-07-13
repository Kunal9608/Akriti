"""Attendance repository."""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from datetime import date, datetime, timezone
from typing import Optional, List
import uuid

from backend.app.models.attendance_event import AttendanceEvent, EventTypeEnum
from backend.app.models.face_embedding import FaceEmbedding


def get_last_event_today(db: Session, user_id: uuid.UUID) -> Optional[AttendanceEvent]:
    today = date.today()
    return (
        db.query(AttendanceEvent)
        .filter(
            AttendanceEvent.user_id == user_id,
            func.date(AttendanceEvent.event_time) == today,
            AttendanceEvent.is_pending == 0,
        )
        .order_by(desc(AttendanceEvent.event_time))
        .first()
    )


def insert_event(db: Session, user_id: uuid.UUID, event_type: str,
                 confidence: float, device_id: Optional[str] = None,
                 source: str = "online", is_pending: bool = False) -> AttendanceEvent:
    event = AttendanceEvent(
        user_id=user_id,
        event_type=event_type,
        matched_confidence=confidence,
        device_id=device_id,
        source=source,
        is_pending=1 if is_pending else 0,
    )
    db.add(event)
    db.flush()
    return event


def get_all_embeddings(db: Session) -> List[FaceEmbedding]:
    return db.query(FaceEmbedding).all()


def get_embeddings_for_user(db: Session, user_id: uuid.UUID) -> List[FaceEmbedding]:
    return db.query(FaceEmbedding).filter(FaceEmbedding.user_id == user_id).all()


def count_embeddings_for_user(db: Session, user_id: uuid.UUID) -> int:
    return db.query(FaceEmbedding).filter(FaceEmbedding.user_id == user_id).count()


def add_embedding(db: Session, user_id: uuid.UUID, embedding, sample_index: int) -> FaceEmbedding:
    fe = FaceEmbedding(user_id=user_id, embedding=embedding, sample_index=sample_index)
    db.add(fe)
    db.flush()
    return fe


def get_today_present_user_ids(db: Session) -> List[uuid.UUID]:
    today = date.today()
    rows = (
        db.query(AttendanceEvent.user_id)
        .filter(
            func.date(AttendanceEvent.event_time) == today,
            AttendanceEvent.event_type == "check_in",
            AttendanceEvent.is_pending == 0,
        )
        .distinct()
        .all()
    )
    return [r[0] for r in rows]


def get_events_for_range(db: Session, date_from: date, date_to: date,
                         user_id: Optional[uuid.UUID] = None) -> List[AttendanceEvent]:
    q = (
        db.query(AttendanceEvent)
        .options(joinedload(AttendanceEvent.user))
        .filter(
            func.date(AttendanceEvent.event_time) >= date_from,
            func.date(AttendanceEvent.event_time) <= date_to,
        )
    )
    if user_id:
        q = q.filter(AttendanceEvent.user_id == user_id)
    return q.order_by(AttendanceEvent.event_time).all()
