"""Redis client — with fallback to None if Redis is unavailable."""
import os
import sys

_redis_client = None
_redis_failed = False

def get_redis():
    global _redis_client, _redis_failed
    if _redis_failed:
        return None
    if _redis_client is not None:
        return _redis_client
    try:
        import redis
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))
        from backend.app.config import settings
        r = redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=0.5)
        r.ping()
        _redis_client = r
        return r
    except Exception:
        _redis_failed = True
        return None
