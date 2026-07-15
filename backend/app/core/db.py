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


import time
import logging

logger = logging.getLogger("akriti.db")

is_sqlite = settings.DATABASE_URL.startswith("sqlite")

engine_kwargs = {
    "poolclass": QueuePool if not is_sqlite else None,
    "echo": False,
}

if not is_sqlite:
    engine_kwargs.update({
        "pool_size": 15,
        "max_overflow": 30,
        "pool_timeout": 30,
        "pool_recycle": 1800,  # Recycle every 30m to prevent stale sockets/leaks on Supabase
        "pool_pre_ping": True,
        "connect_args": {
            "options": "-c statement_timeout=15000 -c lock_timeout=5000"
        }
    })
else:
    engine_kwargs.update({
        "connect_args": {"check_same_thread": False}
    })

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault("query_start_time", []).append(time.time())


@event.listens_for(engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    times = conn.info.get("query_start_time", [])
    if times:
        start_time = times.pop(-1)
        duration = time.time() - start_time
        if duration > 0.2:  # Log slow queries exceeding 200ms
            logger.warning(
                f"SLOW SQL [{duration:.3f}s]: {statement[:200]} | params: {str(parameters)[:100]}"
            )


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
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_locked BOOLEAN DEFAULT FALSE;"))
        conn.execute(text("ALTER TABLE doctors ADD COLUMN IF NOT EXISTS commission_pct NUMERIC(5, 2) DEFAULT 0.0;"))
        conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS referred_doctor_commission_pct NUMERIC(5, 2) DEFAULT 0.0;"))
        conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS referred_doctor_commission_amount NUMERIC(10, 2) DEFAULT 0.0;"))
        
        # Add franchise columns fallback
        conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS franchise_name VARCHAR(100);"))
        conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS franchise_other VARCHAR(100);"))
        conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS sample_sent_date DATE;"))
        conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS sample_sent_time VARCHAR(20);"))
        conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS courier_name VARCHAR(100);"))
        conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS tracking_id VARCHAR(100);"))
        conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS franchise_remarks VARCHAR(255);"))
        
        # PostgreSQL extensions (if permitted)
        if not is_sqlite:
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto;"))
                conn.commit()
            except Exception:
                conn.rollback()

        # Enterprise Scale Indexes (10M+ records support)
        # 1. Partial indexes on active patients (WHERE deleted_at IS NULL)
        if not is_sqlite:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_patients_active_created ON patients (created_at DESC) WHERE deleted_at IS NULL;"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_patients_active_status ON patients (status, created_at DESC) WHERE deleted_at IS NULL;"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_patients_active_doctor ON patients (doctor_id, created_at DESC) WHERE deleted_at IS NULL;"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_patients_active_mobile ON patients (mobile) WHERE deleted_at IS NULL;"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_patients_active_collector ON patients (collected_by, created_at DESC) WHERE deleted_at IS NULL;"))
            # Trigram / ILIKE prefix optimization on patient name
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_patients_name_trgm ON patients USING gin (name gin_trgm_ops);"))
            except Exception:
                conn.rollback()
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_patients_name_lower ON patients (lower(name));"))
            
            # Trigram on test catalog
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tests_name_trgm ON tests USING gin (name gin_trgm_ops);"))
            except Exception:
                conn.rollback()
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tests_name_lower ON tests (lower(name));"))
            
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_staff_active ON users (created_at DESC) WHERE role = 'staff';"))
        else:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_patients_active_created ON patients (created_at DESC);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_patients_active_status ON patients (status, created_at DESC);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_staff_active ON users (created_at DESC);"))

        # 2. Composite and Foreign Key scale indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_patient_tests_patient_id ON patient_tests (patient_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_patient_tests_test_id ON patient_tests (test_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reports_patient_version ON reports (patient_id, version DESC);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reports_verification_hash ON reports (verification_hash);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reports_uploaded_by ON reports (uploaded_by);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_active_sessions_refresh_token_hash ON active_sessions (refresh_token_hash);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_active_sessions_user_id ON active_sessions (user_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_patients_doctor_id ON patients (doctor_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_patients_collected_by ON patients (collected_by);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_face_embeddings_user_id ON face_embeddings (user_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_expenses_date_cat ON expenses (expense_date DESC, category);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_login_history_email_time ON login_history (email_attempted, attempted_at DESC);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_login_history_user_id ON login_history (user_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_logs_actor_time ON audit_logs (actor_user_id, occurred_at DESC);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_logs_action_time ON audit_logs (action, occurred_at DESC);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_attendance_user_time ON attendance_events (user_id, event_time DESC);"))
        conn.commit()
        
        # PostgreSQL custom enum values fallback
        try:
            conn.execute(text("ALTER TYPE patient_status_enum ADD VALUE IF NOT EXISTS 'sent_to_franchise';"))
            conn.commit()
        except Exception:
            pass

        try:
            conn.execute(text("ALTER TYPE otp_purpose_enum ADD VALUE IF NOT EXISTS 'delete_verify';"))
            conn.execute(text("ALTER TYPE otp_purpose_enum ADD VALUE IF NOT EXISTS 'password_change';"))
            conn.commit()
        except Exception:
            pass
