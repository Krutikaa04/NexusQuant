"""JWT/RBAC dependency for the Strategy API (mirrors the platform security convention)."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header, HTTPException, Request, status
from jose import JWTError, jwt

from strategy_core.config import Settings


@dataclass(frozen=True, slots=True)
class Principal:
    subject: str
    roles: frozenset[str]


ANONYMOUS = Principal(subject="anonymous", roles=frozenset({"developer"}))


def require_principal(
    request: Request, authorization: str | None = Header(default=None)
) -> Principal:
    state = request.app.state
    container = getattr(state, "strategy_container", None) or state.container
    settings: Settings = container.settings
    if not settings.auth_enabled:
        return ANONYMOUS
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        claims = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid token") from exc
    return Principal(
        subject=str(claims.get("sub", "unknown")), roles=frozenset(claims.get("roles", []))
    )
