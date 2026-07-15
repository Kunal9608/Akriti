"""
Security utilities: password hashing, JWT encode/decode, OTP generation.
"""
import os
import random
import string
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Dict

import jwt
from jwt.exceptions import PyJWTError as JWTError
import bcrypt

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))
from backend.app.config import settings


def hash_password(plain: str) -> str:
    pw_bytes = plain.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pw_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    pw_bytes = plain.encode('utf-8')
    hashed_bytes = hashed.encode('utf-8')
    try:
        return bcrypt.checkpw(pw_bytes, hashed_bytes)
    except Exception:
        return False


def create_access_token(user_id: str, role: str, session_id: Optional[str] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
        "type": "access",
    }
    if session_id:
        payload["sid"] = str(session_id)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    import uuid
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_REFRESH_EXPIRE_HOURS)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "jti": str(uuid.uuid4()),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_short_lived_token(user_id: str, purpose: str = "password_reset", minutes: int = 10) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "purpose": purpose,
        "type": "short",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """Raises JWTError if invalid or expired."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def generate_otp(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()


def verify_otp(plain: str, hashed: str) -> bool:
    return hmac.compare_digest(hashlib.sha256(plain.encode()).hexdigest(), hashed)


def hash_token(token: str) -> str:
    """Used to store refresh tokens hashed (never raw)."""
    return hashlib.sha256(token.encode()).hexdigest()


def sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def canonical_json(data: dict) -> str:
    """Stable JSON serialization for hash-chaining."""
    return json.dumps(data, sort_keys=True, default=str, ensure_ascii=True)


def validate_password_policy(password: str) -> bool:
    """FR-1.4: min 6 chars, max 13 chars, at least one letter and one digit, alphanumeric only."""
    import re
    pattern = r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z0-9]{6,13}$"
    return bool(re.match(pattern, password))
