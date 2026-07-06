"""Integration coverage: GET /api/v1/overview must exist and return real aggregates (A1)."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.dependencies import CurrentUser, get_current_user
from app.database import get_db
from app.main import app
from tests.conftest import FakeResult, FakeRow


@pytest.mark.integration
async def test_overview_route_returns_aggregated_stats(mock_db):
    row = FakeRow(4, 2, 9, 1, None)
    mock_db.execute.return_value = FakeResult([row])

    async def override_db():
        yield mock_db

    async def override_current_user() -> CurrentUser:
        return CurrentUser(user_id="user-1", email="reader@example.com", role="readonly")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_current_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/overview", headers={"Authorization": "Bearer fake"}
            )
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["total_assets"] == 4
    assert body["data"]["total_trials"] == 9
