"""Shared pytest fixtures."""

import asyncio
import os
from typing import Any
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# Settings are instantiated by application modules during test collection.
os.environ["STORAGE_BACKEND"] = "minio"


@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.DefaultEventLoopPolicy()


# ── DB mock ───────────────────────────────────────────────────────────────────


class FakeRow:
    """Behaves like a SQLAlchemy Row for index access."""

    def __init__(self, *values):
        self._values = values

    def __getitem__(self, idx):
        return self._values[idx]


class FakeResult:
    def __init__(self, rows: list, scalar_value: Any = 0):
        self._rows = rows
        self._scalar = scalar_value

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def scalar(self):
        return self._scalar


@pytest.fixture
def mock_db():
    """Async session mock. Configure .execute.return_value per test."""
    db = AsyncMock(spec=AsyncSession)
    return db


# ── Settings override ─────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def override_settings(monkeypatch):
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
    monkeypatch.setenv("AUTH_ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("AUTH_ADMIN_PASSWORD", "test-admin-password")
    monkeypatch.setenv("AUTH_JWT_SECRET", "test-jwt-secret-32-chars-minimum!!!")
    monkeypatch.setenv("MINIO_ENDPOINT_URL", "http://minio:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY_ID", "test-minio-access")
    monkeypatch.setenv("MINIO_SECRET_ACCESS_KEY", "test-minio-secret")
    monkeypatch.setenv("API_SECRET_KEY", "test-secret-key-32-chars-minimum!!")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("MCP_TOKEN_CHATGPT", "test-chatgpt-token")
    monkeypatch.setenv("MCP_TOKEN_CLAUDE", "test-claude-token")
    yield
    get_settings.cache_clear()
