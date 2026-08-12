import json
from pathlib import Path

import pytest

from tests.conftest import FakeResult, FakeRow
from workers.connectors.clinicaltrials.parser import ClinicalTrialsParser
from workers.persistence.clinical_outcomes import persist_clinical_outcomes


class ProjectionDB:
    def __init__(self):
        self.evidence: dict[str, str] = {}
        self.endpoints: dict[tuple, tuple[str, str]] = {}
        self.results: dict[tuple, tuple[str, str]] = {}
        self.events: dict[tuple, tuple[str, str]] = {}
        self.insert_counts = {"endpoints": 0, "results": 0, "adverse_events": 0}
        self.result_values: list[str] = []

    async def execute(self, statement, params=None):
        sql = " ".join(str(statement).split())
        params = params or {}
        if sql.startswith("INSERT INTO evidence_snippets"):
            if params["field"] in self.evidence:
                return FakeResult([])
            self.evidence[params["field"]] = params["id"]
            return FakeResult([FakeRow(params["id"])])
        if sql.startswith("SELECT id::text FROM evidence_snippets"):
            return FakeResult([FakeRow(self.evidence[params["field"]])])
        if "FROM endpoints" in sql and sql.startswith("SELECT"):
            key = (
                params["trial_id"],
                params.get("arm_id"),
                params["name"].casefold(),
                params.get("timepoint"),
            )
            return FakeResult([FakeRow(*self.endpoints[key])] if key in self.endpoints else [])
        if sql.startswith("INSERT INTO endpoints"):
            key = (
                params["trial_id"],
                params.get("arm_id"),
                params["name"].casefold(),
                params.get("timepoint"),
            )
            fingerprint = json.loads(params["metadata"])["source_fingerprint"]
            self.endpoints[key] = (params["id"], fingerprint)
            self.insert_counts["endpoints"] += 1
        elif "FROM trial_results" in sql and sql.startswith("SELECT"):
            key = (
                params["trial_id"],
                params["endpoint_id"],
                params.get("arm_id"),
                params.get("timepoint"),
                params.get("population"),
            )
            return FakeResult([FakeRow(*self.results[key])] if key in self.results else [])
        elif sql.startswith("INSERT INTO trial_results"):
            key = (
                params["trial_id"],
                params["endpoint_id"],
                params.get("arm_id"),
                params.get("timepoint"),
                params.get("population"),
            )
            fingerprint = json.loads(params["metadata"])["source_fingerprint"]
            self.results[key] = (params["id"], fingerprint)
            self.insert_counts["results"] += 1
            self.result_values.append(params["result_value"])
        elif "FROM adverse_events" in sql and sql.startswith("SELECT"):
            key = (params["trial_id"], params["name"].casefold(), params.get("population"))
            return FakeResult([FakeRow(*self.events[key])] if key in self.events else [])
        elif sql.startswith("INSERT INTO adverse_events"):
            key = (params["trial_id"], params["name"].casefold(), params.get("population"))
            fingerprint = json.loads(params["metadata"])["source_fingerprint"]
            self.events[key] = (params["id"], fingerprint)
            self.insert_counts["adverse_events"] += 1
        return FakeResult([])


@pytest.mark.unit
async def test_fixture_persistence_is_idempotent_and_preserves_literal_results():
    fixture = Path(__file__).parents[1] / "fixtures/clinicaltrials/study_with_results.json"
    raw = json.loads(fixture.read_text(encoding="utf-8"))
    parsed = ClinicalTrialsParser().parse_study(raw)
    db = ProjectionDB()

    first = await persist_clinical_outcomes(
        db,
        trial_id="00000000-0000-0000-0000-000000000007",
        source_document_id="00000000-0000-0000-0000-000000000009",
        parsed=parsed,
        raw=raw,
    )
    first_insert_counts = dict(db.insert_counts)
    second = await persist_clinical_outcomes(
        db,
        trial_id="00000000-0000-0000-0000-000000000007",
        source_document_id="00000000-0000-0000-0000-000000000009",
        parsed=parsed,
        raw=raw,
    )

    assert first == {"endpoints": 2, "results": 3, "adverse_events": 3}
    assert second == {"endpoints": 2, "results": 0, "adverse_events": 0}
    assert db.insert_counts == first_insert_counts
    assert any("-2.4" in value for value in db.result_values)
    assert any("Not estimable" in value for value in db.result_values)
    assert set(db.evidence) == {"planned_outcomes", "posted_outcomes", "adverse_events"}
