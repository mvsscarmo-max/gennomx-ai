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
        "AUTH_ADMIN_EMAIL": "admin@example.com",
        "AUTH_ADMIN_PASSWORD": "very-strong-admin-password",
        "AUTH_JWT_SECRET": "jwt-secret-32-chars-minimum!!!!!",
        "AUTH_JWT_ISSUER": "gennomx-ai",
        "AUTH_JWT_AUDIENCE": "gennomx-dashboard",
        "MINIO_ENDPOINT_URL": "http://minio.example:9000",
        "MINIO_ACCESS_KEY_ID": "minio-access",
        "MINIO_SECRET_ACCESS_KEY": "minio-secret",
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
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("AUTH_JWT_SECRET", ""),
        ("MINIO_ACCESS_KEY_ID", ""),
        ("MINIO_SECRET_ACCESS_KEY", ""),
    ],
)
def test_production_rejects_missing_security_inputs(field, value):
    with pytest.raises(ValidationError):
        production_settings(**{field: value})


@pytest.mark.unit
def test_production_rejects_weak_admin_password():
    with pytest.raises(ValidationError):
        production_settings(AUTH_ADMIN_PASSWORD="short")


@pytest.mark.unit
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("DATABASE_URL", "postgresql+asyncpg://app:secret@db.example/gennomx"),
        ("REDIS_URL", "redis://:secret@redis.example/0"),
        ("MINIO_ENDPOINT_URL", "minio.example:9000"),
    ],
)
def test_insecure_production_infrastructure_is_rejected(field, value):
    with pytest.raises(ValidationError):
        production_settings(**{field: value})


@pytest.mark.unit
def test_production_rejects_wildcard_api_allowed_hosts():
    with pytest.raises(ValidationError):
        production_settings(API_ALLOWED_HOSTS="*")


@pytest.mark.unit
def test_api_allowed_hosts_are_parsed_as_csv():
    settings = production_settings(API_ALLOWED_HOSTS="api.gennomx.example, mcp.gennomx.example")
    assert settings.api_allowed_hosts_list == ["api.gennomx.example", "mcp.gennomx.example"]
