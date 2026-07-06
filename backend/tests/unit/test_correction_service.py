"""Unit coverage for CorrectionService.review governance (A3 regression)."""

import pytest

from app.core.exceptions import AuthorizationError, NotFoundError
from app.services.correction_service import CorrectionService


class _FakeMappingResult:
    """Mimics the `.mappings().first()` chain used by CorrectionService.review."""

    def __init__(self, mapping: dict | None) -> None:
        self._mapping = mapping

    def mappings(self):
        return self

    def first(self):
        return self._mapping


@pytest.mark.unit
async def test_review_rejects_when_reviewer_is_requester(mock_db):
    """Four-eyes principle: an admin must not be able to approve their own proposal."""
    mock_db.execute.return_value = _FakeMappingResult(
        {
            "id": "correction-1",
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

    with pytest.raises(AuthorizationError):
        await CorrectionService(mock_db).review(
            correction_id="correction-1",
            approve=True,
            reviewer="admin-1",
            decision_reason="Looks correct to me",
        )

    # Only the SELECT ... FOR UPDATE should have run; no write was attempted.
    assert mock_db.execute.call_count == 1


@pytest.mark.unit
async def test_review_allows_distinct_reviewer(mock_db):
    mock_db.execute.side_effect = [
        _FakeMappingResult(
            {
                "id": "correction-1",
                "entity_type": "drug_asset",
                "entity_id": "entity-1",
                "field_path": "modality",
                "granularity_key": "entity",
                "proposed_value": "Small molecule",
                "previous_assertion_id": None,
                "evidence_snippet_id": "evidence-1",
                "requested_by": "admin-1",
            }
        ),
        None,  # INSERT INTO field_assertions
        None,  # UPDATE manual_corrections
    ]

    result = await CorrectionService(mock_db).review(
        correction_id="correction-1",
        approve=True,
        reviewer="admin-2",
        decision_reason="Confirmed against source document",
    )

    assert result["review_status"] == "approved"
    assert mock_db.execute.call_count == 3


@pytest.mark.unit
async def test_review_raises_not_found_when_correction_missing(mock_db):
    mock_db.execute.return_value = _FakeMappingResult(None)

    with pytest.raises(NotFoundError):
        await CorrectionService(mock_db).review(
            correction_id="missing",
            approve=True,
            reviewer="admin-2",
            decision_reason="N/A",
        )
