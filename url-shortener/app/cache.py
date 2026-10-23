from redis import Redis

from app.config import get_settings

_redis: Redis | None = None


def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(get_settings().redis_url, decode_responses=True)
    return _redis


def _key(code: str) -> str:
    return f"link:{code}"


def get_cached_target(r: Redis, code: str) -> str | None:
    return r.get(_key(code))


def cache_target(r: Redis, code: str, target: str, ttl: int) -> None:
    r.set(_key(code), target, ex=ttl)


def evict(r: Redis, code: str) -> None:
    r.delete(_key(code))
