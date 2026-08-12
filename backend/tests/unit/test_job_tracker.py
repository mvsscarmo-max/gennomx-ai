"""Unit tests for JobTracker."""

import json
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from tests.conftest import FakeResult, FakeRow
from workers.base.connector import ConnectorResult
from workers.base.job_tracker import JobTracker


@pytest.mark.unit
class TestJobTracker:
    async def test_create_job_resolves_data_source_id(self, mock_db):
        source_id = str(uuid4())
        mock_db.execute = AsyncMock(
            side_effect=[
                FakeResult([FakeRow(source_id)]),
                FakeResult([]),
            ]
        )

        tracker = JobTracker(mock_db)
        job_id = await tracker.create_job("clinicaltrials_gov", celery_task_id="task-1")

        assert job_id
        insert_params = mock_db.execute.call_args_list[1][0][1]
        assert insert_params["data_source_id"] == source_id
        assert insert_params["slug"] == "clinicaltrials_gov"
        mock_db.commit.assert_awaited()

    async def test_complete_job_serializes_json_fields(self, mock_db):
        result = ConnectorResult("clinicaltrials_gov")
        result.metadata = {"source": "clinicaltrials_gov"}
        result.add_error("schema_error", "Bad payload", {"nct_id": "NCT1"})
        result.finish()

        tracker = JobTracker(mock_db)
        await tracker.complete_job(str(uuid4()), result)

        params = mock_db.execute.call_args_list[0][0][1]
        assert json.loads(params["metadata"]) == {"source": "clinicaltrials_gov"}
        assert json.loads(params["error_detail"])["errors"][0]["type"] == "schema_error"
        source_params = mock_db.execute.call_args_list[1][0][1]
        assert source_params == {"slug": "clinicaltrials_gov"}
        assert "connector_status = 'active'" in str(mock_db.execute.call_args_list[1][0][0])

    async def test_dry_run_does_not_update_data_source(self, mock_db):
        result = ConnectorResult("clinicaltrials_gov")
        result.metadata = {"dry_run": True}
        result.finish()

        await JobTracker(mock_db).complete_job(
            str(uuid4()), result, status="success", update_source=False
        )

        assert mock_db.execute.await_count == 1
