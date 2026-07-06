"""Exercise the complete new-record persistence path without a live database."""

from contextlib import AbstractAsyncContextManager
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from tests.conftest import FakeResult, FakeRow
from workers.base.connector import ConnectorResult
from workers.persistence.trials import _persist_trials


class Savepoint(AbstractAsyncContextManager):
    async def __aexit__(self, exc_type, exc, traceback):
        return False


class RecordingDB:
    def __init__(self, existing_trial=None):
        self.statements: list[str] = []
        self.committed = False
        self.existing_trial = existing_trial

    def begin_nested(self):
        return Savepoint()

    async def execute(self, statement, params=None):
        sql = str(statement)
        self.statements.append(sql)
        if "FROM data_sources" in sql:
            return FakeResult([FakeRow("source-1")])
        if "FROM source_documents WHERE" in sql:
            return FakeResult([])
        if "FROM clinical_trials WHERE nct_id" in sql:
            return FakeResult([self.existing_trial] if self.existing_trial else [])
        if "FROM field_assertions" in sql:
            return FakeResult([])
        return FakeResult([])

    async def commit(self):
        self.committed = True


@pytest.mark.unit
async def test_new_trial_path_persists_document_trial_evidence_and_assertions(monkeypatch):
    db = RecordingDB()
    parsed = SimpleNamespace(nct_id="NCT00000001", title="Trial", last_update_date=None)
    raw = {
        "protocolSection": {
            "identificationModule": {"nctId": parsed.nct_id},
            "statusModule": {"overallStatus": "RECRUITING"},
        }
    }
    result = ConnectorResult("clinicaltrials_gov")
    result.raw_payloads = [{"parsed": parsed, "raw": raw, "hash": "a" * 64}]

    class Normalizer:
        def normalize(self, _parsed):
            return {
                "nct_id": parsed.nct_id,
                "title": parsed.title,
                "phase_normalized": None,
                "status_normalized": "RECRUITING",
                "source_updated_at": None,
                "enrollment": None,
                "start_date": None,
                "completion_date": None,
                "sponsor_name": None,
            }

    async def fake_assets(**kwargs):
        return []

    async def fake_store(**kwargs):
        return SimpleNamespace(path="raw/test.json.gz", byte_count=42)

    monkeypatch.setattr("workers.persistence.trials._upsert_drug_assets_from_trial", fake_assets)
    monkeypatch.setattr("workers.persistence.trials.store_raw_payload", fake_store)

    await _persist_trials(db, result, Normalizer())

    joined = "\n".join(db.statements)
    assert result.records_inserted == 1
    assert result.records_rejected == 0
    assert "INSERT INTO source_documents" in joined
    assert "INSERT INTO clinical_trials" in joined
    assert "INSERT INTO evidence_snippets" in joined
    assert "INSERT INTO field_assertions" in joined
    assert db.committed


@pytest.mark.unit
async def test_all_persistence_failures_fail_the_page_instead_of_silent_success(monkeypatch):
    db = RecordingDB()
    parsed = SimpleNamespace(nct_id="NCT00000001", title="Trial", last_update_date=None)
    result = ConnectorResult("clinicaltrials_gov")
    result.raw_payloads = [{"parsed": parsed, "raw": {"protocolSection": {}}, "hash": "b" * 64}]

    class Normalizer:
        def normalize(self, _parsed):
            return {"nct_id": parsed.nct_id, "title": parsed.title}

    async def failing_store(**kwargs):
        raise RuntimeError("storage unavailable")

    monkeypatch.setattr("workers.persistence.trials.store_raw_payload", failing_store)
    with pytest.raises(RuntimeError, match="All parsed records failed"):
        await _persist_trials(db, result, Normalizer())
    assert result.records_rejected == 1
    assert not db.committed


@pytest.mark.unit
async def test_newer_existing_trial_updates_canonical_record(monkeypatch):
    now = datetime(2026, 6, 21, tzinfo=UTC)
    db = RecordingDB(FakeRow("trial-1", now - timedelta(days=1), "old-hash"))
    parsed = SimpleNamespace(nct_id="NCT00000001", title="Trial", last_update_date=now.date())
    result = ConnectorResult("clinicaltrials_gov")
    result.raw_payloads = [{"parsed": parsed, "raw": {"protocolSection": {}}, "hash": "new-hash"}]

    class Normalizer:
        def normalize(self, _parsed):
            return {
                "nct_id": parsed.nct_id,
                "title": parsed.title,
                "source_updated_at": now,
                "status_normalized": "COMPLETED",
            }

    monkeypatch.setattr(
        "workers.persistence.trials.store_raw_payload",
        AsyncMock(return_value=SimpleNamespace(path="raw/new.json.gz", byte_count=42)),
    )
    monkeypatch.setattr(
        "workers.persistence.trials._upsert_drug_assets_from_trial", AsyncMock(return_value=[])
    )
    await _persist_trials(db, result, Normalizer())
    assert result.records_updated == 1
    assert any("UPDATE clinical_trials SET" in sql for sql in db.statements)


@pytest.mark.unit
async def test_same_payload_is_noop_without_asset_side_effects(monkeypatch):
    now = datetime(2026, 6, 21, tzinfo=UTC)
    same_hash = "same-hash"
    db = RecordingDB(FakeRow("trial-1", now, same_hash))
    parsed = SimpleNamespace(nct_id="NCT00000001", title="Trial", last_update_date=now.date())
    result = ConnectorResult("clinicaltrials_gov")
    result.raw_payloads = [{"parsed": parsed, "raw": {"protocolSection": {}}, "hash": same_hash}]

    class Normalizer:
        def normalize(self, _parsed):
            return {"nct_id": parsed.nct_id, "title": parsed.title, "source_updated_at": now}

    asset_upsert = AsyncMock(return_value=[])
    monkeypatch.setattr(
        "workers.persistence.trials.store_raw_payload",
        AsyncMock(return_value=SimpleNamespace(path="raw/same.json.gz", byte_count=42)),
    )
    monkeypatch.setattr("workers.persistence.trials._upsert_drug_assets_from_trial", asset_upsert)
    await _persist_trials(db, result, Normalizer())
    assert result.records_skipped == 1
    asset_upsert.assert_not_awaited()
    assert not any("UPDATE clinical_trials SET" in sql for sql in db.statements)
