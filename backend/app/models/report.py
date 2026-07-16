"""Report model with digital signature and version tracking."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.core.db import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                server_default=text("gen_random_uuid()"))
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True)
    signed = Column(Boolean, default=False)
    signature_applied_at = Column(DateTime(timezone=True), nullable=True)
    verification_hash = Column(String(128), nullable=True)
    version = Column(Integer, default=1)
    source = Column(String(20), default="manual")  # 'manual' vs 'auto'
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    uploaded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_latest = Column(Boolean, default=True)

    patient = relationship("Patient", back_populates="reports")
    uploader = relationship("User", back_populates="reports_uploaded")
