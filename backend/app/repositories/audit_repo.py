"""Audit log repository — INSERT only."""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
import uuid

from backend.app.models.audit_log import AuditLog


def get_last_row(db: Session) -> Optional[AuditLog]:
    return db.query(AuditLog).order_by(desc(AuditLog.id)).first()


def insert_log(db: Session, **kwargs) -> AuditLog:
    log = AuditLog(**kwargs)
    db.add(log)
    db.flush()
    return log


def get_logs(db: Session, page: int = 1, page_size: int = 50,
             action: Optional[str] = None, user_id: Optional[uuid.UUID] = None,
             date_from=None, date_to=None):
    q = db.query(AuditLog)
    if action:
        q = q.filter(AuditLog.action.ilike(f"%{action}%"))
    if user_id:
        q = q.filter(AuditLog.actor_user_id == user_id)
    if date_from:
        q = q.filter(AuditLog.occurred_at >= date_from)
    if date_to:
        q = q.filter(AuditLog.occurred_at <= date_to)
        
    # Cap total count at 1000 to prevent full table scans on millions of logs
    count_q = q.limit(1000).subquery()
    total = db.query(count_q).count()
    
    items = q.order_by(desc(AuditLog.id)).offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def get_all_ordered(db: Session):
    """For integrity check — ordered by id ascending."""
    return db.query(AuditLog).order_by(AuditLog.id).yield_per(1000)
