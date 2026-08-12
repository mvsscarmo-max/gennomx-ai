import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field

from app.auth.dependencies import CurrentUser, get_current_user
from app.config import get_settings

router = APIRouter()
settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class LoginUser(BaseModel):
    email: str
    role: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: LoginUser


def _password_matches(candidate: str) -> bool:
    if settings.AUTH_ADMIN_PASSWORD_HASH:
        try:
            return pwd_context.verify(candidate, settings.AUTH_ADMIN_PASSWORD_HASH)
        except Exception:
            return False
    if settings.AUTH_ADMIN_PASSWORD:
        return secrets.compare_digest(candidate, settings.AUTH_ADMIN_PASSWORD)
    return False


def _issue_access_token(*, email: str, role: str = "admin") -> tuple[str, int]:
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": email,
        "email": email,
        "role": role,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "iss": settings.AUTH_JWT_ISSUER,
        "aud": settings.AUTH_JWT_AUDIENCE,
    }
    token = jwt.encode(payload, settings.AUTH_JWT_SECRET, algorithm=settings.AUTH_JWT_ALGORITHM)
    return token, int((expires_at - now).total_seconds())


@router.post("/login", summary="Authenticate the internal admin user")
async def login(payload: LoginRequest) -> LoginResponse:
    if not settings.AUTH_ADMIN_EMAIL or not settings.AUTH_JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured",
        )
    if payload.email.lower() != settings.AUTH_ADMIN_EMAIL.lower() or not _password_matches(
        payload.password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas",
        )
    token, expires_in = _issue_access_token(email=settings.AUTH_ADMIN_EMAIL, role="admin")
    return LoginResponse(
        access_token=token,
        expires_in=expires_in,
        user=LoginUser(email=settings.AUTH_ADMIN_EMAIL, role="admin"),
    )


@router.get("/me", summary="Inspect the authenticated user")
async def me(user: Annotated[CurrentUser, Depends(get_current_user)]) -> dict:
    return {
        "success": True,
        "data": {
            "user_id": user.user_id,
            "email": user.email,
            "role": user.role,
            "is_service": user.is_service,
            "auth_source": user.auth_source,
            "platform_subject": user.platform_subject,
            "tenant_id": user.tenant_id,
            "scopes": list(user.scopes),
        },
    }
