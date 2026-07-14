"""Data Platform configuration (SPEC-006 §9)."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = Field(default="development")
    service_name: str = Field(default="data_platform")

    database_url: str = Field(
        default="sqlite+aiosqlite:///:memory:", alias="DATA_PLATFORM_DATABASE_URL"
    )
    redis_url: str | None = Field(default=None)  # None => in-memory cache

    # SPEC-006 §9 knobs
    db_pool_size: int = Field(default=10, ge=1)
    cache_ttl: int = Field(default=300, ge=1)
    query_timeout: int = Field(default=30, ge=1)

    # Where this service publishes its own events (the Event Fabric ingress). When unset,
    # an in-memory publisher is used (tests / offline development).
    event_fabric_url: str | None = Field(default=None)

    auth_enabled: bool = Field(default=True)
    jwt_secret: str = Field(default="change-me-in-production")
    jwt_algorithm: str = Field(default="HS256")


@lru_cache
def get_settings() -> Settings:
    return Settings()
