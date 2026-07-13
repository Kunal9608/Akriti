"""
Database engine, session factory, and base model.
"""
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import QueuePool
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from backend.app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency — yields a DB session and ensures it's closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def enable_pgvector(db_session):
    """Enable pgvector extension if available."""
    try:
        db_session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        db_session.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        db_session.commit()
    except Exception:
        db_session.rollback()


def init_db():
    """Create all tables (used in development; production uses Alembic)."""
    from backend.app.models import (  # noqa: F401 — import all models for metadata
        user, face_embedding, attendance_event, patient, patient_test,
        test, test_price_history, doctor, franchise, report, expense,
        login_history, active_session, audit_log, otp_request
    )
    Base.metadata.create_all(bind=engine)

    # Ensure staff_code and test_code columns exist (SQLite/PostgreSQL fallback)
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS staff_code VARCHAR(16) UNIQUE;"))
        conn.execute(text("ALTER TABLE tests ADD COLUMN IF NOT EXISTS test_code VARCHAR(16) UNIQUE;"))
        conn.commit()
