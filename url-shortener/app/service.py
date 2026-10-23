from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.codes import generate_code
from app.models import Link
from app.schemas import LinkCreate

MAX_ATTEMPTS = 5


class CodeTakenError(Exception):
    pass


def create_link(db: Session, data: LinkCreate, code_length: int) -> Link:
    if data.custom_code:
        return _insert(db, data, data.custom_code)

    for _ in range(MAX_ATTEMPTS):
        try:
            return _insert(db, data, generate_code(code_length))
        except CodeTakenError:
            continue
    raise RuntimeError("Could not allocate a unique code")


def _insert(db: Session, data: LinkCreate, code: str) -> Link:
    link = Link(code=code, target_url=str(data.url), expires_at=data.expires_at)
    db.add(link)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise CodeTakenError(code) from exc
    db.refresh(link)
    return link


def get_link(db: Session, code: str) -> Link | None:
    return db.scalar(select(Link).where(Link.code == code))


def record_click(db: Session, code: str) -> None:
    # Atomic increment in SQL avoids lost updates under concurrent redirects.
    db.execute(update(Link).where(Link.code == code).values(clicks=Link.clicks + 1))
    db.commit()


def delete_link(db: Session, link: Link) -> None:
    db.delete(link)
    db.commit()
