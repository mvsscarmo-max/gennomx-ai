"""Integration test fixtures — requires a real PostgreSQL instance.

Set DATABASE_URL_SYNC and DATABASE_URL env vars pointing to a test database.
Use `make up` to start the local database before running integration tests.
"""

import os

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://gennomx:gennomx@localhost:5432/gennomx_test",
)


@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(DATABASE_URL, echo=False)
    yield engine
    await engine.dispose()


@pytest.fixture
async def test_db(test_engine):
    session_local = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_local() as session:
        yield session
        await session.rollback()
