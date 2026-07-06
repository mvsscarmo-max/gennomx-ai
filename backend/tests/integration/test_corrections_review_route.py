"""Integration coverage: correction review endpoint enforces four-eyes (A3)
and domain errors surface as structured HTTP responses, not 500s (A8)."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.dependencies import CurrentUser, get_current_user
from app.database import get_db
from app.main import app

_CORRECTION_ID = "11111111-1111-1111-1111-111111111111"
_MISSING_ID = "22222222-2222-2222-2222-222222222222"


class _FakeMappingResult:
    def __init__(self, mapping: dict | None) -> None:
        self._mapping = mapping

    def mappings(self):
        return self

    def first(self):
        return self._mapping


@pytest.mark.integration
async def test_review_by_requester_returns_403_not_500(mock_db):
    mock_db.execute.return_value = _FakeMappingResult(
        {
            "id": _CORRECTION_ID,
            "entity_type": "drug_asset",
            "entity_id": "entity-1",
            "field_path": "modality",
            "granularity_key": "entity",
            "proposed_value": "Small molecule",
            "previous_assertion_id": None,
            "evidence_snippet_id": "evidence-1",
            "requested_by": "admin-1",
        }
    )

    async def override_db():
        yield mock_db

    async def override_current_user() -> CurrentUser:
        return CurrentUser(user_id="admin-1", email="admin@example.com", role="admin")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_current_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/corrections/{_CORRECTION_ID}/review",
                headers={"Authorization": "Bearer fake"},
                json={"approve": True, "decision_reason": "Looks correct to me"},
            )
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTHORIZATION_ERROR"


@pytest.mark.integration
async def test_review_missing_correction_returns_404_not_500(mock_db):
    mock_db.execute.return_value = _FakeMappingResult(None)

    async def override_db():
        yield mock_db

    async def override_current_user() -> CurrentUser:
        return CurrentUser(user_id="admin-2", email="admin2@example.com", role="admin")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_current_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/corrections/{_MISSING_ID}/review",
                headers={"Authorization": "Bearer fake"},
                json={"approve": True, "decision_reason": "Correction id does not exist"},
            )
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
