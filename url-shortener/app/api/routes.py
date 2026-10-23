from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from redis import Redis
from sqlalchemy.orm import Session

from app import cache, service
from app.cache import get_redis
from app.config import Settings, get_settings
from app.db import get_db
from app.models import Link
from app.rate_limit import rate_limit
from app.schemas import LinkCreate, LinkOut

router = APIRouter()


def to_out(link: Link, settings: Settings) -> LinkOut:
    return LinkOut(
        code=link.code,
        short_url=f"{settings.base_url.rstrip('/')}/{link.code}",
        target_url=link.target_url,
        clicks=link.clicks,
        created_at=link.created_at,
        expires_at=link.expires_at,
    )


def get_active_link(code: str, db: Session = Depends(get_db)) -> Link:
    link = service.get_link(db, code)
    if link is None or link.is_expired():
        raise HTTPException(status_code=404, detail="Link not found")
    return link


@router.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post(
    "/api/v1/links",
    response_model=LinkOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit)],
    tags=["links"],
)
def create_link(
    data: LinkCreate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> LinkOut:
    try:
        link = service.create_link(db, data, settings.code_length)
    except service.CodeTakenError:
        raise HTTPException(status_code=409, detail="Custom code already in use") from None
    return to_out(link, settings)


@router.get("/api/v1/links/{code}", response_model=LinkOut, tags=["links"])
def link_stats(
    link: Link = Depends(get_active_link), settings: Settings = Depends(get_settings)
) -> LinkOut:
    return to_out(link, settings)


@router.delete("/api/v1/links/{code}", status_code=status.HTTP_204_NO_CONTENT, tags=["links"])
def delete_link(
    link: Link = Depends(get_active_link),
    db: Session = Depends(get_db),
    r: Redis = Depends(get_redis),
) -> Response:
    cache.evict(r, link.code)
    service.delete_link(db, link)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{code}", tags=["redirect"])
def redirect(
    code: str,
    db: Session = Depends(get_db),
    r: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    target = cache.get_cached_target(r, code)
    if target is None:
        link = get_active_link(code, db)
        target = link.target_url
        ttl = settings.cache_ttl_seconds
        left = link.seconds_left()
        if left is not None:
            # Never cache past the link's expiry.
            ttl = max(1, min(ttl, int(left)))
        cache.cache_target(r, code, target, ttl)

    service.record_click(db, code)
    return RedirectResponse(target, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
