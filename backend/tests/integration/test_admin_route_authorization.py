"""Regression test: readonly users must be rejected by admin-only API routes."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.dependencies import CurrentUser, get_current_user
from app.database import get_db
from app.main import app


@pytest.mark.integration
async def test_readonly_user_gets_403_on_admin_governance_route(mock_db):
    async def override_db():
        yield mock_db

    async def override_current_user() -> CurrentUser:
        return CurrentUser(user_id="user-1", email="reader@example.com", role="readonly")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_current_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/governance/status", headers={"Authorization": "Bearer fake"}
            )
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 403
