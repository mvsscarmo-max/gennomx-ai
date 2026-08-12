"""Integration contracts for the controlled source activation and run APIs."""

from unittest.mock import AsyncMock, Mock

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.v1 import sources as source_routes
from app.auth.dependencies import CurrentUser, get_current_user
from app.database import get_db
from app.main import app


async def _admin_user() -> CurrentUser:
    return CurrentUser(user_id="admin-1", email="admin@example.com", role="admin")


async def _override_db():
    yield Mock()


@pytest.mark.integration
async def test_run_rejects_disabled_source_without_scheduling(monkeypatch):
    monkeypatch.setattr(
        source_routes.SourceService,
        "get_source_by_slug",
        AsyncMock(return_value={"slug": "pubmed", "is_enabled": False}),
    )
    scheduler = Mock()
    monkeypatch.setattr(source_routes, "schedule_ingestion", scheduler)
    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _admin_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/sources/pubmed/run",
                json={"max_records": 10, "dry_run": False},
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 409
    scheduler.assert_not_called()


@pytest.mark.integration
async def test_dry_run_can_schedule_a_disabled_allowed_source(monkeypatch):
    monkeypatch.setattr(
        source_routes.SourceService,
        "get_source_by_slug",
        AsyncMock(return_value={"slug": "pubmed", "is_enabled": False}),
    )
    monkeypatch.setattr(source_routes.SourceService, "record_ingestion_trigger", AsyncMock())
    monkeypatch.setattr(source_routes, "schedule_ingestion", Mock(return_value=Mock(id="celery-1")))
    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _admin_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/sources/pubmed/run",
                json={"max_records": 10, "dry_run": True, "query": "oncology"},
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    assert response.json()["data"]["dry_run"] is True


@pytest.mark.integration
async def test_activation_refuses_non_implemented_source(monkeypatch):
    monkeypatch.setattr(source_routes.SourceService, "set_source_enabled", AsyncMock())
    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _admin_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch(
                "/api/v1/sources/anvisa/activation",
                json={"is_enabled": True},
                headers={"Authorization": "Bearer fake"},
            )
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 409
