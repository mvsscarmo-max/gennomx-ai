import pytest

from app.db_url import coerce_database_url


@pytest.mark.unit
def test_supabase_sync_url_is_coerced_for_asyncpg():
    url = (
        "postgresql://gennomx_app:secret@aws-0-us-east-1.pooler.supabase.com:6543/"
        "postgres?sslmode=require"
    )

    assert coerce_database_url(url, async_driver=True) == (
        "postgresql+asyncpg://gennomx_app:secret@aws-0-us-east-1.pooler.supabase.com:6543/"
        "postgres?ssl=require"
    )


@pytest.mark.unit
def test_asyncpg_url_is_coerced_for_alembic_psycopg():
    url = "postgresql+asyncpg://gennomx_migrator:secret@db.example/postgres?ssl=require"

    assert coerce_database_url(url, async_driver=False) == (
        "postgresql://gennomx_migrator:secret@db.example/postgres?sslmode=require"
    )


@pytest.mark.unit
def test_existing_driver_and_tls_query_are_preserved():
    url = "postgresql+asyncpg://gennomx_app:secret@db.example/postgres?ssl=require"

    assert coerce_database_url(url, async_driver=True) == url
