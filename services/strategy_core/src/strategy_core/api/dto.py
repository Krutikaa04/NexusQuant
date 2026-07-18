"""Request/response DTOs for the Strategy API. All request bodies are validated here."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from strategy_core.domain.models import StrategyConfig


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
    migrations_applied: list[str]


class CreateStrategyBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=4000)
    category: str | None = Field(default=None, max_length=64)
    owner: str = Field(default="unknown", max_length=120)
    tags: list[str] = Field(default_factory=list)
    config: StrategyConfig = Field(default_factory=StrategyConfig)


class UpdateStrategyBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    category: str | None = Field(default=None, max_length=64)
    tags: list[str] | None = Field(default=None)
    config: StrategyConfig | None = Field(default=None)
    change_summary: str = Field(default="", max_length=280)


class TransitionBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    to_status: str = Field(min_length=1)
    reason: str = Field(default="", max_length=280)


class RollbackBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = Field(ge=1)


class CloneBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=160)
