"""Unit coverage for Phase 5 dashboard query contracts."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError
from app.services.audit_service import AuditService
from app.services.catalog_service import CatalogService
from tests.conftest import FakeResult, FakeRow


@pytest.mark.unit
async def test_list_indications_maps_traceable_catalog_fields(mock_db):
    now = datetime(2026, 6, 20, tzinfo=UTC)
    row = FakeRow(
        str(uuid4()), "Melanoma", ["Melanoma maligno"], "Oncologia", {"mesh": "D008545"}, None, now
    )
    mock_db.execute.side_effect = [FakeResult([], scalar_value=1), FakeResult([row])]

    items, total = await CatalogService(mock_db).list_indications(q="melanoma")

    assert total == 1
    assert items[0]["preferred_name"] == "Melanoma"
    assert items[0]["ontology_ids"] == {"mesh": "D008545"}


@pytest.mark.unit
async def test_list_targets_maps_open_targets_score(mock_db):
    now = datetime(2026, 6, 20, tzinfo=UTC)
    row = FakeRow(
        str(uuid4()),
        "BRAF",
        "B-Raf",
        [],
        "Homo sapiens",
        "protein",
        {"ensembl": "ENSG1"},
        0.91,
        ["id-1"],
        now,
    )
    mock_db.execute.side_effect = [FakeResult([], scalar_value=1), FakeResult([row])]

    items, total = await CatalogService(mock_db).list_targets(q="BRAF")

    assert total == 1
    assert items[0]["symbol"] == "BRAF"
    assert items[0]["open_targets_score"] == 0.91


@pytest.mark.unit
async def test_get_indication_raises_when_missing(mock_db):
    mock_db.execute.return_value = FakeResult([])
    with pytest.raises(NotFoundError):
        await CatalogService(mock_db).get_indication(uuid4())


@pytest.mark.unit
async def test_mcp_audit_never_returns_arguments_or_actor_ids(mock_db):
    now = datetime(2026, 6, 20, tzinfo=UTC)
    row = FakeRow(
        str(uuid4()), now, "search_drugs", "claude", 2, 15.5, "success", None, ["drug_asset"], []
    )
    mock_db.execute.side_effect = [FakeResult([], scalar_value=1), FakeResult([row])]

    items, total = await AuditService(mock_db).list_mcp_logs(
        status=None, tool_name=None, page=1, page_size=20
    )

    assert total == 1
    assert items[0]["tool_name"] == "search_drugs"
    assert "normalized_arguments" not in items[0]
    assert "user_id" not in items[0]


@pytest.mark.unit
async def test_security_audit_omits_ip_hash_and_actor_id(mock_db):
    now = datetime(2026, 6, 20, tzinfo=UTC)
    row = FakeRow(
        str(uuid4()),
        now,
        "rate_limit",
        "medium",
        "mcp_token",
        "search_drugs",
        "Limit reached",
        "blocked",
        "open",
    )
    mock_db.execute.side_effect = [FakeResult([], scalar_value=1), FakeResult([row])]

    items, _ = await AuditService(mock_db).list_security_events(
        severity=None, status=None, page=1, page_size=20
    )

    assert items[0]["event_type"] == "rate_limit"
    assert "source_ip_hash" not in items[0]
    assert "actor_id" not in items[0]
