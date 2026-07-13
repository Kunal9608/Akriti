"""User repository — all DB queries for the users table."""
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid

from backend.app.models.user import User, RoleEnum


def normalize_email(email: str) -> str:
    email = email.lower().strip()
    if "@" in email:
        local, domain = email.rsplit("@", 1)
        local = local.replace(".", "")
        return f"{local}@{domain}"
    return email


def get_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == normalize_email(email)).first()


def get_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_all_staff(db: Session, include_inactive: bool = False) -> List[User]:
    q = db.query(User).filter(User.role == RoleEnum.staff)
    if not include_inactive:
        q = q.filter(User.deactivated_at.is_(None))
    return q.order_by(User.created_at.desc()).all()


def get_staff_paginated(
    db: Session,
    include_inactive: bool = False,
    q: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20,
):
    """Paginated + searchable staff list."""
    from typing import Tuple
    query = db.query(User).filter(User.role == RoleEnum.staff)
    if not include_inactive:
        query = query.filter(User.deactivated_at.is_(None))
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    if q:
        search = f"%{q.strip()}%"
        query = query.filter(
            User.name.ilike(search) | User.email.ilike(search)
        )
    total = query.count()
    items = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def create_user(db: Session, **kwargs) -> User:
    # Normalize email
    if "email" in kwargs:
        kwargs["email"] = normalize_email(kwargs["email"])
    user = User(**kwargs)
    db.add(user)
    db.flush()  # get ID without committing
    return user


def update_user(db: Session, user_id: uuid.UUID, **kwargs) -> Optional[User]:
    user = get_by_id(db, user_id)
    if not user:
        return None
    for k, v in kwargs.items():
        setattr(user, k, v)
    db.flush()
    return user


def count_active_staff(db: Session) -> int:
    return db.query(User).filter(
        User.role == RoleEnum.staff,
        User.is_active == True,
        User.deactivated_at.is_(None)
    ).count()
