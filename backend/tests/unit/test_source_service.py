"""Unit tests for SourceService."""

from datetime import datetime
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError
from app.services.source_service import SourceService
from tests.conftest import FakeResult, FakeRow


@pytest.mark.unit
class TestSourceServiceJobs:
    async def test_list_jobs_returns_paginated_items(self, mock_db):
        now = datetime(2026, 6, 9, 12, 0)
        row = FakeRow(
            str(uuid4()),
            "clinicaltrials_gov",
            "incremental",
            "success",
            "celery-1",
            now,
            now,
            1.5,
            10,
            8,
            1,
            1,
            None,
            None,
            now,
        )
        mock_db.execute.side_effect = [
            FakeResult([], scalar_value=1),
            FakeResult([row]),
        ]

        service = SourceService(mock_db)
        items, total = await service.list_jobs(source_slug="clinicaltrials_gov")

        assert total == 1
        assert items[0]["source_slug"] == "clinicaltrials_gov"
        assert items[0]["records_fetched"] == 10
        assert items[0]["started_at"] == now.isoformat()

    async def test_get_job_detail_raises_when_missing(self, mock_db):
        mock_db.execute.return_value = FakeResult([])

        service = SourceService(mock_db)

        with pytest.raises(NotFoundError):
            await service.get_job_detail(uuid4())
