"""Strategy Core configuration."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = Field(default="development")
    service_name: str = Field(default="strategy_core")

    database_url: str = Field(
        default="sqlite+aiosqlite:///:memory:", alias="STRATEGY_DATABASE_URL"
    )
    db_pool_size: int = Field(default=10, ge=1)

    max_strategies: int = Field(default=1000, ge=1)
    default_category: str = Field(default="uncategorized")

    auth_enabled: bool = Field(default=True)
    jwt_secret: str = Field(default="change-me-in-production")
    jwt_algorithm: str = Field(default="HS256")


@lru_cache
def get_settings() -> Settings:
    return Settings()
