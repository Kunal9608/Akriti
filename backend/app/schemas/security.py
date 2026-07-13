"""Security schemas — sessions, login history, audit logs."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid


class SessionResponse(BaseModel):
    id: uuid.UUID
    device_label: Optional[str]
    ip_address: Optional[str]
    issued_at: datetime
    last_active_at: datetime
    is_current: bool = False

    class Config:
        from_attributes = True


class LoginHistoryResponse(BaseModel):
    id: uuid.UUID
    email_attempted: str
    outcome: str
    ip_address: str
    user_agent: Optional[str]
    attempted_at: datetime
    user_name: Optional[str] = None

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    id: int
    actor_name: Optional[str] = None
    action: str
    entity_type: Optional[str]
    entity_id: Optional[uuid.UUID]
    before_value: Optional[dict] = None
    after_value: Optional[dict] = None
    ip_address: Optional[str]
    occurred_at: datetime
    record_hash: str

    class Config:
        from_attributes = True


class AttendanceResponse(BaseModel):
    id: uuid.UUID
    user_name: str
    event_type: str
    matched_confidence: float
    event_time: datetime
    source: str

    class Config:
        from_attributes = True


class AttendanceReportEntry(BaseModel):
    user_id: uuid.UUID
    user_name: str
    date: str
    check_in: Optional[str]
    check_out: Optional[str]
    hours_present: Optional[float]
    is_late: bool
    is_early_leave: bool
