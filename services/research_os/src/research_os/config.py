"""Research OS configuration (SPEC-007 §9)."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = Field(default="development")
    service_name: str = Field(default="research_os")

    database_url: str = Field(
        default="sqlite+aiosqlite:///:memory:", alias="RESEARCH_DATABASE_URL"
    )
    db_pool_size: int = Field(default=10, ge=1)

    event_fabric_url: str | None = Field(default=None)  # None => in-memory publisher

    # SPEC-007 §9 knobs
    max_projects_per_user: int = Field(default=25, ge=1)
    auto_archive_days: int = Field(default=180, ge=1)
    review_required: bool = Field(default=True)
    default_experiment_timeout: int = Field(default=3600, ge=1)

    auth_enabled: bool = Field(default=True)
    jwt_secret: str = Field(default="change-me-in-production")
    jwt_algorithm: str = Field(default="HS256")


@lru_cache
def get_settings() -> Settings:
    return Settings()
