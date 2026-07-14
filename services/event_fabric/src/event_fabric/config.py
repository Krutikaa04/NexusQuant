"""Runtime configuration for the Event Fabric (SPEC-005 §9, §11)."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = Field(default="development")
    service_name: str = Field(default="event_fabric")

    # Persistence. Defaults to an in-memory SQLite DB so the service and its tests run
    # with zero external infrastructure; production supplies an async Postgres DSN.
    database_url: str = Field(
        default="sqlite+aiosqlite:///:memory:", alias="EVENT_FABRIC_DATABASE_URL"
    )

    # Security (SPEC-005 §11)
    jwt_secret: str = Field(default="change-me-in-production")
    jwt_algorithm: str = Field(default="HS256")
    event_signing_key: str = Field(default="change-me-in-production")
    auth_enabled: bool = Field(default=True)

    # Fabric knobs (SPEC-005 §9)
    event_retention_days: int = Field(default=365, ge=1)
    max_retry_count: int = Field(default=5, ge=0)
    websocket_heartbeat: int = Field(default=30, ge=1)
    replay_batch_size: int = Field(default=500, ge=1)

    # Schema policy: when False, unregistered event types pass through unvalidated
    # (useful before every context has declared its payload schemas).
    strict_schema_validation: bool = Field(default=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
