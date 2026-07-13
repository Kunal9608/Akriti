"""Immutable audit log with hash chaining — INSERT only at DB role level."""
from datetime import datetime, timezone
from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from backend.app.core.db import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String(60), nullable=False)
    entity_type = Column(String(40), nullable=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    before_value = Column(JSONB, nullable=True)
    after_value = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)
    occurred_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    record_hash = Column(String(64), nullable=False)
    prev_hash = Column(String(64), nullable=False, default="GENESIS")

    actor = relationship("User")
