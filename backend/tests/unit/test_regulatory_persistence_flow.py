"""Exercise the shared regulatory-approval persistence path (openFDA/DailyMed/EMA)."""

from contextlib import AbstractAsyncContextManager
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from tests.conftest import FakeResult, FakeRow
from workers.base.connector import ConnectorResult
from workers.persistence.regulatory import _persist_regulatory_approvals


class Savepoint(AbstractAsyncContextManager):
    async def __aexit__(self, exc_type, exc, traceback):
        return False


class RecordingDB:
    def __init__(self, *, drug_asset_row=None, existing_approval=None):
        self.statements: list[str] = []
        self.committed = False
        self.drug_asset_row = drug_asset_row
        self.existing_approval = existing_approval

    def begin_nested(self):
        return Savepoint()

    async def execute(self, statement, params=None):
        sql = str(statement)
        self.statements.append(sql)
        if "FROM data_sources" in sql:
            return FakeResult([FakeRow("source-1")])
        if "FROM drug_assets" in sql:
            return FakeResult([self.drug_asset_row] if self.drug_asset_row else [])
        if "FROM source_documents WHERE" in sql:
            return FakeResult([])
        if "FROM regulatory_approvals" in sql and "WHERE drug_asset_id" in sql:
            return FakeResult([self.existing_approval] if self.existing_approval else [])
        return FakeResult([])

    async def commit(self):
        self.committed = True


def _normalized_payload(**overrides):
    base = {
        "asset_name": "Lipitor",
        "asset_aliases": ["Atorvastatin"],
        "agency": "FDA",
        "region": "US",
        "approval_status": "approved",
        "approval_date": None,
        "submission_date": None,
        "pathway": None,
        "special_designations": [],
        "application_number": "NDA020702",
        "label_url": "https://example.test/label",
        "indication_name": None,
        "indication_id": None,
        "source_updated_at": datetime(2026, 1, 1, tzinfo=UTC),
        "raw_data": {},
    }
    base.update(overrides)
    return base


class Normalizer:
    def __init__(self, payload):
        self._payload = payload

    def normalize(self, _parsed):
        return dict(self._payload)


@pytest.mark.unit
@pytest.mark.connector
async def test_new_approval_persists_document_evidence_and_asset_link(monkeypatch):
    db = RecordingDB(drug_asset_row=FakeRow("asset-1"))
    parsed = SimpleNamespace(external_id="NDA020702", asset_name="Lipitor")
    result = ConnectorResult("openfda")
    result.raw_payloads = [{"parsed": parsed, "raw": {"x": 1}, "hash": "a" * 64}]

    async def fake_store(**kwargs):
        return SimpleNamespace(path="raw/openfda/test.json.gz", byte_count=10)

    monkeypatch.setattr("workers.persistence.regulatory.store_raw_payload", fake_store)

    await _persist_regulatory_approvals(db, result, Normalizer(_normalized_payload()), "openfda")

    joined = "\n".join(db.statements)
    assert result.records_inserted == 1
    assert result.records_rejected == 0
    assert "INSERT INTO source_documents" in joined
    assert "INSERT INTO regulatory_approvals" in joined
    assert "INSERT INTO evidence_snippets" in joined
    assert db.committed


@pytest.mark.unit
@pytest.mark.connector
async def test_no_drug_asset_match_is_skipped_not_rejected(monkeypatch):
    db = RecordingDB(drug_asset_row=None)
    parsed = SimpleNamespace(external_id="NDA999999", asset_name="UnknownDrug")
    result = ConnectorResult("openfda")
    result.raw_payloads = [{"parsed": parsed, "raw": {"x": 1}, "hash": "b" * 64}]

    async def fake_store(**kwargs):
        return SimpleNamespace(path="raw/openfda/test.json.gz", byte_count=10)

    monkeypatch.setattr("workers.persistence.regulatory.store_raw_payload", fake_store)

    await _persist_regulatory_approvals(
        db, result, Normalizer(_normalized_payload(asset_name="UnknownDrug")), "openfda"
    )

    assert result.records_skipped == 1
    assert result.records_inserted == 0
    assert result.records_rejected == 0
    assert db.committed


@pytest.mark.unit
@pytest.mark.connector
async def test_missing_asset_name_rejected_by_quality_gate(monkeypatch):
    db = RecordingDB(drug_asset_row=FakeRow("asset-1"))
    parsed = SimpleNamespace(external_id="NDA000000", asset_name="")
    result = ConnectorResult("openfda")
    valid_parsed = SimpleNamespace(external_id="NDA020702", asset_name="Lipitor")
    result = ConnectorResult("openfda")
    result.raw_payloads = [
        {"parsed": parsed, "raw": {"x": 1}, "hash": "c" * 64},
        {"parsed": valid_parsed, "raw": {"x": 2}, "hash": "e" * 64},
    ]

    async def fake_store(**kwargs):
        return SimpleNamespace(path="raw/openfda/test.json.gz", byte_count=10)

    monkeypatch.setattr("workers.persistence.regulatory.store_raw_payload", fake_store)

    class MixedNormalizer:
        def normalize(self, parsed_arg):
            if parsed_arg is parsed:
                return _normalized_payload(asset_name="")
            return _normalized_payload()

    await _persist_regulatory_approvals(db, result, MixedNormalizer(), "openfda")

    assert result.records_rejected == 1
    assert result.records_inserted == 1
    assert db.committed


@pytest.mark.unit
@pytest.mark.connector
async def test_existing_approval_with_same_hash_is_noop(monkeypatch):
    db = RecordingDB(
        drug_asset_row=FakeRow("asset-1"),
        existing_approval=FakeRow("approval-1", "same-hash", "2026-01-01T00:00:00+00:00"),
    )
    parsed = SimpleNamespace(external_id="NDA020702", asset_name="Lipitor")
    result = ConnectorResult("openfda")
    result.raw_payloads = [{"parsed": parsed, "raw": {"x": 1}, "hash": "same-hash"}]

    monkeypatch.setattr(
        "workers.persistence.regulatory.store_raw_payload",
        AsyncMock(return_value=SimpleNamespace(path="raw/x.json.gz", byte_count=1)),
    )

    await _persist_regulatory_approvals(db, result, Normalizer(_normalized_payload()), "openfda")

    assert result.records_skipped == 1
    assert not any("INSERT INTO regulatory_approvals" in sql for sql in db.statements)
    assert not any("UPDATE regulatory_approvals" in sql for sql in db.statements)


@pytest.mark.unit
@pytest.mark.connector
async def test_existing_approval_with_new_hash_updates(monkeypatch):
    db = RecordingDB(
        drug_asset_row=FakeRow("asset-1"),
        existing_approval=FakeRow("approval-1", "old-hash", "2025-12-01T00:00:00+00:00"),
    )
    parsed = SimpleNamespace(external_id="NDA020702", asset_name="Lipitor")
    result = ConnectorResult("openfda")
    result.raw_payloads = [{"parsed": parsed, "raw": {"x": 1}, "hash": "new-hash"}]

    monkeypatch.setattr(
        "workers.persistence.regulatory.store_raw_payload",
        AsyncMock(return_value=SimpleNamespace(path="raw/x.json.gz", byte_count=1)),
    )

    await _persist_regulatory_approvals(db, result, Normalizer(_normalized_payload()), "openfda")

    assert result.records_updated == 1
    assert any("UPDATE regulatory_approvals" in sql for sql in db.statements)


@pytest.mark.unit
@pytest.mark.connector
async def test_all_failures_raise_and_do_not_commit(monkeypatch):
    db = RecordingDB(drug_asset_row=FakeRow("asset-1"))
    parsed = SimpleNamespace(external_id="NDA020702", asset_name="Lipitor")
    result = ConnectorResult("openfda")
    result.raw_payloads = [{"parsed": parsed, "raw": {"x": 1}, "hash": "d" * 64}]

    async def failing_store(**kwargs):
        raise RuntimeError("storage unavailable")

    monkeypatch.setattr("workers.persistence.regulatory.store_raw_payload", failing_store)

    with pytest.raises(RuntimeError, match="All parsed regulatory records failed"):
        await _persist_regulatory_approvals(
            db, result, Normalizer(_normalized_payload()), "openfda"
        )
    assert result.records_rejected == 1
    assert not db.committed
