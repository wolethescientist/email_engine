from redis import Redis
from ..core.config import get_settings

_redis = None


def get_redis() -> Redis:
    global _redis
    if _redis is None:
        settings = get_settings()
        _redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis