"""Authentication and authorization helpers (SPEC-005 §11).

Access to every REST mutation and WebSocket channel requires a valid JWT. Verification is
intentionally minimal and stateless (HS256, shared secret) — RBAC claims are read from the
token's ``roles`` claim. In development ``auth_enabled`` may be disabled so the fabric can
run without an identity provider.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header, HTTPException, Request, status
from jose import JWTError, jwt

from event_fabric.config import Settings


@dataclass(frozen=True, slots=True)
class Principal:
    subject: str
    roles: frozenset[str]

    def require_role(self, role: str) -> None:
        if role not in self.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=f"role '{role}' required"
            )


ANONYMOUS = Principal(subject="anonymous", roles=frozenset({"developer"}))


def decode_token(token: str, settings: Settings) -> Principal:
    try:
        claims = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:  # noqa: TRY003
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token"
        ) from exc
    roles = claims.get("roles", [])
    return Principal(subject=str(claims.get("sub", "unknown")), roles=frozenset(roles))


def _extract_bearer(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token"
        )
    return authorization.split(" ", 1)[1].strip()


def require_principal(
    request: Request,
    authorization: str | None = Header(default=None),
) -> Principal:
    """FastAPI dependency resolving the calling principal from the ``Authorization`` header.

    Reads the active settings from the app's container so that a test/instance-specific
    configuration (e.g. ``auth_enabled=False``) is honoured rather than a process global.
    """
    settings: Settings = request.app.state.container.settings
    if not settings.auth_enabled:
        return ANONYMOUS
    return decode_token(_extract_bearer(authorization), settings)


def authenticate_ws_token(token: str | None, settings: Settings) -> Principal:
    """Resolve a principal for a WebSocket connection from a query-string ``token``."""
    if not settings.auth_enabled:
        return ANONYMOUS
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token required")
    return decode_token(token, settings)
