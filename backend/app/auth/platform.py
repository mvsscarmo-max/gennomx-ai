from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import jwt

from app.config import get_settings


class PlatformTokenError(ValueError):
    """Raised when an admin platform token is not valid for GennomX AI."""


@dataclass(frozen=True)
class PlatformPrincipal:
    subject: str
    email: str
    tenant_id: str
    apps: tuple[str, ...]
    scopes: tuple[str, ...]
    jti: str
    kind: str = "internal_admin"
    auth_source: str = "platform"


def _string(payload: dict[str, Any], claim: str) -> str:
    value = payload.get(claim)
    if not isinstance(value, str) or not value:
        raise PlatformTokenError(f"Platform token without valid {claim}.")
    return value


def _strings(payload: dict[str, Any], claim: str) -> tuple[str, ...]:
    value = payload.get(claim)
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(item, str) and item for item in value)
    ):
        raise PlatformTokenError(f"Platform token without valid {claim}.")
    return tuple(value)


def verify_platform_token(token: str, required_scopes: Iterable[str] = ()) -> PlatformPrincipal:
    """Verify the offline RS256 administrative contract for the AI module."""
    settings = get_settings()
    if not settings.PLATFORM_AUTH_PUBLIC_KEY:
        raise PlatformTokenError("Platform Auth public key is not configured.")

    try:
        header = jwt.get_unverified_header(token)
        if header.get("alg") != "RS256":
            raise PlatformTokenError("Platform token algorithm must be RS256.")
        payload = jwt.decode(
            token,
            settings.PLATFORM_AUTH_PUBLIC_KEY.replace("\\n", "\n"),
            algorithms=["RS256"],
            audience=settings.PLATFORM_AUTH_AUDIENCE,
            issuer=settings.PLATFORM_AUTH_ISSUER,
            options={
                "require": [
                    "exp",
                    "iat",
                    "jti",
                    "sub",
                    "email",
                    "kind",
                    "tenant_id",
                    "apps",
                    "scopes",
                ]
            },
        )
    except (jwt.PyJWTError, PlatformTokenError) as exc:
        raise PlatformTokenError("Invalid Platform Auth signature or registered claims.") from exc

    subject = _string(payload, "sub")
    email = _string(payload, "email")
    jti = _string(payload, "jti")
    tenant_id = _string(payload, "tenant_id")
    apps = _strings(payload, "apps")
    scopes = _strings(payload, "scopes")

    if payload.get("kind") != "internal_admin":
        raise PlatformTokenError("Platform token is not an internal admin session.")
    if tenant_id != settings.PLATFORM_AUTH_TENANT_ID:
        raise PlatformTokenError("Platform token tenant is not authorized.")
    if "ai" not in apps:
        raise PlatformTokenError("Platform token is not authorized for AI.")
    if any(scope not in scopes and "ai:admin" not in scopes for scope in required_scopes):
        raise PlatformTokenError("Platform token misses a required scope.")

    return PlatformPrincipal(subject, email, tenant_id, apps, scopes, jti)
