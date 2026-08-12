import os
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

os.environ.setdefault("STORAGE_BACKEND", "minio")
os.environ.setdefault("MINIO_ENDPOINT_URL", "http://minio:9000")
os.environ.setdefault("MINIO_ACCESS_KEY_ID", "test-minio-access")
os.environ.setdefault("MINIO_SECRET_ACCESS_KEY", "test-minio-secret")

from app.auth import dependencies
from app.auth.dependencies import CurrentUser


@pytest.mark.unit
async def test_internal_key_is_service_not_admin(monkeypatch):
    monkeypatch.setattr(dependencies.settings, "API_INTERNAL_KEY", "internal-secret")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="internal-secret")
    user = await dependencies.get_current_user(credentials)
    assert user.is_service
    assert user.role == "service"
    assert not user.is_admin
    assert user.auth_source == "internal_key"


@pytest.mark.unit
async def test_auth_jwt_is_decoded_with_local_secret(monkeypatch):
    monkeypatch.setattr(
        dependencies.settings, "AUTH_JWT_SECRET", "jwt-secret-32-chars-minimum!!!!!"
    )
    monkeypatch.setattr(dependencies.settings, "AUTH_JWT_ALGORITHM", "HS256")
    monkeypatch.setattr(dependencies.settings, "AUTH_JWT_AUDIENCE", "gennomx-dashboard")
    monkeypatch.setattr(dependencies.settings, "AUTH_JWT_ISSUER", "gennomx-ai")

    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": "user-1",
            "email": "admin@example.com",
            "role": "admin",
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
            "iss": "gennomx-ai",
            "aud": "gennomx-dashboard",
        },
        "jwt-secret-32-chars-minimum!!!!!",
        algorithm="HS256",
    )

    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    user = await dependencies.get_current_user(credentials)

    assert user.user_id == "user-1"
    assert user.email == "admin@example.com"
    assert user.role == "admin"
    assert not user.is_service
    assert user.auth_source == "local_jwt"


@pytest.mark.unit
async def test_readonly_user_is_rejected_by_require_admin():
    user = CurrentUser(user_id="user-1", email="reader@example.com", role="readonly")

    with pytest.raises(HTTPException) as exc_info:
        await dependencies.require_admin(user)

    assert exc_info.value.status_code == 403


@pytest.mark.unit
async def test_platform_token_is_rejected_while_feature_flag_is_off(monkeypatch):
    monkeypatch.setattr(dependencies.settings, "PLATFORM_AUTH_ENABLED", False)
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="platform-looking-token"
    )

    with pytest.raises(HTTPException) as exc_info:
        await dependencies.get_current_user(credentials)

    assert exc_info.value.status_code == 401


@pytest.mark.unit
async def test_enabled_platform_cookie_builds_normalized_current_user(monkeypatch):
    monkeypatch.setattr(dependencies.settings, "PLATFORM_AUTH_ENABLED", True)
    monkeypatch.setattr(
        dependencies,
        "verify_platform_token",
        lambda token: SimpleNamespace(
            subject="platform-1",
            email="admin@gennomx.com",
            tenant_id="gennomx-internal",
            scopes=(dependencies.AI_READ,),
        ),
    )

    user = await dependencies.get_current_user(None, platform_cookie="platform-token")

    assert user.auth_source == "platform"
    assert user.platform_subject == "platform-1"
    assert user.tenant_id == "gennomx-internal"
    assert user.scopes == (dependencies.AI_READ,)


@pytest.mark.unit
async def test_platform_scope_mapping_does_not_grant_admin_implicitly():
    user = CurrentUser(
        user_id="platform-1",
        email="admin@gennomx.com",
        role="admin",
        auth_source="platform",
        platform_subject="platform-1",
        tenant_id="gennomx-internal",
        scopes=(dependencies.AI_READ,),
    )

    assert await dependencies.require_read(user) is user
    with pytest.raises(HTTPException) as exc_info:
        await dependencies.require_admin(user)
    assert exc_info.value.status_code == 403


@pytest.mark.unit
async def test_platform_admin_scope_satisfies_all_module_actions():
    user = CurrentUser(
        user_id="platform-1",
        email="admin@gennomx.com",
        role="admin",
        auth_source="platform",
        platform_subject="platform-1",
        tenant_id="gennomx-internal",
        scopes=(dependencies.AI_ADMIN,),
    )

    assert await dependencies.require_read(user) is user
    assert await dependencies.require_curate(user) is user
    assert await dependencies.require_ingest_run(user) is user
    assert await dependencies.require_security(user) is user
    assert await dependencies.require_admin(user) is user
