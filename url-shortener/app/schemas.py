from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class LinkCreate(BaseModel):
    url: HttpUrl
    custom_code: str | None = Field(
        default=None, min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_-]+$"
    )
    expires_at: datetime | None = None


class LinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    short_url: str
    target_url: str
    clicks: int
    created_at: datetime
    expires_at: datetime | None
