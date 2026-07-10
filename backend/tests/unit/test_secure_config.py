"""Production configuration must fail closed on insecure infrastructure."""

import pytest
from pydantic import ValidationError

from app.config import Settings


def production_settings(**overrides):
    values = {
        "ENVIRONMENT": "production",
        "DATABASE_URL": "postgresql+asyncpg://gennomx_app:secret@db.example/gennomx?ssl=require",
        "WORKER_DATABASE_URL": "postgresql+asyncpg://gennomx_worker:secret@db.example/gennomx?ssl=require",
        "DATABASE_URL_SYNC": "postgresql://gennomx_migrator:secret@db.example/gennomx?sslmode=require",
        "REDIS_URL": "rediss://:secret@redis.example/0",
        "CELERY_BROKER_URL": "rediss://:secret@redis.example/0",
        "CELERY_RESULT_BACKEND": "rediss://:secret@redis.example/1",
        "SUPABASE_URL": "https://project.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "service-secret",
        "SUPABASE_JWKS_URL": "https://project.supabase.co/auth/v1/.well-known/jwks.json",
        "SUPABASE_JWT_SECRET": "jwt-secret",
        "API_INTERNAL_KEY": "internal-secret",
        "ROOT_PATH": "/api/ai",
        "MCP_TOKEN_CHATGPT": "mcp-secret",
        "CORS_ORIGINS": "https://app.gennomx.example",
        "API_ALLOWED_HOSTS": "api.gennomx.example,*.gennomx.example",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


@pytest.mark.unit
def test_secure_production_configuration_is_accepted():
    settings = production_settings()
    assert settings.is_production


@pytest.mark.unit
def test_secure_production_configuration_accepts_supabase_pooler_usernames():
    settings = production_settings(
        DATABASE_URL=(
            "postgresql+asyncpg://gennomx_app.project-ref:secret@pooler.supabase.com/postgres"
            "?ssl=require"
        ),
        WORKER_DATABASE_URL=(
            "postgresql+asyncpg://gennomx_worker.project-ref:secret@pooler.supabase.com/postgres"
            "?ssl=require"
        ),
    )
    assert settings.is_production


@pytest.mark.unit
@pytest.mark.parametrize("role", ["postgres", "service_role", "app"])
def test_production_rejects_unapproved_database_role(role):
    with pytest.raises(ValidationError):
        production_settings(
            DATABASE_URL=f"postgresql+asyncpg://{role}:secret@db.example/gennomx?ssl=require"
        )


@pytest.mark.unit
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("DATABASE_URL", "postgresql+asyncpg://app:secret@db.example/gennomx"),
        ("REDIS_URL", "redis://:secret@redis.example/0"),
        ("STORAGE_BACKEND", "s3"),
    ],
)
def test_insecure_production_infrastructure_is_rejected(field, value):
    with pytest.raises(ValidationError):
        production_settings(**{field: value})


@pytest.mark.unit
def test_production_requires_jwks_url():
    with pytest.raises(ValidationError):
        production_settings(SUPABASE_JWKS_URL="")


@pytest.mark.unit
def test_production_rejects_wildcard_api_allowed_hosts():
    with pytest.raises(ValidationError):
        production_settings(API_ALLOWED_HOSTS="*")


@pytest.mark.unit
def test_api_allowed_hosts_are_parsed_as_csv():
    settings = production_settings(API_ALLOWED_HOSTS="api.gennomx.example, mcp.gennomx.example")
    assert settings.api_allowed_hosts_list == ["api.gennomx.example", "mcp.gennomx.example"]

@pytest.mark.unit
def test_vps_database_provider_rejects_supabase_database_urls():
    with pytest.raises(ValidationError):
        production_settings(
            DATABASE_PROVIDER="vps_postgres",
            DATABASE_URL=(
                "postgresql+asyncpg://gennomx_app.project-ref:secret@pooler.supabase.com/postgres"
                "?ssl=require"
            ),
            WORKER_DATABASE_URL=(
                "postgresql+asyncpg://gennomx_worker.project-ref:secret@pooler.supabase.com/postgres"
                "?ssl=require"
            ),
            DATABASE_URL_SYNC=(
                "postgresql://gennomx_migrator:secret@db.project-ref.supabase.co/postgres"
                "?sslmode=require"
            ),
        )
