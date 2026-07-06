"""Exercise the Open Targets biological-target persistence path."""

from contextlib import AbstractAsyncContextManager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from tests.conftest import FakeResult, FakeRow
from workers.base.connector import ConnectorResult
from workers.persistence.targets import _persist_targets


class Savepoint(AbstractAsyncContextManager):
    async def __aexit__(self, exc_type, exc, traceback):
        return False


class RecordingDB:
    def __init__(self, *, existing_target=None, indication_rows=None):
        self.statements: list[str] = []
        self.committed = False
        self.existing_target = existing_target
        self.indication_rows = indication_rows or []

    def begin_nested(self):
        return Savepoint()

    async def execute(self, statement, params=None):
        sql = str(statement)
        self.statements.append(sql)
        if "FROM data_sources" in sql:
            return FakeResult([FakeRow("source-1")])
        if "FROM indications" in sql:
            return FakeResult(self.indication_rows)
        if "FROM source_documents WHERE" in sql:
            return FakeResult([])
        if "FROM targets" in sql and "WHERE lower(symbol)" in sql:
            return FakeResult([self.existing_target] if self.existing_target else [])
        return FakeResult([])

    async def commit(self):
        self.committed = True


def _normalized_payload(**overrides):
    base = {
        "symbol": "TP53",
        "name": "tumor protein p53",
        "aliases": ["p53"],
        "organism": "Homo sapiens",
        "target_type": "protein",
        "external_ids": {"ensembl": "ENSG00000141510"},
        "open_targets_score": 0.87,
        "associated_indication_names": ["non-small cell lung cancer"],
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
async def test_new_target_persists_document_and_evidence(monkeypatch):
    db = RecordingDB(indication_rows=[FakeRow("indication-1")])
    parsed = SimpleNamespace(external_id="ENSG00000141510", symbol="TP53")
    result = ConnectorResult("open_targets")
    result.raw_payloads = [{"parsed": parsed, "raw": {"x": 1}, "hash": "a" * 64}]

    async def fake_store(**kwargs):
        return SimpleNamespace(path="raw/open_targets/test.json.gz", byte_count=10)

    monkeypatch.setattr("workers.persistence.targets.store_raw_payload", fake_store)

    await _persist_targets(db, result, Normalizer(_normalized_payload()), "open_targets")

    joined = "\n".join(db.statements)
    assert result.records_inserted == 1
    assert result.records_rejected == 0
    assert "INSERT INTO source_documents" in joined
    assert "INSERT INTO targets" in joined
    assert "INSERT INTO evidence_snippets" in joined
    assert db.committed


@pytest.mark.unit
@pytest.mark.connector
async def test_missing_symbol_rejected_by_quality_gate(monkeypatch):
    db = RecordingDB()
    parsed = SimpleNamespace(external_id="ENSG000", symbol="")
    result = ConnectorResult("open_targets")
    result.raw_payloads = [{"parsed": parsed, "raw": {"x": 1}, "hash": "b" * 64}]

    async def fake_store(**kwargs):
        return SimpleNamespace(path="raw/x.json.gz", byte_count=1)

    monkeypatch.setattr("workers.persistence.targets.store_raw_payload", fake_store)

    with pytest.raises(RuntimeError, match="All parsed target records failed"):
        await _persist_targets(
            db, result, Normalizer(_normalized_payload(symbol="")), "open_targets"
        )
    assert result.records_rejected == 1
    assert not db.committed


@pytest.mark.unit
@pytest.mark.connector
async def test_existing_target_same_hash_is_noop(monkeypatch):
    db = RecordingDB(existing_target=FakeRow("target-1", ["p53"], ["indication-1"], "same-hash"))
    parsed = SimpleNamespace(external_id="ENSG00000141510", symbol="TP53")
    result = ConnectorResult("open_targets")
    result.raw_payloads = [{"parsed": parsed, "raw": {"x": 1}, "hash": "same-hash"}]

    monkeypatch.setattr(
        "workers.persistence.targets.store_raw_payload",
        AsyncMock(return_value=SimpleNamespace(path="raw/x.json.gz", byte_count=1)),
    )

    await _persist_targets(db, result, Normalizer(_normalized_payload()), "open_targets")

    assert result.records_skipped == 1
    assert not any("INSERT INTO targets" in sql for sql in db.statements)
    assert not any("UPDATE targets" in sql for sql in db.statements)


@pytest.mark.unit
@pytest.mark.connector
async def test_existing_target_new_hash_merges_aliases_and_updates(monkeypatch):
    db = RecordingDB(existing_target=FakeRow("target-1", ["LFS1"], ["indication-2"], "old-hash"))
    parsed = SimpleNamespace(external_id="ENSG00000141510", symbol="TP53")
    result = ConnectorResult("open_targets")
    result.raw_payloads = [{"parsed": parsed, "raw": {"x": 1}, "hash": "new-hash"}]

    monkeypatch.setattr(
        "workers.persistence.targets.store_raw_payload",
        AsyncMock(return_value=SimpleNamespace(path="raw/x.json.gz", byte_count=1)),
    )

    await _persist_targets(db, result, Normalizer(_normalized_payload()), "open_targets")

    assert result.records_updated == 1
    assert any("UPDATE targets" in sql for sql in db.statements)
