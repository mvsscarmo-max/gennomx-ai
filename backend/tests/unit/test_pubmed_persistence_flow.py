"""Exercise the PubMed publication persistence path without a live database."""

from contextlib import AbstractAsyncContextManager
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from tests.conftest import FakeResult, FakeRow
from workers.base.connector import ConnectorResult
from workers.persistence.publications import _persist_publications


class Savepoint(AbstractAsyncContextManager):
    async def __aexit__(self, exc_type, exc, traceback):
        return False


class RecordingDB:
    def __init__(self, existing_publication=None):
        self.statements: list[str] = []
        self.committed = False
        self.existing_publication = existing_publication

    def begin_nested(self):
        return Savepoint()

    async def execute(self, statement, params=None):
        sql = str(statement)
        self.statements.append(sql)
        if "FROM data_sources" in sql:
            return FakeResult([FakeRow("source-1")])
        if "FROM source_documents WHERE" in sql:
            return FakeResult([])
        if "FROM publications WHERE pmid" in sql:
            return FakeResult([self.existing_publication] if self.existing_publication else [])
        if "FROM clinical_trials" in sql and "nct_id" in sql:
            return FakeResult([FakeRow("NCT03914612")])
        return FakeResult([])

    async def commit(self):
        self.committed = True


@pytest.mark.unit
@pytest.mark.connector
async def test_new_publication_path_persists_document_and_evidence(monkeypatch):
    db = RecordingDB()
    parsed = SimpleNamespace(
        pmid="39567890",
        title="Test Article",
        journal="N Engl J Med",
        doi="10.1056/NEJMoa2411764",
        pmcid=None,
        abstract="Some abstract",
        authors=["Smith J"],
        publication_date=None,
        date_revised=datetime(2026, 1, 15, tzinfo=UTC).date(),
        publication_type="article",
        keywords=["Cancer"],
        nct_ids=["NCT03914612"],
    )
    raw = {"xml": "<PubmedArticle>...</PubmedArticle>"}
    result = ConnectorResult("pubmed")
    result.raw_payloads = [{"parsed": parsed, "raw": raw, "hash": "a" * 64}]

    class Normalizer:
        def normalize(self, _parsed):
            return {
                "pmid": parsed.pmid,
                "title": parsed.title,
                "journal": parsed.journal,
                "doi": parsed.doi,
                "pmcid": parsed.pmcid,
                "abstract": parsed.abstract,
                "authors": parsed.authors,
                "publication_date": parsed.publication_date,
                "publication_type": parsed.publication_type,
                "keywords": parsed.keywords,
                "nct_ids": parsed.nct_ids,
                "source_updated_at": datetime(2026, 1, 15, tzinfo=UTC),
                "registry_source": "pubmed",
                "evidence_maturity": "peer_reviewed_primary",
                "source_url": "https://pubmed.ncbi.nlm.nih.gov/39567890/",
                "open_access": False,
            }

    async def fake_store(**kwargs):
        return SimpleNamespace(path="raw/test.xml.gz", byte_count=42)

    monkeypatch.setattr("workers.persistence.publications.store_raw_payload", fake_store)

    await _persist_publications(db, result, Normalizer())

    joined = "\n".join(db.statements)
    assert result.records_inserted == 1
    assert result.records_rejected == 0
    assert "INSERT INTO source_documents" in joined
    assert "INSERT INTO publications" in joined
    assert "INSERT INTO evidence_snippets" in joined
    assert "linked_trial_ids" in joined
    assert db.committed


@pytest.mark.unit
@pytest.mark.connector
async def test_all_publication_persistence_failures_fail_the_page(monkeypatch):
    db = RecordingDB()
    parsed = SimpleNamespace(
        pmid="39567890",
        title="Test",
        date_revised=None,
    )
    result = ConnectorResult("pubmed")
    result.raw_payloads = [{"parsed": parsed, "raw": {"xml": "<x/>"}, "hash": "b" * 64}]

    class Normalizer:
        def normalize(self, _parsed):
            return {"pmid": parsed.pmid, "title": parsed.title}

    async def failing_store(**kwargs):
        raise RuntimeError("storage unavailable")

    monkeypatch.setattr("workers.persistence.publications.store_raw_payload", failing_store)
    with pytest.raises(RuntimeError, match="All parsed publication records failed"):
        await _persist_publications(db, result, Normalizer())
    assert result.records_rejected == 1
    assert not db.committed


@pytest.mark.unit
@pytest.mark.connector
async def test_newer_existing_publication_updates_canonical(monkeypatch):
    now = datetime(2026, 6, 21, tzinfo=UTC)
    old_time = datetime(2026, 6, 20, tzinfo=UTC)
    db = RecordingDB(FakeRow("pub-1", old_time.isoformat(), "old-hash"))
    parsed = SimpleNamespace(
        pmid="39567890",
        title="Updated Title",
        abstract="Updated abstract",
        journal="Test Journal",
        doi=None,
        pmcid=None,
        authors=[],
        publication_date=None,
        date_revised=now.date(),
        publication_type="article",
        keywords=[],
        nct_ids=[],
    )
    result = ConnectorResult("pubmed")
    result.raw_payloads = [{"parsed": parsed, "raw": {"xml": "<x/>"}, "hash": "new-hash"}]

    class Normalizer:
        def normalize(self, _parsed):
            return {
                "pmid": parsed.pmid,
                "title": parsed.title,
                "source_updated_at": now,
                "nct_ids": [],
                "authors": [],
                "keywords": [],
            }

    monkeypatch.setattr(
        "workers.persistence.publications.store_raw_payload",
        AsyncMock(return_value=SimpleNamespace(path="raw/new.xml.gz", byte_count=42)),
    )
    await _persist_publications(db, result, Normalizer())
    assert result.records_updated == 1
    assert any("UPDATE publications SET" in sql for sql in db.statements)


@pytest.mark.unit
@pytest.mark.connector
async def test_same_payload_is_noop(monkeypatch):
    now = datetime(2026, 6, 21, tzinfo=UTC)
    same_hash = "same-hash"
    db = RecordingDB(FakeRow("pub-1", now.isoformat(), same_hash))
    parsed = SimpleNamespace(
        pmid="39567890",
        title="Same Title",
        abstract="Same abstract",
        journal="Test Journal",
        doi=None,
        pmcid=None,
        authors=[],
        publication_date=None,
        date_revised=now.date(),
        publication_type="article",
        keywords=[],
        nct_ids=[],
    )
    result = ConnectorResult("pubmed")
    result.raw_payloads = [{"parsed": parsed, "raw": {"xml": "<x/>"}, "hash": same_hash}]

    class Normalizer:
        def normalize(self, _parsed):
            return {
                "pmid": parsed.pmid,
                "title": parsed.title,
                "source_updated_at": now,
                "nct_ids": [],
                "authors": [],
                "keywords": [],
            }

    monkeypatch.setattr(
        "workers.persistence.publications.store_raw_payload",
        AsyncMock(return_value=SimpleNamespace(path="raw/same.xml.gz", byte_count=42)),
    )
    await _persist_publications(db, result, Normalizer())
    assert result.records_skipped == 1
    assert not any("UPDATE publications SET" in sql for sql in db.statements)
    assert not any("INSERT INTO publications" in sql for sql in db.statements)


@pytest.mark.unit
@pytest.mark.connector
async def test_invalid_pmid_rejected_by_quality_gate(monkeypatch):
    db = RecordingDB()
    parsed = SimpleNamespace(
        pmid="",
        title="No PMID",
        date_revised=None,
    )
    result = ConnectorResult("pubmed")
    result.raw_payloads = [{"parsed": parsed, "raw": {"xml": "<x/>"}, "hash": "x" * 64}]

    class Normalizer:
        def normalize(self, _parsed):
            return {"pmid": "", "title": "No PMID"}

    async def fake_store(**kwargs):
        return SimpleNamespace(path="raw/x.xml.gz", byte_count=42)

    monkeypatch.setattr("workers.persistence.publications.store_raw_payload", fake_store)
    await _persist_publications(db, result, Normalizer())
    assert result.records_rejected == 1
    assert result.records_inserted == 0
