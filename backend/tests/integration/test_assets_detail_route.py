"""Integration coverage: GET /api/v1/assets/{id} returns a validated DrugAssetDetail
(mypy regression: the route previously declared -> DrugAssetDetail while returning
a plain dict from the service layer)."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.dependencies import CurrentUser, get_current_user
from app.database import get_db
from app.main import app
from tests.conftest import FakeResult, FakeRow


@pytest.mark.integration
async def test_asset_detail_route_returns_validated_shape(mock_db):
    now = datetime(2026, 6, 20, tzinfo=UTC)
    asset_id = uuid4()
    row = FakeRow(
        str(asset_id),
        "Semaglutide",
        ["Ozempic"],
        "semaglutide",
        "Small molecule",
        "GLP-1 receptor agonist",
        "PHASE3",
        {"nct": "NCT123"},
        ["Obesity"],
        ["GLP1R"],
        ["Novo Nordisk"],
        {"us": "approved"},
        0.95,
        0.9,
        None,
        now,
        now,
    )
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
                f"/api/v1/assets/{asset_id}", headers={"Authorization": "Bearer fake"}
            )
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    body = response.json()
    assert body["primary_name"] == "Semaglutide"
    assert body["mechanism_of_action"] == "GLP-1 receptor agonist"
    assert body["source_confidence"] == 0.95
