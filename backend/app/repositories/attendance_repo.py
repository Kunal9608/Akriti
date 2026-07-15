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
    start_dt = datetime.combine(today, datetime.min.time())
    end_dt = datetime.combine(today, datetime.max.time())
    return (
        db.query(AttendanceEvent)
        .filter(
            AttendanceEvent.user_id == user_id,
            AttendanceEvent.event_time >= start_dt,
            AttendanceEvent.event_time <= end_dt,
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


def get_user_events_today(db: Session, user_id: uuid.UUID) -> List[AttendanceEvent]:
    today = date.today()
    start_dt = datetime.combine(today, datetime.min.time())
    end_dt = datetime.combine(today, datetime.max.time())
    return (
        db.query(AttendanceEvent)
        .filter(
            AttendanceEvent.user_id == user_id,
            AttendanceEvent.event_time >= start_dt,
            AttendanceEvent.event_time <= end_dt,
            AttendanceEvent.is_pending == 0,
        )
        .order_by(AttendanceEvent.event_time)
        .all()
    )


def get_pending_events(db: Session) -> List[AttendanceEvent]:
    return (
        db.query(AttendanceEvent)
        .options(joinedload(AttendanceEvent.user))
        .filter(AttendanceEvent.is_pending == 1)
        .order_by(AttendanceEvent.event_time.desc())
        .all()
    )


def get_event_by_id(db: Session, event_id: uuid.UUID) -> Optional[AttendanceEvent]:
    return db.query(AttendanceEvent).filter(AttendanceEvent.id == event_id).first()


def get_today_present_user_ids(db: Session) -> List[uuid.UUID]:
    today = date.today()
    start_dt = datetime.combine(today, datetime.min.time())
    end_dt = datetime.combine(today, datetime.max.time())
    rows = (
        db.query(AttendanceEvent.user_id)
        .filter(
            AttendanceEvent.event_time >= start_dt,
            AttendanceEvent.event_time <= end_dt,
            AttendanceEvent.event_type == "check_in",
            AttendanceEvent.is_pending == 0,
        )
        .distinct()
        .all()
    )
    return [r[0] for r in rows]


def get_events_for_range(db: Session, date_from: date, date_to: date,
                         user_id: Optional[uuid.UUID] = None) -> List[AttendanceEvent]:
    start_dt = datetime.combine(date_from, datetime.min.time())
    end_dt = datetime.combine(date_to, datetime.max.time())
    q = (
        db.query(AttendanceEvent)
        .options(joinedload(AttendanceEvent.user))
        .filter(
            AttendanceEvent.event_time >= start_dt,
            AttendanceEvent.event_time <= end_dt,
        )
    )
    if user_id:
        q = q.filter(AttendanceEvent.user_id == user_id)
    return q.order_by(AttendanceEvent.event_time).all()
