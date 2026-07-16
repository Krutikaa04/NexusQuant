"""Typed domain errors, mapped to HTTP statuses at the API boundary."""

from __future__ import annotations


class NotFoundError(LookupError):
    """The referenced aggregate does not exist."""


class GovernanceError(PermissionError):
    """A business rule (SPEC-007 §8) forbids the requested operation."""


class ImmutableArtifactError(GovernanceError):
    """The artifact is frozen (project approved/retired) and cannot be modified."""
