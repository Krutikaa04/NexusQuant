"""Strategy configuration value object (versioned, immutable once written).

``StrategyConfig`` is the full, self-contained configuration snapshot captured in every
strategy version. It is normalized and validated here so the persisted JSON is always in a
canonical shape, independent of the API request that produced it.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StrategyConfig(BaseModel):
    """A complete, versioned strategy configuration."""

    model_config = ConfigDict(extra="forbid")

    symbols: list[str] = Field(default_factory=list)
    exchanges: list[str] = Field(default_factory=list)
    timeframes: list[str] = Field(default_factory=list)
    entry_params: dict[str, object] = Field(default_factory=dict)
    exit_params: dict[str, object] = Field(default_factory=dict)
    risk_params: dict[str, object] = Field(default_factory=dict)
    position_sizing: dict[str, object] = Field(default_factory=dict)
    trading_session: dict[str, object] = Field(default_factory=dict)

    def normalized(self) -> "StrategyConfig":
        """Return a copy with de-duplicated, order-preserving symbol/exchange/timeframe lists."""

        def dedup(items: list[str]) -> list[str]:
            seen: set[str] = set()
            out: list[str] = []
            for it in items:
                key = it.strip()
                if key and key not in seen:
                    seen.add(key)
                    out.append(key)
            return out

        return self.model_copy(
            update={
                "symbols": dedup(self.symbols),
                "exchanges": dedup(self.exchanges),
                "timeframes": dedup(self.timeframes),
            }
        )
