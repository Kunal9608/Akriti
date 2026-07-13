"""Test catalog model."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, Boolean, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.core.db import Base


class Test(Base):
    __tablename__ = "tests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                server_default=text("gen_random_uuid()"))
    test_code = Column(String(16), nullable=True, unique=True)
    name = Column(String(150), nullable=False, unique=True)
    price = Column(Numeric(10, 2), nullable=False)
    category = Column(String(80), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    patient_tests = relationship("PatientTest", back_populates="test")
    price_history = relationship("TestPriceHistory", back_populates="test", cascade="all, delete-orphan")
