"""Readiness must fail closed when a required dependency is unavailable."""

from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app import main


@pytest.mark.unit
async def test_readiness_reports_database_and_redis(monkeypatch):
    monkeypatch.setattr(main, "_check_database", AsyncMock(return_value="ok"))
    monkeypatch.setattr(main, "_check_redis", AsyncMock(return_value="ok"))
    async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test") as client:
        response = await client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "checks": {"database": "ok", "redis": "ok"}}


@pytest.mark.unit
async def test_readiness_returns_503_if_redis_is_unavailable(monkeypatch):
    monkeypatch.setattr(main, "_check_database", AsyncMock(return_value="ok"))
    monkeypatch.setattr(main, "_check_redis", AsyncMock(return_value="unavailable"))
    async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test") as client:
        response = await client.get("/ready")

    assert response.status_code == 503
    assert response.json()["checks"]["redis"] == "unavailable"


@pytest.mark.unit
async def test_readiness_hides_component_detail_in_production(monkeypatch):
    monkeypatch.setattr(main, "_check_database", AsyncMock(return_value="ok"))
    monkeypatch.setattr(main, "_check_redis", AsyncMock(return_value="unavailable"))
    monkeypatch.setattr(main.settings, "ENVIRONMENT", "production")
    async with AsyncClient(transport=ASGITransport(app=main.app), base_url="http://test") as client:
        response = await client.get("/ready")

    assert response.status_code == 503
    body = response.json()
    assert body == {"status": "not_ready"}
    assert "checks" not in body
