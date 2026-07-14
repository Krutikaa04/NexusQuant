"""JWT/RBAC dependency for the Data Platform API (SPEC-006 §11).

Mirrors the fabric's model: stateless HS256 verification, roles from the token, and a
development bypass via ``auth_enabled=False``. Reads settings from the app container so
per-instance configuration is honoured.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header, HTTPException, Request, status
from jose import JWTError, jwt

from data_platform.config import Settings


@dataclass(frozen=True, slots=True)
class Principal:
    subject: str
    roles: frozenset[str]


ANONYMOUS = Principal(subject="anonymous", roles=frozenset({"developer"}))


def require_principal(
    request: Request, authorization: str | None = Header(default=None)
) -> Principal:
    settings: Settings = request.app.state.container.settings
    if not settings.auth_enabled:
        return ANONYMOUS
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        claims = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid token") from exc
    return Principal(subject=str(claims.get("sub", "unknown")), roles=frozenset(claims.get("roles", [])))
