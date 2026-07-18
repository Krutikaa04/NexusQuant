"""Domain errors for the Strategy context. Mapped to HTTP status codes at the API edge."""

from __future__ import annotations


class StrategyError(Exception):
    """Base class for all strategy-domain errors."""


class StrategyNotFound(StrategyError):
    """No strategy (or version) exists for the given identifier."""


class IllegalTransition(StrategyError):
    """A requested lifecycle transition is not permitted from the current state."""


class ImmutableStrategy(StrategyError):
    """The strategy is retired or deleted and may not be modified."""


class ValidationError(StrategyError):
    """A domain invariant was violated (e.g. empty name, unknown version)."""
