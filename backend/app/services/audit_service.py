"""Audit service — hash-chained immutable log writer."""
import json
from datetime import datetime, timezone
from typing import Optional, Any
import uuid

from backend.app.core.security import sha256_hex, canonical_json
from backend.app.repositories import audit_repo


def _sanitize_for_json(data: Any) -> Any:
    from datetime import date, datetime
    import uuid
    from decimal import Decimal
    if isinstance(data, (datetime, date)):
        return data.isoformat()
    if isinstance(data, uuid.UUID):
        return str(data)
    if isinstance(data, Decimal):
        return float(data)
    if isinstance(data, bytes):
        try:
            return data.decode('utf-8')
        except UnicodeDecodeError:
            return data.hex()
    if hasattr(data, "value"):
        return data.value
    if isinstance(data, dict):
        return {k: _sanitize_for_json(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_sanitize_for_json(v) for v in data]
    return data


def log(db, action: str, actor_user_id: Optional[uuid.UUID] = None,
        entity_type: Optional[str] = None, entity_id: Optional[uuid.UUID] = None,
        before: Optional[Any] = None, after: Optional[Any] = None,
        ip_address: Optional[str] = None):
    """
    Write a hash-chained audit log entry.
    The record_hash links to the previous row — any tampering breaks the chain.
    """
    try:
        before = _sanitize_for_json(before)
        after = _sanitize_for_json(after)

        # Use PostgreSQL advisory lock to serialize audit log inserts and prevent hash-chain forks
        from sqlalchemy import text
        db.execute(text("SELECT pg_advisory_xact_lock(7777777)"))

        last_row = audit_repo.get_last_row(db)
        prev_hash = last_row.record_hash if last_row else "GENESIS"

        canonical = canonical_json({
            "action": action,
            "entity_type": entity_type,
            "entity_id": str(entity_id) if entity_id else None,
            "before": before,
            "after": after,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
        })
        record_hash = sha256_hex(canonical + prev_hash)

        audit_repo.insert_log(
            db,
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before_value=before,
            after_value=after,
            ip_address=ip_address,
            record_hash=record_hash,
            prev_hash=prev_hash,
        )
    except Exception as e:
        import logging
        logging.getLogger("akriti.audit").error(f"Audit log failed: {e}")
        # Audit log must never crash the main operation, but we log the error
        pass


def verify_chain(db) -> tuple[bool, Optional[int]]:
    """Verify hash chain integrity using explicit pagination to prevent OOM."""
    from backend.app.models.audit_log import AuditLog
    expected_prev = "GENESIS"
    last_id = 0
    chunk_size = 5000

    while True:
        rows = db.query(AuditLog).filter(AuditLog.id > last_id).order_by(AuditLog.id).limit(chunk_size).all()
        if not rows:
            break

        for row in rows:
            canonical = canonical_json({
                "action": row.action,
                "entity_type": row.entity_type,
                "entity_id": str(row.entity_id) if row.entity_id else None,
                "before": row.before_value,
                "after": row.after_value,
                "occurred_at": row.occurred_at.isoformat() if row.occurred_at else None,
            })
            expected_hash = sha256_hex(canonical + expected_prev)
            if expected_hash != row.record_hash:
                return False, row.id
            expected_prev = row.record_hash
            last_id = row.id

    return True, None
