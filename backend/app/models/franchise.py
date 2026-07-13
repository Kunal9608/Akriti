"""Franchise/courier partner model."""
import uuid
from sqlalchemy import Column, String, SmallInteger, text
from sqlalchemy.dialects.postgresql import UUID

from backend.app.core.db import Base


class Franchise(Base):
    __tablename__ = "franchises"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                server_default=text("gen_random_uuid()"))
    name = Column(String(100), nullable=False)
    contact_info = Column(String(200), nullable=True)
    default_tat_days = Column(SmallInteger, nullable=True)
