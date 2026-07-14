"""A minimal ``Result`` type for explicit, non-exceptional success/failure flows.

Used at context boundaries where failure is an expected outcome (e.g. schema
validation, idempotency rejection) rather than an exceptional one.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")


@dataclass(frozen=True, slots=True)
class Ok(Generic[T]):
    value: T

    @property
    def is_ok(self) -> bool:
        return True


@dataclass(frozen=True, slots=True)
class Err(Generic[E]):
    error: E

    @property
    def is_ok(self) -> bool:
        return False


Result = Ok[T] | Err[E]
