"""Doctor reference model."""
import uuid
from sqlalchemy import Column, String, Boolean, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.core.db import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                server_default=text("gen_random_uuid()"))
    name = Column(String(120), nullable=False)
    clinic_name = Column(String(150), nullable=True)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("name", "clinic_name", name="uq_doctor_name_clinic"),
    )

    patients = relationship("Patient", back_populates="doctor")
