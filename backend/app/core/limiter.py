from slowapi import Limiter
from backend.app.dependencies import get_client_ip
import os

redis_url = os.getenv("REDIS_URL")
use_redis = False

if redis_url:
    try:
        import redis
        r = redis.from_url(redis_url, socket_connect_timeout=0.5)
        r.ping()
        use_redis = True
    except Exception:
        pass

if use_redis:
    limiter = Limiter(key_func=get_client_ip, storage_uri=redis_url)
else:
    limiter = Limiter(key_func=get_client_ip)
