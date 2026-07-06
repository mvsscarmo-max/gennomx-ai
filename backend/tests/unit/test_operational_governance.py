from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api.v1.governance import ScraperDomainPolicy
from app.services.assertion_service import (
    AssertionService,
    GovernedCandidate,
    _merge_non_destructive,
)
from app.services.correction_service import CorrectionService
from app.services.data_policy import get_field_policy
from app.services.persistence_decision import PersistenceAction
from workers.base import scraping_policy
from workers.persistence import trials as trials_persistence
from workers.tasks import ingest


@pytest.mark.unit
def test_granularity_policy_is_deterministic_and_requires_dimensions():
    policy = get_field_policy("trial_result", "result_value")
    key = policy.granularity_key(
        {
            "trial_id": "NCT00000001",
            "arm": "Experimental",
            "population": "ITT",
            "timepoint": "Week 12",
            "measure": "ORR",
        }
    )
    assert key == (
        "trial_id=nct00000001|arm=experimental|population=itt|timepoint=week 12|measure=orr"
    )
    assert policy.expires_at() is None
    with pytest.raises(ValueError, match="missing_granularity_dimension"):
        policy.granularity_key({"trial_id": "NCT00000001"})


@pytest.mark.unit
def test_trial_status_policy_has_freshness_window():
    policy = get_field_policy("clinical_trial", "status_normalized")
    observed = datetime(2026, 1, 1, tzinfo=UTC)
    assert policy.granularity_key({"registry": "ClinicalTrials.gov"}) == (
        "registry=clinicaltrials.gov"
    )
    assert (policy.expires_at(observed) - observed).days == 14


@pytest.mark.unit
def test_unknown_field_policy_fails_closed():
    with pytest.raises(ValueError, match="undefined_data_policy"):
        get_field_policy("unknown", "field")


@pytest.mark.unit
def test_duckdb_staging_is_invoked_only_for_duplicate_trial_keys(monkeypatch):
    called = {}

    def fake_stage(rows, natural_key, updated_key):
        called["keys"] = (natural_key, updated_key)
        return [rows[-1]]

    monkeypatch.setattr(trials_persistence, "stage_and_deduplicate", fake_stage)
    payloads = [
        {"parsed": SimpleNamespace(nct_id="NCT00000001", last_update_date=None), "v": 1},
        {"parsed": SimpleNamespace(nct_id="NCT00000001", last_update_date=None), "v": 2},
    ]
    staged = ingest._stage_trial_payloads(payloads)
    assert called["keys"] == ("nct_id", "updated_at")
    assert staged[0]["v"] == 2


@pytest.mark.unit
def test_html_sanitizer_removes_active_content():
    pytest.importorskip("bs4")
    cleaned = scraping_policy.sanitize_html(
        b'<html><script>alert(1)</script><a href="javascript:x" onclick="x()">safe</a></html>'
    ).decode()
    assert "script" not in cleaned
    assert "javascript:" not in cleaned
    assert "onclick" not in cleaned
    assert "safe" in cleaned


@pytest.mark.unit
async def test_scrape_url_enforces_allowlist_and_public_resolution(monkeypatch):
    resolved = []

    async def fake_public(host):
        resolved.append(host)
        return ["203.0.113.10"]

    monkeypatch.setattr(scraping_policy, "_public_addresses", fake_public)
    policy = {
        "domain": "example.org",
        "allowed_schemes": ["https"],
        "allowed_hosts": ["api.example.org"],
    }
    addresses = await scraping_policy.validate_scrape_url("https://api.example.org/data", policy)
    assert resolved == ["api.example.org"]
    assert addresses == ["203.0.113.10"]
    with pytest.raises(ValueError, match="not_allowlisted"):
        await scraping_policy.validate_scrape_url("https://evil.example/data", policy)


@pytest.mark.unit
def test_pin_request_to_address_preserves_hostname_for_host_and_sni():
    """A4 regression: the outgoing request must target the validated IP while
    keeping the original hostname for Host/SNI, so the HTTP client never
    re-resolves DNS between validation and connection (rebinding window)."""
    pinned_url, hostname = scraping_policy._pin_request_to_address(
        "https://api.example.org/data?x=1", "203.0.113.10"
    )
    assert pinned_url == "https://203.0.113.10:443/data?x=1"
    assert hostname == "api.example.org"


@pytest.mark.unit
def test_pin_request_to_address_brackets_ipv6():
    pinned_url, hostname = scraping_policy._pin_request_to_address(
        "https://api.example.org/data", "2001:db8::1"
    )
    assert pinned_url == "https://[2001:db8::1]:443/data"
    assert hostname == "api.example.org"


@pytest.mark.unit
def test_pin_request_to_address_respects_explicit_port():
    pinned_url, _ = scraping_policy._pin_request_to_address(
        "http://api.example.org:80/data", "203.0.113.10"
    )
    assert pinned_url == "http://203.0.113.10:80/data"


@pytest.mark.unit
def test_operational_migration_contains_enforced_governance_structures():
    migration = Path("migrations/versions/0004_operational_governance.py").read_text(
        encoding="utf-8"
    )
    for token in (
        "evidence_maturity",
        "novelty_score",
        "clinical_impact_score",
        "retention_policies",
        "legal_holds",
        "archive_manifests",
        "archive_items",
        "scraper_domain_policies",
        "kill_switch",
    ):
        assert token in migration


@pytest.mark.unit
def test_retention_requires_archive_index_and_legal_hold_check_before_delete():
    source = Path("workers/tasks/retention.py").read_text(encoding="utf-8")
    assert "USING archive_items" in source
    assert "legal_holds" in source
    assert "ai.deleted_at IS NULL" in source
    assert "store_raw_payload" in source


@pytest.mark.unit
def test_scraper_domain_cannot_activate_without_approved_controls():
    base = {
        "owner": "Data Engineering",
        "purpose": "Collect official regulatory updates",
        "legal_basis": "Public official information",
        "terms_reviewed_at": datetime(2026, 6, 21, tzinfo=UTC),
        "robots_policy": "blocked",
        "active": True,
        "kill_switch": False,
    }
    with pytest.raises(ValueError, match="approved robots"):
        ScraperDomainPolicy(**base)


class _MappingResult:
    def __init__(self, row=None):
        self.row = row

    def mappings(self):
        return self

    def first(self):
        return self.row


@pytest.mark.unit
async def test_approved_correction_supersedes_and_creates_curated_assertion():
    correction = {
        "id": "correction-1",
        "entity_type": "clinical_trial",
        "entity_id": "00000000-0000-0000-0000-000000000001",
        "field_path": "status_normalized",
        "granularity_key": "registry=clinicaltrials.gov",
        "proposed_value": "COMPLETED",
        "previous_assertion_id": "00000000-0000-0000-0000-000000000002",
        "evidence_snippet_id": "00000000-0000-0000-0000-000000000003",
        "requested_by": "analyst-1",
    }
    db = SimpleNamespace(
        execute=AsyncMock(
            side_effect=[
                _MappingResult(correction),
                _MappingResult(),
                _MappingResult(),
                _MappingResult(),
            ]
        )
    )
    result = await CorrectionService(db).review(
        correction_id="correction-1",
        approve=True,
        reviewer="admin-1",
        decision_reason="Official evidence confirms corrected status",
    )
    statements = [str(call.args[0]) for call in db.execute.await_args_list]
    assert result["review_status"] == "approved"
    assert result["resulting_assertion_id"]
    assert any("lifecycle_status = 'superseded'" in sql for sql in statements)
    assert any("INSERT INTO field_assertions" in sql for sql in statements)
    assert any("UPDATE manual_corrections" in sql for sql in statements)


@pytest.mark.unit
async def test_generic_assertion_service_applies_policy_metadata_before_insert():
    db = SimpleNamespace(execute=AsyncMock(side_effect=[_MappingResult(None), _MappingResult()]))
    outcome = await AssertionService(db).persist(
        GovernedCandidate(
            entity_type="clinical_trial",
            entity_id="00000000-0000-0000-0000-000000000001",
            field_path="status_normalized",
            value="RECRUITING",
            dimensions={"registry": "ClinicalTrials.gov"},
            source_document_id="00000000-0000-0000-0000-000000000002",
            evidence_snippet_id="00000000-0000-0000-0000-000000000003",
            source_record_id="NCT00000001",
            source_version="2026-06-21",
            source_updated_at=datetime(2026, 6, 21, tzinfo=UTC),
            extraction_method="api_structured",
            confidence_score=0.99,
            source_type="official_registry",
            validation_status="confirmed",
        )
    )
    insert_call = db.execute.await_args_list[1]
    params = insert_call.args[1]
    assert outcome.action is PersistenceAction.INSERT
    assert params["granularity_key"] == "registry=clinicaltrials.gov"
    assert params["data_class"] == "operational"
    assert params["expires_at"] is not None


@pytest.mark.unit
def test_partial_enrichment_never_erases_existing_values():
    assert _merge_non_destructive(
        {"phase": "PHASE3", "sponsor": "Acme"},
        {"phase": None, "country": "BR"},
    ) == {"phase": "PHASE3", "sponsor": "Acme", "country": "BR"}
    assert _merge_non_destructive(["A", "B"], ["B", "C"]) == ["A", "B", "C"]
    with pytest.raises(ValueError, match="requires_object_or_list"):
        _merge_non_destructive("old", "new")
