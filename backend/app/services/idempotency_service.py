"""Idempotency service — Redis-backed at-most-once execution."""
import json
from typing import Callable, Any, Optional

from backend.app.core.redis_client import get_redis

# Fallback in-memory store if Redis is unavailable (process-scoped, not distributed)
_fallback_store: dict = {}


def with_idempotency(key: str, user_id: str, handler_fn: Callable, ttl: int = 86400) -> Any:
    """
    If we've seen this key before, return the stored response verbatim.
    Otherwise, execute handler_fn(), store result, and return it.
    """
    redis = get_redis()
    redis_key = f"idem:{key}:{user_id}"

    # Check cache
    if redis:
        cached = redis.get(redis_key)
        if cached:
            return json.loads(cached)
    else:
        if redis_key in _fallback_store:
            return _fallback_store[redis_key]

    # Execute the actual business logic
    result = handler_fn()

    # Serialize and store
    try:
        serialized = json.dumps(result, default=str)
        if redis:
            redis.set(redis_key, serialized, ex=ttl)
        else:
            _fallback_store[redis_key] = result
    except Exception:
        pass  # Non-fatal — the operation succeeded even if caching fails

    return result


def check_key_exists(key: str, user_id: str) -> Optional[Any]:
    """Returns stored result if key exists, else None."""
    redis = get_redis()
    redis_key = f"idem:{key}:{user_id}"
    if redis:
        cached = redis.get(redis_key)
        if cached:
            return json.loads(cached)
    else:
        return _fallback_store.get(redis_key)
    return None


def store_result(key: str, user_id: str, result: Any, ttl: int = 86400):
    redis = get_redis()
    redis_key = f"idem:{key}:{user_id}"
    try:
        serialized = json.dumps(result, default=str)
        if redis:
            redis.set(redis_key, serialized, ex=ttl)
        else:
            _fallback_store[redis_key] = result
    except Exception:
        pass
