from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Link(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    target_url: Mapped[str] = mapped_column(Text)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def seconds_left(self) -> float | None:
        if self.expires_at is None:
            return None
        expires = self.expires_at
        if expires.tzinfo is None:  # SQLite drops tzinfo
            expires = expires.replace(tzinfo=UTC)
        return (expires - utcnow()).total_seconds()

    def is_expired(self) -> bool:
        left = self.seconds_left()
        return left is not None and left <= 0
