"""Test Parameter Master model (§2.1 / §2.3)."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, SmallInteger, Numeric, ForeignKey, text, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from backend.app.core.db import Base, is_sqlite


class TestParameter(Base):
    __tablename__ = "test_parameters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                server_default=text("gen_random_uuid()"))
    test_id = Column(UUID(as_uuid=True), ForeignKey("tests.id", ondelete="CASCADE"), nullable=False, index=True)
    parameter_name = Column(String(120), nullable=False)
    unit = Column(String(20), nullable=True)
    input_type = Column(String(20), nullable=False)  # 'numeric', 'text', 'dropdown'
    dropdown_options = Column(JSON if is_sqlite else JSONB, nullable=True)  # List[str] e.g. ["Positive", "Negative"]
    reference_low = Column(Numeric(10, 3), nullable=True)
    reference_high = Column(Numeric(10, 3), nullable=True)
    reference_text = Column(String(200), nullable=True)
    applicable_gender = Column(String(20), default="all")  # 'all', 'male', 'female'
    display_order = Column(SmallInteger, nullable=False, default=1)

    test = relationship("Test", back_populates="parameters")
