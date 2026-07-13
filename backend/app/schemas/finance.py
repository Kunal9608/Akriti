"""Finance schemas — expenses, revenue, profit/loss."""
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import date, datetime
import uuid


class ExpenseCreate(BaseModel):
    category: str
    description: Optional[str] = None
    amount: float
    paid_to: Optional[str] = None
    payment_mode: str
    expense_date: date
    attachment_path: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v):
        valid = ("rent", "reagents", "salaries", "utilities",
                 "equipment_maintenance", "courier_charges", "misc")
        if v not in valid:
            raise ValueError(f"category must be one of {valid}")
        return v

    @field_validator("payment_mode")
    @classmethod
    def validate_payment_mode(cls, v):
        if v not in ("cash", "bank_transfer", "upi"):
            raise ValueError("payment_mode must be cash, bank_transfer, or upi")
        return v


class ExpenseUpdate(BaseModel):
    category: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    paid_to: Optional[str] = None
    payment_mode: Optional[str] = None
    expense_date: Optional[date] = None


class ExpenseResponse(BaseModel):
    id: uuid.UUID
    category: str
    description: Optional[str]
    amount: float
    paid_to: Optional[str]
    payment_mode: str
    expense_date: date
    recorded_by_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProfitLossResponse(BaseModel):
    from_date: date
    to_date: date
    total_revenue: float
    total_expenses: float
    net_profit: float


class RevenuePoint(BaseModel):
    period: str  # date or month label
    revenue: float
    patient_count: int


class RevenueResponse(BaseModel):
    data: List[RevenuePoint]
    total: float


class PaymentSplitResponse(BaseModel):
    cash_amount: float
    qr_amount: float
    cash_count: int
    qr_count: int


class DashboardStats(BaseModel):
    today_revenue: float
    today_patients: int
    pending_reports: int
    outstanding_due: float
    staff_present: int
    staff_total: int
    monthly_revenue: float
    monthly_expenses: float
    monthly_profit: float
