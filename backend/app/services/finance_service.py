"""Finance service — expenses, revenue aggregation, profit/loss."""
import uuid
from datetime import date, datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.expense import Expense
from backend.app.models.patient import Patient
from backend.app.repositories import audit_repo
from backend.app.services import audit_service


def create_expense(db: Session, payload, actor_id: uuid.UUID) -> dict:
    expense = Expense(
        category=payload.category,
        description=payload.description,
        amount=payload.amount,
        paid_to=payload.paid_to,
        payment_mode=payload.payment_mode,
        expense_date=payload.expense_date,
        recorded_by=actor_id,
    )
    db.add(expense)
    db.flush()
    audit_service.log(db, "expense.create", actor_user_id=actor_id,
                      entity_type="expense", entity_id=expense.id,
                      after={"amount": payload.amount, "category": payload.category})
    db.commit()
    return _expense_to_dict(expense)


def list_expenses(db: Session, date_from: Optional[date] = None,
                  date_to: Optional[date] = None, category: Optional[str] = None,
                  page: int = 1, page_size: int = 50):
    q = db.query(Expense)
    if date_from:
        q = q.filter(Expense.expense_date >= date_from)
    if date_to:
        q = q.filter(Expense.expense_date <= date_to)
    if category:
        q = q.filter(Expense.category == category)
    total = q.count()
    items = q.order_by(Expense.expense_date.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return [_expense_to_dict(e) for e in items], total


def get_profit_loss(db: Session, date_from: date, date_to: date) -> dict:
    """FR-9.1 — Net profit/loss over a date range."""
    revenue = db.query(func.sum(Patient.amount_paid)).filter(
        func.date(Patient.created_at) >= date_from,
        func.date(Patient.created_at) <= date_to,
        Patient.deleted_at.is_(None),
    ).scalar() or 0

    expenses = db.query(func.sum(Expense.amount)).filter(
        Expense.expense_date >= date_from,
        Expense.expense_date <= date_to,
    ).scalar() or 0

    commissions = db.query(func.sum(Patient.referred_doctor_commission_amount)).filter(
        func.date(Patient.created_at) >= date_from,
        func.date(Patient.created_at) <= date_to,
        Patient.deleted_at.is_(None),
    ).scalar() or 0

    return {
        "from_date": str(date_from),
        "to_date": str(date_to),
        "total_revenue": float(revenue),
        "total_expenses": float(expenses),
        "total_doctor_commissions": float(commissions),
        "net_profit": float(revenue) - float(expenses) - float(commissions),
    }


def get_daily_revenue(db: Session, date_from: date, date_to: date) -> dict:
    """FR-8.1 — Daily revenue series for charts."""
    rows = db.query(
        func.date(Patient.created_at).label("day"),
        func.sum(Patient.amount_paid).label("revenue"),
        func.count(Patient.id).label("count"),
    ).filter(
        func.date(Patient.created_at) >= date_from,
        func.date(Patient.created_at) <= date_to,
        Patient.deleted_at.is_(None),
    ).group_by(func.date(Patient.created_at)).order_by("day").all()

    data = [{"period": str(r.day), "revenue": float(r.revenue or 0), "patient_count": r.count} for r in rows]
    return {"data": data, "total": sum(d["revenue"] for d in data)}


def get_monthly_revenue(db: Session, year: int) -> dict:
    """FR-8.1 — Monthly revenue series."""
    rows = db.query(
        func.extract("month", Patient.created_at).label("month"),
        func.sum(Patient.amount_paid).label("revenue"),
        func.count(Patient.id).label("count"),
    ).filter(
        func.extract("year", Patient.created_at) == year,
        Patient.deleted_at.is_(None),
    ).group_by("month").order_by("month").all()

    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    data = [{"period": months[int(r.month)-1], "revenue": float(r.revenue or 0), "patient_count": r.count} for r in rows]
    return {"data": data, "total": sum(d["revenue"] for d in data)}


def get_payment_split(db: Session, date_from: date, date_to: date) -> dict:
    cash = db.query(func.sum(Patient.amount_paid), func.count(Patient.id)).filter(
        Patient.payment_mode == "cash",
        func.date(Patient.created_at) >= date_from,
        func.date(Patient.created_at) <= date_to,
        Patient.deleted_at.is_(None),
    ).first()
    qr = db.query(func.sum(Patient.amount_paid), func.count(Patient.id)).filter(
        Patient.payment_mode == "qr",
        func.date(Patient.created_at) >= date_from,
        func.date(Patient.created_at) <= date_to,
        Patient.deleted_at.is_(None),
    ).first()
    return {
        "cash_amount": float(cash[0] or 0),
        "cash_count": cash[1] or 0,
        "qr_amount": float(qr[0] or 0),
        "qr_count": qr[1] or 0,
    }


def get_dashboard_stats(db: Session) -> dict:
    from backend.app.repositories.patient_repo import get_today_stats
    from backend.app.repositories.attendance_repo import get_today_present_user_ids
    from backend.app.repositories.user_repo import count_active_staff

    today_stats = get_today_stats(db)
    today = date.today()
    month_start = today.replace(day=1)

    pl = get_profit_loss(db, month_start, today)
    present_ids = get_today_present_user_ids(db)
    total_staff = count_active_staff(db)

    return {
        "today_revenue": today_stats["revenue"],
        "today_patients": today_stats["count"],
        "pending_reports": today_stats["pending"],
        "outstanding_due": today_stats["due"],
        "staff_present": len(present_ids),
        "staff_total": total_staff,
        "monthly_revenue": pl["total_revenue"],
        "monthly_expenses": pl["total_expenses"],
        "monthly_doctor_commissions": pl["total_doctor_commissions"],
        "monthly_profit": pl["net_profit"],
    }


def _expense_to_dict(e) -> dict:
    return {
        "id": str(e.id),
        "category": e.category,
        "description": e.description,
        "amount": float(e.amount),
        "paid_to": e.paid_to,
        "payment_mode": e.payment_mode,
        "expense_date": str(e.expense_date),
        "created_at": e.created_at.isoformat() if e.created_at else None,
        "recorded_by_name": e.recorder.name if hasattr(e, "recorder") and e.recorder else None,
    }
