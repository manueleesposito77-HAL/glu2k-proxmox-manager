import redis
import json
import hashlib
import logging
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_redis = None

def get_redis():
    global _redis
    if _redis is None:
        try:
            _redis = redis.from_url(settings.REDIS_URL, decode_responses=True, socket_timeout=2)
            _redis.ping()
            logger.info("Redis cache connected")
        except Exception as e:
            logger.warning(f"Redis unavailable, cache disabled: {e}")
            _redis = None
    return _redis


def cache_key(prefix: str, *args, **kwargs) -> str:
    raw = f"{prefix}:{':'.join(str(a) for a in args)}:{json.dumps(kwargs, sort_keys=True)}"
    return f"pxc:{hashlib.md5(raw.encode()).hexdigest()[:16]}:{prefix}"


def cache_get(key: str):
    r = get_redis()
    if not r:
        return None
    try:
        val = r.get(key)
        if val:
            return json.loads(val)
    except Exception:
        pass
    return None


def cache_set(key: str, value, ttl: int = 10):
    r = get_redis()
    if not r:
        return
    try:
        r.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        pass


def cached(prefix: str, ttl: int = 10):
    """Decorator per cachare il risultato di una funzione."""
    def decorator(fn):
        def wrapper(*args, **kwargs):
            key = cache_key(prefix, *args, **kwargs)
            hit = cache_get(key)
            if hit is not None:
                return hit
            result = fn(*args, **kwargs)
            cache_set(key, result, ttl)
            return result
        wrapper.__name__ = fn.__name__
        return wrapper
    return decorator
