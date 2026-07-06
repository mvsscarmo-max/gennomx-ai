"""Unit tests for app/api/v1/jobs.py — retry_job and worker_status."""

from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1.jobs import retry_job, worker_status
from tests.conftest import FakeResult, FakeRow


def _job_row(source_slug: str, job_type: str = "incremental"):
    now = datetime(2026, 6, 9, 12, 0)
    return FakeRow(
        str(uuid4()),
        str(uuid4()),
        source_slug,
        job_type,
        "failed",
        "celery-1",
        now,
        now,
        1.5,
        10,
        8,
        1,
        1,
        "connector_error",
        "boom",
        None,
        None,
        now,
        now,
    )


@pytest.mark.unit
class TestRetryJob:
    async def test_retry_clinicaltrials_job_schedules_known_task(self, mock_db):
        mock_db.execute.return_value = FakeResult([_job_row("clinicaltrials_gov")])
        fake_task = MagicMock(id="task-1")

        with patch("workers.tasks.ingest.run_clinicaltrials_ingest") as mocked:
            mocked.delay.return_value = fake_task
            result = await retry_job(job_id=uuid4(), db=mock_db, _user=MagicMock())

        assert result["success"] is True
        assert result["data"]["celery_task_id"] == "task-1"
        assert result["data"]["source_slug"] == "clinicaltrials_gov"

    async def test_retry_pubmed_job_schedules_known_task(self, mock_db):
        mock_db.execute.return_value = FakeResult([_job_row("pubmed")])
        fake_task = MagicMock(id="task-2")

        with patch("workers.tasks.ingest.run_pubmed_ingest") as mocked:
            mocked.delay.return_value = fake_task
            result = await retry_job(job_id=uuid4(), db=mock_db, _user=MagicMock())

        assert result["success"] is True
        assert result["data"]["celery_task_id"] == "task-2"

    @pytest.mark.parametrize(
        ("source_slug", "task_name"),
        [
            ("openfda", "run_openfda_ingest"),
            ("dailymed", "run_dailymed_ingest"),
            ("open_targets", "run_opentargets_ingest"),
            ("ema", "run_ema_ingest"),
        ],
    )
    async def test_retry_p1_connector_job_schedules_known_task(
        self, mock_db, source_slug, task_name
    ):
        mock_db.execute.return_value = FakeResult([_job_row(source_slug)])
        fake_task = MagicMock(id=f"task-{source_slug}")

        with patch(f"workers.tasks.ingest.{task_name}") as mocked:
            mocked.delay.return_value = fake_task
            result = await retry_job(job_id=uuid4(), db=mock_db, _user=MagicMock())

        assert result["success"] is True
        assert result["data"]["celery_task_id"] == f"task-{source_slug}"
        assert result["data"]["source_slug"] == source_slug

    async def test_retry_unknown_source_returns_501(self, mock_db):
        mock_db.execute.return_value = FakeResult([_job_row("unknown_source")])

        with pytest.raises(HTTPException) as exc_info:
            await retry_job(job_id=uuid4(), db=mock_db, _user=MagicMock())

        assert exc_info.value.status_code == 501

    async def test_retry_scheduling_failure_is_reported_without_raising(self, mock_db):
        mock_db.execute.return_value = FakeResult([_job_row("clinicaltrials_gov")])

        with patch("workers.tasks.ingest.run_clinicaltrials_ingest") as mocked:
            mocked.delay.side_effect = RuntimeError("broker unavailable")
            result = await retry_job(job_id=uuid4(), db=mock_db, _user=MagicMock())

        assert result["success"] is False
        assert "broker unavailable" in result["message"]


@pytest.mark.unit
class TestWorkerStatus:
    async def test_worker_status_reports_ok_when_workers_respond(self):
        inspect = MagicMock()
        inspect.stats.return_value = {"worker1@host": {}}
        inspect.active.return_value = {"worker1@host": [1, 2]}
        celery_app = MagicMock()
        celery_app.control.inspect.return_value = inspect

        with patch("workers.celery_app.celery_app", celery_app):
            result = await worker_status(_user=MagicMock())

        assert result["success"] is True
        assert result["data"]["state"] == "ok"
        assert result["data"]["worker_count"] == 1
        assert result["data"]["active_tasks"] == 2

    async def test_worker_status_reports_unknown_when_inspect_returns_none(self):
        inspect = MagicMock()
        inspect.stats.return_value = None
        inspect.active.return_value = None
        celery_app = MagicMock()
        celery_app.control.inspect.return_value = inspect

        with patch("workers.celery_app.celery_app", celery_app):
            result = await worker_status(_user=MagicMock())

        assert result["success"] is False
        assert result["data"]["state"] == "unknown"

    async def test_worker_status_reports_unknown_on_exception(self):
        celery_app = MagicMock()
        celery_app.control.inspect.side_effect = RuntimeError("broker down")

        with patch("workers.celery_app.celery_app", celery_app):
            result = await worker_status(_user=MagicMock())

        assert result["success"] is False
        assert result["data"]["state"] == "unknown"
