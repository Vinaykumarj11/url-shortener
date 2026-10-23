from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "url-shortener"
    base_url: str = "http://localhost:8000"
    database_url: str = "postgresql+psycopg://shortener:shortener@localhost:5432/shortener"
    redis_url: str = "redis://localhost:6379/0"

    code_length: int = 7
    cache_ttl_seconds: int = 3600
    rate_limit_requests: int = 20
    rate_limit_window_seconds: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
