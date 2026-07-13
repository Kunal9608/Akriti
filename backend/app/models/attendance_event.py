"""AttendanceEvent model."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Enum, Numeric, String, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
import enum

from backend.app.core.db import Base


class EventTypeEnum(str, enum.Enum):
    check_in = "check_in"
    check_out = "check_out"


class AttendanceSourceEnum(str, enum.Enum):
    online = "online"
    offline_synced = "offline_synced"


class AttendanceEvent(Base):
    __tablename__ = "attendance_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    event_type = Column(Enum(EventTypeEnum, name="event_type_enum"), nullable=False)
    matched_confidence = Column(Numeric(5, 4), nullable=False, default=1.0)
    device_id = Column(String(64), nullable=True)
    event_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    source = Column(Enum(AttendanceSourceEnum, name="attendance_source_enum"), default="online")
    is_pending = Column(Numeric(1, 0), default=0)  # 1 = pending admin review (low confidence)

    user = relationship("User", back_populates="attendance_events")
