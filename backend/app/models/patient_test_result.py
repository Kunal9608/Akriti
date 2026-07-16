"""Patient Test Result model (§2.3) for structured result entry."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Text, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.core.db import Base


class PatientTestResult(Base):
    __tablename__ = "patient_test_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                server_default=text("gen_random_uuid()"))
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    test_id = Column(UUID(as_uuid=True), ForeignKey("tests.id", ondelete="CASCADE"), nullable=False, index=True)
    parameter_id = Column(UUID(as_uuid=True), ForeignKey("test_parameters.id", ondelete="CASCADE"), nullable=False, index=True)
    entered_value = Column(String(100), nullable=False)
    is_abnormal = Column(Boolean, default=False)
    interpretation_note = Column(Text, nullable=True)
    entered_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    entered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    patient = relationship("Patient", back_populates="test_results")
    test = relationship("Test")
    parameter = relationship("TestParameter")
    entered_by_user = relationship("User")
