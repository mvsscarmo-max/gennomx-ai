"""Unit coverage for warehouse operational metrics in empty and populated states."""

from datetime import datetime

import pytest

from app.services.warehouse_coverage_service import WarehouseCoverageService
from tests.conftest import FakeResult, FakeRow


@pytest.mark.unit
async def test_warehouse_coverage_returns_metrics_and_limitations(mock_db):
    now = datetime(2026, 7, 10, 12, 0)
    mock_db.execute.side_effect = [
        FakeResult([FakeRow(2, 3, 4, 5, 6, 0, 0, 0)]),
        FakeResult([FakeRow(7, 8, 9, 1, 10)]),
        FakeResult([FakeRow("pubmed", True, "active", now, None)]),
        FakeResult([FakeRow("pubmed", "success", 2)]),
    ]

    result = await WarehouseCoverageService(mock_db).get_coverage()

    assert result["entities"]["trials"] == 3
    assert result["traceability"]["open_conflicts"] == 1
    assert result["sources"][0]["last_successful_run"] == now.isoformat()
    assert result["jobs"] == [{"source_slug": "pubmed", "status": "success", "count": 2}]
    assert result["limitations"]
