"""Idempotency service — Redis-backed at-most-once execution."""
import json
from typing import Callable, Any, Optional

from backend.app.core.redis_client import get_redis

def with_idempotency(key: str, user_id: str, handler_fn: Callable, ttl: int = 86400) -> Any:
    """
    If we've seen this key before, return the stored response verbatim.
    Otherwise, execute handler_fn(), store result, and return it.
    """
    redis = get_redis()
    if not redis:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Service Unavailable: Redis is required for idempotent operations.")
        
    redis_key = f"idem:{key}:{user_id}"

    # Check cache and acquire lock
    cached = redis.get(redis_key)
    if cached:
        if cached == b"PENDING":
            from fastapi import HTTPException
            raise HTTPException(status_code=409, detail="Duplicate request is already processing.")
        return json.loads(cached)
        
    # Try to acquire lock
    acquired = redis.set(redis_key, "PENDING", nx=True, ex=30)
    if not acquired:
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail="Duplicate request is already processing.")

    # Execute the actual business logic
    result = handler_fn()

    # Serialize and store
    try:
        serialized = json.dumps(result, default=str)
        redis.set(redis_key, serialized, ex=ttl)
    except Exception:
        pass  # Non-fatal — the operation succeeded even if caching fails

    return result


def check_key_exists(key: str, user_id: str) -> Optional[Any]:
    """Returns stored result if key exists, else None."""
    redis = get_redis()
    if not redis:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Service Unavailable: Redis is required.")
        
    redis_key = f"idem:{key}:{user_id}"
    cached = redis.get(redis_key)
    if cached:
        return json.loads(cached)
    return None


def store_result(key: str, user_id: str, result: Any, ttl: int = 86400):
    redis = get_redis()
    if not redis:
        return
        
    redis_key = f"idem:{key}:{user_id}"
    try:
        serialized = json.dumps(result, default=str)
        redis.set(redis_key, serialized, ex=ttl)
    except Exception:
        pass

