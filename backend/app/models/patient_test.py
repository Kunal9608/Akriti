"""PatientTest junction model — many-to-many with price snapshot."""
import uuid
from sqlalchemy import Column, Numeric, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.core.db import Base


class PatientTest(Base):
    __tablename__ = "patient_tests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                server_default=text("gen_random_uuid()"))
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    test_id = Column(UUID(as_uuid=True), ForeignKey("tests.id"), nullable=False, index=True)
    price_at_booking = Column(Numeric(10, 2), nullable=False)

    patient = relationship("Patient", back_populates="patient_tests")
    test = relationship("Test", back_populates="patient_tests")
