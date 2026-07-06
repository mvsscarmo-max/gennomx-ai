import secrets
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from app.config import get_settings
from app.core.exceptions import unauthorized_exception

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser:
    def __init__(self, user_id: str, email: str, role: str, is_service: bool = False) -> None:
        self.user_id = user_id
        self.email = email
        self.role = role
        self.is_service = is_service

    @property
    def is_admin(self) -> bool:
        return self.role in ("admin",)


def _supabase_issuer() -> str | None:
    return settings.SUPABASE_JWT_ISSUER or (
        f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1" if settings.SUPABASE_URL else None
    )


def _supabase_jwks_url() -> str:
    return settings.SUPABASE_JWKS_URL or (
        f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
        if settings.SUPABASE_URL
        else ""
    )


@lru_cache
def _jwks_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url, cache_keys=True)


def _decode_supabase_jwt(token: str) -> dict:
    import jwt
    from jwt.types import Options

    issuer = _supabase_issuer()
    jwks_url = _supabase_jwks_url()
    decode_options: Options = {"verify_iss": bool(issuer)}
    if jwks_url:
        signing_key = _jwks_client(jwks_url).get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256"],
            audience=settings.SUPABASE_JWT_AUDIENCE,
            issuer=issuer,
            options=decode_options,
        )
    return jwt.decode(
        token,
        settings.SUPABASE_JWT_SECRET,
        algorithms=["HS256"],
        audience=settings.SUPABASE_JWT_AUDIENCE,
        issuer=issuer,
        options=decode_options,
    )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> CurrentUser:
    if not credentials:
        raise unauthorized_exception()

    token = credentials.credentials

    if settings.API_INTERNAL_KEY and secrets.compare_digest(token, settings.API_INTERNAL_KEY):
        return CurrentUser(
            user_id="service",
            email="service@gennomx.internal",
            role="service",
            is_service=True,
        )

    try:
        payload = _decode_supabase_jwt(token)
        user_id = payload.get("sub")
        email = payload.get("email", "")
        app_metadata = payload.get("app_metadata") or {}
        role = app_metadata.get("gennomx_role", "readonly")

        if not user_id:
            raise unauthorized_exception("Invalid token payload")

        return CurrentUser(user_id=user_id, email=email, role=role)

    except Exception as exc:
        raise unauthorized_exception("Invalid or expired token") from exc


async def require_admin(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Admin role required"},
        )
    return user
