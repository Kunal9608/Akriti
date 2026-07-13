"""SQLAlchemy ORM Models — User (Staff + Admin)"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, Enum, DateTime, Date,
    ForeignKey, LargeBinary, CheckConstraint, text
)
from sqlalchemy.dialects.postgresql import UUID, BYTEA
from sqlalchemy.orm import relationship
import enum

from backend.app.core.db import Base


class RoleEnum(str, enum.Enum):
    admin = "admin"
    staff = "staff"


class ViewScopeEnum(str, enum.Enum):
    all = "all"
    own = "own"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                server_default=text("gen_random_uuid()"))
    role = Column(Enum(RoleEnum, name="role_enum"), nullable=False)
    staff_code = Column(String(16), nullable=True, unique=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    mobile = Column(String(10), nullable=True)
    dob = Column(Date, nullable=True)
    aadhar_encrypted = Column(BYTEA, nullable=True)
    aadhar_last4 = Column(String(4), nullable=True)
    view_scope = Column(Enum(ViewScopeEnum, name="view_scope_enum"), default="own")
    face_registered = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)
    must_reset_password = Column(Boolean, default=True)
    branch_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    deactivated_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("mobile ~ '^[6-9][0-9]{9}$'", name="chk_mobile_format"),
    )

    # Relationships
    face_embeddings = relationship("FaceEmbedding", back_populates="user", cascade="all, delete-orphan")
    attendance_events = relationship("AttendanceEvent", back_populates="user")
    patients_collected = relationship("Patient", foreign_keys="Patient.collected_by", back_populates="collector")
    login_history = relationship("LoginHistory", back_populates="user")
    active_sessions = relationship("ActiveSession", back_populates="user")
    expenses_recorded = relationship("Expense", back_populates="recorder")
    reports_uploaded = relationship("Report", back_populates="uploader")
