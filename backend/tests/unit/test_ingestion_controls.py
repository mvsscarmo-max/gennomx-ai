"""Contract tests for source activation, dry-runs, and raw storage preflight."""

from unittest.mock import AsyncMock

import pytest

from workers.base.connector import ConnectorResult
from workers.storage import raw_payload
from workers.tasks import ingest


@pytest.mark.unit
class TestIngestionControls:
    async def test_disabled_source_does_not_create_a_real_job(self, mock_db, monkeypatch):
        monkeypatch.setattr(ingest, "_is_source_enabled", AsyncMock(return_value=False))

        tracked_job = await ingest._create_tracked_job(
            mock_db, "pubmed", "incremental", "task-1", dry_run=False
        )

        assert tracked_job is None
        mock_db.execute.assert_not_awaited()
        mock_db.commit.assert_not_awaited()

    async def test_real_run_requires_storage_preflight(self, mock_db, monkeypatch):
        monkeypatch.setattr(ingest, "_is_source_enabled", AsyncMock(return_value=True))
        preflight = AsyncMock(side_effect=RuntimeError("storage unavailable"))
        monkeypatch.setattr(ingest, "preflight_raw_storage", preflight)

        with pytest.raises(RuntimeError, match="storage unavailable"):
            await ingest._create_tracked_job(
                mock_db, "pubmed", "incremental", "task-1", dry_run=False
            )

        preflight.assert_awaited_once()
        mock_db.commit.assert_not_awaited()

    async def test_dry_run_skips_storage_preflight(self, mock_db, monkeypatch):
        class Tracker:
            async def create_job(self, *args, **kwargs):
                return "job-1"

            async def start_job(self, job_id):
                assert job_id == "job-1"

        preflight = AsyncMock()
        monkeypatch.setattr(ingest, "JobTracker", lambda db: Tracker())
        monkeypatch.setattr(ingest, "preflight_raw_storage", preflight)

        tracked_job = await ingest._create_tracked_job(
            mock_db, "pubmed", "incremental", "task-1", dry_run=True
        )

        assert tracked_job is not None
        preflight.assert_not_awaited()

    async def test_dry_run_normalizes_without_persistence(self):
        class Normalizer:
            def normalize(self, payload):
                if payload["invalid"]:
                    raise ValueError("invalid")
                return payload

        counters = {"parsed": 0, "accepted": 0, "rejected": 0}
        await ingest._normalize_dry_run_page(
            [{"parsed": {"invalid": False}}, {"parsed": {"invalid": True}}],
            Normalizer(),
            counters,
        )
        result = ConnectorResult("pubmed")
        ingest._finalize_dry_run(result, counters)

        assert counters == {"parsed": 2, "accepted": 1, "rejected": 1}
        assert result.records_inserted == 0
        assert result.metadata["dry_run"] is True
        assert result.metadata["dry_run_counts"] == counters

    async def test_storage_preflight_writes_reads_and_removes_probe(self, monkeypatch):
        monkeypatch.setattr(raw_payload.settings, "MINIO_ACCESS_KEY_ID", "test-access")
        monkeypatch.setattr(raw_payload.settings, "MINIO_SECRET_ACCESS_KEY", "test-secret")
        ensure = AsyncMock()
        put = AsyncMock()
        get = AsyncMock(return_value=b"gennomx-ai-storage-preflight")
        delete = AsyncMock()
        monkeypatch.setattr(raw_payload, "ensure_buckets_exist", ensure)
        monkeypatch.setattr(raw_payload, "put_object", put)
        monkeypatch.setattr(raw_payload, "get_object", get)
        monkeypatch.setattr(raw_payload, "delete_object", delete)

        result = await raw_payload.preflight_raw_storage()

        assert result["status"] == "ok"
        ensure.assert_awaited_once()
        put.assert_awaited_once()
        get.assert_awaited_once()
        delete.assert_awaited_once()
