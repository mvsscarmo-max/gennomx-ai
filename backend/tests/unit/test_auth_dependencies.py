import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

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


@pytest.mark.unit
async def test_supabase_jwt_uses_jwks_when_configured(monkeypatch):
    class FakeSigningKey:
        key = "public-key"

    class FakeJwksClient:
        def __init__(self, url, cache_keys=True):
            self.url = url
            self.cache_keys = cache_keys

        def get_signing_key_from_jwt(self, token):
            assert token == "jwt-token"
            return FakeSigningKey()

    decoded = {}

    def fake_decode(token, key, algorithms, audience, issuer, options):
        decoded.update(
            {
                "token": token,
                "key": key,
                "algorithms": algorithms,
                "audience": audience,
                "issuer": issuer,
                "options": options,
            }
        )
        return {
            "sub": "user-1",
            "email": "admin@example.com",
            "app_metadata": {"gennomx_role": "admin"},
        }

    dependencies._jwks_client.cache_clear()
    monkeypatch.setattr(dependencies.settings, "API_INTERNAL_KEY", "internal-secret")
    monkeypatch.setattr(dependencies.settings, "SUPABASE_URL", "https://project.supabase.co")
    monkeypatch.setattr(dependencies.settings, "SUPABASE_JWKS_URL", "")
    monkeypatch.setattr(dependencies.settings, "SUPABASE_JWT_AUDIENCE", "authenticated")
    monkeypatch.setattr(dependencies, "PyJWKClient", FakeJwksClient)
    monkeypatch.setattr("jwt.decode", fake_decode)

    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="jwt-token")
    user = await dependencies.get_current_user(credentials)

    assert user.user_id == "user-1"
    assert user.email == "admin@example.com"
    assert user.role == "admin"
    assert decoded == {
        "token": "jwt-token",
        "key": "public-key",
        "algorithms": ["ES256", "RS256"],
        "audience": "authenticated",
        "issuer": "https://project.supabase.co/auth/v1",
        "options": {"verify_iss": True},
    }


@pytest.mark.unit
async def test_readonly_user_is_rejected_by_require_admin():
    user = CurrentUser(user_id="user-1", email="reader@example.com", role="readonly")

    with pytest.raises(HTTPException) as exc_info:
        await dependencies.require_admin(user)

    assert exc_info.value.status_code == 403
