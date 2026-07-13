"""Expense model — lab operating expenses."""
import uuid
from datetime import datetime, date, timezone
from sqlalchemy import Column, String, Numeric, Enum, Date, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from backend.app.core.db import Base


class ExpenseCategoryEnum(str, enum.Enum):
    rent = "rent"
    reagents = "reagents"
    salaries = "salaries"
    utilities = "utilities"
    equipment_maintenance = "equipment_maintenance"
    courier_charges = "courier_charges"
    misc = "misc"


class ExpensePaymentModeEnum(str, enum.Enum):
    cash = "cash"
    bank_transfer = "bank_transfer"
    upi = "upi"


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                server_default=text("gen_random_uuid()"))
    category = Column(Enum(ExpenseCategoryEnum, name="expense_category_enum"), nullable=False)
    description = Column(String(200), nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    paid_to = Column(String(150), nullable=True)
    payment_mode = Column(Enum(ExpensePaymentModeEnum, name="expense_payment_mode_enum"), nullable=False)
    attachment_path = Column(String(255), nullable=True)
    expense_date = Column(Date, nullable=False, default=lambda: date.today())
    recorded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    recorder = relationship("User", back_populates="expenses_recorded")
