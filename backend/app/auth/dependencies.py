import secrets
from typing import Annotated

import jwt
from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.platform import PlatformTokenError, verify_platform_token
from app.config import get_settings
from app.core.exceptions import unauthorized_exception

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)

AI_READ = "ai:read"
AI_CURATE = "ai:curate"
AI_INGEST_DRY_RUN = "ai:ingest:dry_run"
AI_INGEST_RUN = "ai:ingest:run"
AI_SECURITY = "ai:security"
AI_ADMIN = "ai:admin"


class CurrentUser:
    def __init__(
        self,
        user_id: str,
        email: str,
        role: str,
        is_service: bool = False,
        *,
        auth_source: str = "local_jwt",
        platform_subject: str | None = None,
        tenant_id: str | None = None,
        scopes: tuple[str, ...] = (),
    ) -> None:
        self.user_id = user_id
        self.email = email
        self.role = role
        self.is_service = is_service
        self.auth_source = auth_source
        self.platform_subject = platform_subject
        self.tenant_id = tenant_id
        self.scopes = scopes

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


def _decode_auth_jwt(token: str) -> dict:
    if not settings.AUTH_JWT_SECRET:
        raise jwt.InvalidTokenError("Authentication secret is not configured")

    return jwt.decode(
        token,
        settings.AUTH_JWT_SECRET,
        algorithms=[settings.AUTH_JWT_ALGORITHM],
        audience=settings.AUTH_JWT_AUDIENCE,
        issuer=settings.AUTH_JWT_ISSUER or None,
        options={"verify_iss": bool(settings.AUTH_JWT_ISSUER)},
    )


def _local_user(token: str) -> CurrentUser:
    payload = _decode_auth_jwt(token)
    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise jwt.InvalidTokenError("Invalid token subject")
    return CurrentUser(
        user_id=user_id,
        email=payload.get("email", ""),
        role=payload.get("role", "readonly"),
        auth_source="local_jwt",
    )


def _platform_user(token: str) -> CurrentUser:
    principal = verify_platform_token(token)
    return CurrentUser(
        user_id=principal.subject,
        email=principal.email,
        role="admin",
        auth_source="platform",
        platform_subject=principal.subject,
        tenant_id=principal.tenant_id,
        scopes=principal.scopes,
    )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    platform_cookie: Annotated[str | None, Cookie(alias=settings.PLATFORM_AUTH_COOKIE_NAME)] = None,
) -> CurrentUser:
    token = credentials.credentials if credentials else None
    if (
        token
        and settings.API_INTERNAL_KEY
        and secrets.compare_digest(token, settings.API_INTERNAL_KEY)
    ):
        return CurrentUser(
            user_id="service",
            email="service@gennomx.internal",
            role="service",
            is_service=True,
            auth_source="internal_key",
        )

    if token:
        try:
            return _local_user(token)
        except jwt.PyJWTError:
            pass

    platform_token = token or platform_cookie
    if settings.PLATFORM_AUTH_ENABLED and platform_token:
        try:
            return _platform_user(platform_token)
        except PlatformTokenError:
            pass

    raise unauthorized_exception("Invalid or expired token")


def authorize_action(user: CurrentUser, required_scope: str, *, local_admin: bool) -> CurrentUser:
    if user.auth_source == "platform":
        if required_scope in user.scopes or AI_ADMIN in user.scopes:
            return user
    elif local_admin:
        if user.is_admin:
            return user
    else:
        return user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"code": "FORBIDDEN", "message": f"Scope {required_scope} required"},
    )


async def require_read(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
    return authorize_action(user, AI_READ, local_admin=False)


async def require_curate(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
    return authorize_action(user, AI_CURATE, local_admin=True)


async def require_ingest_run(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    return authorize_action(user, AI_INGEST_RUN, local_admin=True)


async def require_security(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
    return authorize_action(user, AI_SECURITY, local_admin=True)


async def require_admin(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
    return authorize_action(user, AI_ADMIN, local_admin=True)
