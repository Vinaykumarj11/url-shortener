from fastapi import Depends, HTTPException, Request, status
from redis import Redis

from app.cache import get_redis
from app.config import Settings, get_settings


def rate_limit(
    request: Request,
    r: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> None:
    """Fixed-window limiter: N requests per client IP per window."""
    client = request.client.host if request.client else "unknown"
    key = f"ratelimit:{client}"

    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expire(key, settings.rate_limit_window_seconds, nx=True)
    count, _ = pipe.execute()

    if count > settings.rate_limit_requests:
        retry_after = max(r.ttl(key), 1)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )
