from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.auth import platform
from app.auth.platform import PlatformTokenError, verify_platform_token


@pytest.fixture
def platform_keys(monkeypatch):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    public_pem = (
        private_key.public_key()
        .public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )
    settings = SimpleNamespace(
        PLATFORM_AUTH_PUBLIC_KEY=public_pem,
        PLATFORM_AUTH_ISSUER="gennomx-platform",
        PLATFORM_AUTH_AUDIENCE="gennomx-admin",
        PLATFORM_AUTH_TENANT_ID="gennomx-internal",
    )
    monkeypatch.setattr(platform, "get_settings", lambda: settings)
    return private_pem


def issue(
    private_key,
    *,
    audience="gennomx-admin",
    tenant="gennomx-internal",
    scopes=None,
    algorithm="RS256",
    app="ai",
    kind="internal_admin",
):
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "iss": "gennomx-platform",
            "aud": audience,
            "sub": "platform-founder",
            "email": "admin@gennomx.com",
            "kind": kind,
            "tenant_id": tenant,
            "apps": [app],
            "scopes": scopes or ["ai:read"],
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "jti": "platform-test-jti",
        },
        private_key,
        algorithm=algorithm,
    )


@pytest.mark.unit
def test_platform_token_verifies_offline(platform_keys):
    principal = verify_platform_token(issue(platform_keys), ["ai:read"])
    assert principal.email == "admin@gennomx.com"
    assert principal.auth_source == "platform"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("audience", "tenant", "required_scope"),
    [
        ("ai-client", "gennomx-internal", "ai:read"),
        ("gennomx-admin", "client-tenant", "ai:read"),
        ("gennomx-admin", "gennomx-internal", "ai:admin"),
    ],
)
def test_platform_token_rejects_wrong_audience_tenant_or_scope(
    platform_keys, audience, tenant, required_scope
):
    with pytest.raises(PlatformTokenError):
        verify_platform_token(
            issue(platform_keys, audience=audience, tenant=tenant), [required_scope]
        )


@pytest.mark.unit
@pytest.mark.parametrize(
    ("app", "kind"),
    [("content", "internal_admin"), ("ai", "external_user")],
)
def test_platform_token_rejects_wrong_app_or_kind(platform_keys, app, kind):
    with pytest.raises(PlatformTokenError):
        verify_platform_token(issue(platform_keys, app=app, kind=kind))


@pytest.mark.unit
def test_ai_admin_satisfies_specific_scope(platform_keys):
    principal = verify_platform_token(issue(platform_keys, scopes=["ai:admin"]), ["ai:ingest:run"])
    assert principal.scopes == ("ai:admin",)
