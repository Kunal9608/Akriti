"""Login history — every auth attempt recorded."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Enum, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
import enum

from backend.app.core.db import Base


class LoginOutcomeEnum(str, enum.Enum):
    success = "success"
    bad_password = "bad_password"
    bad_otp = "bad_otp"
    locked_out = "locked_out"
    unknown_email = "unknown_email"


class LoginHistory(Base):
    __tablename__ = "login_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    email_attempted = Column(String(255), nullable=False)
    outcome = Column(Enum(LoginOutcomeEnum, name="login_outcome_enum"), nullable=False)
    ip_address = Column(String(45), nullable=False)  # String for cross-DB compat
    user_agent = Column(String(255), nullable=True)
    attempted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", back_populates="login_history")
