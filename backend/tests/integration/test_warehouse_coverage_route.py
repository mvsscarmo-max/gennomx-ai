"""Integration contract for the admin-only warehouse coverage endpoint."""

from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.dependencies import CurrentUser, get_current_user
from app.database import get_db
from app.main import app
from app.services.warehouse_coverage_service import WarehouseCoverageService


@pytest.mark.integration
async def test_warehouse_coverage_requires_admin(mock_db, monkeypatch):
    monkeypatch.setattr(
        WarehouseCoverageService,
        "get_coverage",
        AsyncMock(return_value={"entities": {}, "traceability": {}, "sources": [], "jobs": []}),
    )

    async def override_db():
        yield mock_db

    async def readonly_user() -> CurrentUser:
        return CurrentUser(user_id="reader", email="reader@example.com", role="readonly")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = readonly_user
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/warehouse/coverage", headers={"Authorization": "Bearer fake"}
            )
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 403
