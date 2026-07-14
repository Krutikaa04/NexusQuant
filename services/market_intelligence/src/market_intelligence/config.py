"""Market Intelligence configuration (SPEC-004 performance/reliability knobs)."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = Field(default="development")
    service_name: str = Field(default="market_intelligence")

    database_url: str = Field(
        default="sqlite+aiosqlite:///:memory:", alias="MARKET_DATABASE_URL"
    )
    redis_url: str | None = Field(default=None)
    db_pool_size: int = Field(default=10, ge=1)
    cache_ttl: int = Field(default=60, ge=1)

    event_fabric_url: str | None = Field(default=None)  # None => in-memory publisher

    # Data-quality thresholds (SPEC-004 Data Quality Engine)
    dq_max_timestamp_drift_ms: int = Field(default=5000, ge=0)
    dq_ready_threshold: float = Field(default=0.90, ge=0, le=1)
    dq_degraded_threshold: float = Field(default=0.60, ge=0, le=1)
    dq_window_size: int = Field(default=100, ge=1)

    # Default candle interval produced by the aggregator, in seconds (60 = 1-minute).
    default_candle_interval_seconds: int = Field(default=60, ge=1)

    auth_enabled: bool = Field(default=True)
    jwt_secret: str = Field(default="change-me-in-production")
    jwt_algorithm: str = Field(default="HS256")


@lru_cache
def get_settings() -> Settings:
    return Settings()
