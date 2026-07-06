"""Unit coverage for the dashboard overview aggregate (A1 regression)."""

from datetime import UTC, datetime

import pytest

from app.services.overview_service import OverviewService
from tests.conftest import FakeResult, FakeRow


@pytest.mark.unit
async def test_get_stats_maps_aggregate_counts(mock_db):
    now = datetime(2026, 6, 20, tzinfo=UTC)
    row = FakeRow(12, 5, 30, 3, now)
    mock_db.execute.return_value = FakeResult([row])

    stats = await OverviewService(mock_db).get_stats()

    assert stats == {
        "total_assets": 12,
        "total_companies": 5,
        "total_trials": 30,
        "active_sources": 3,
        "last_ingest": now.isoformat(),
    }


@pytest.mark.unit
async def test_get_stats_handles_empty_database(mock_db):
    """No data ingested yet: counts are zero and last_ingest is null, not an error."""
    row = FakeRow(0, 0, 0, 0, None)
    mock_db.execute.return_value = FakeResult([row])

    stats = await OverviewService(mock_db).get_stats()

    assert stats["total_assets"] == 0
    assert stats["last_ingest"] is None
