"""Resilience and traceability tests for ClinicalTrials.gov ingestion."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from workers.base.connector import ConnectorResult
from workers.connectors.clinicaltrials.connector import ClinicalTrialsConnector
from workers.storage.raw_payload import build_raw_object_path
from workers.tasks.ingest import (
    _has_fatal_connector_error,
    _insert_asset_evidence_snippet,
    _insert_evidence_snippet,
    _sync_trial_asset_links,
)


class JsonResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def json(self) -> dict:
        return self.payload


@pytest.mark.unit
async def test_pagination_streams_pages_without_accumulating_payloads(monkeypatch):
    connector = ClinicalTrialsConnector()
    connector.parser.parse_study = lambda raw: SimpleNamespace(nct_id=raw["id"])
    connector._fetch_page = AsyncMock(
        side_effect=[
            JsonResponse({"studies": [{"id": "A"}], "nextPageToken": "next"}),
            JsonResponse({"studies": [{"id": "B"}]}),
        ]
    )
    monkeypatch.setattr("workers.connectors.clinicaltrials.connector.asyncio.sleep", AsyncMock())
    batches: list[list[dict]] = []

    async def handler(batch: list[dict]) -> None:
        batches.append(batch)

    result = ConnectorResult("clinicaltrials_gov")
    await connector._paginate(object(), {}, None, result, handler)

    assert result.records_fetched == 2
    assert result.raw_payloads == []
    assert [[item["raw"]["id"] for item in batch] for batch in batches] == [["A"], ["B"]]


@pytest.mark.unit
async def test_pagination_marks_record_limit_as_incomplete():
    connector = ClinicalTrialsConnector()
    connector.parser.parse_study = lambda raw: SimpleNamespace(nct_id=raw["id"])
    connector._fetch_page = AsyncMock(
        return_value=JsonResponse({"studies": [{"id": "A"}, {"id": "B"}], "nextPageToken": "next"})
    )
    result = ConnectorResult("clinicaltrials_gov")

    await connector._paginate(object(), {}, 1, result)

    assert result.records_fetched == 1
    assert result.metadata["next_page_token"] == "next"
    assert result.errors[0]["type"] == "record_limit_reached"


@pytest.mark.unit
def test_raw_object_path_is_hash_addressed_and_sanitized():
    path = build_raw_object_path("clinicaltrials_gov", "NCT/00 01", "abc123")
    assert path.endswith("/NCT0001/abc123.json.gz")
    assert ".." not in path


@pytest.mark.unit
def test_record_limit_is_partial_not_fatal():
    result = ConnectorResult("clinicaltrials_gov")
    result.add_error("record_limit_reached", "continue in next scheduled run")
    assert not _has_fatal_connector_error(result)


@pytest.mark.unit
async def test_trial_evidence_is_literal_source_fragment(mock_db):
    raw = {
        "protocolSection": {
            "identificationModule": {"nctId": "NCT1", "briefTitle": "Exact title"},
            "statusModule": {"overallStatus": "RECRUITING"},
        }
    }
    await _insert_evidence_snippet(
        db=mock_db, source_document_id="doc-1", trial_id="trial-1", raw=raw
    )
    params = mock_db.execute.call_args_list[0][0][1]
    assert json.loads(params["text_excerpt"]) == raw["protocolSection"]
    field_params = [call.args[1] for call in mock_db.execute.call_args_list[1:]]
    assert {params["entity_field"] for params in field_params} == {"status_normalized"}


@pytest.mark.unit
async def test_asset_evidence_uses_exact_intervention_object(mock_db):
    intervention = {"type": "DRUG", "name": "Asset A", "otherNames": ["AA-1"]}
    raw = {"protocolSection": {"armsInterventionsModule": {"interventions": [intervention]}}}
    await _insert_asset_evidence_snippet(
        db=mock_db,
        source_document_id="doc-1",
        asset_id="asset-1",
        parsed=SimpleNamespace(nct_id="NCT1", phase_normalized="PHASE2"),
        primary_name="Asset A",
        raw=raw,
    )
    params = mock_db.execute.call_args[0][1]
    assert json.loads(params["text_excerpt"]) == intervention


@pytest.mark.unit
async def test_trial_asset_links_are_replaced_idempotently(mock_db):
    await _sync_trial_asset_links(mock_db, "trial-1", ["asset-1", "asset-2"], "document-1")

    assert mock_db.execute.await_count == 4
    history_params = mock_db.execute.call_args_list[0][0][1]
    assert history_params == {"trial_id": "trial-1"}
    delete_params = mock_db.execute.call_args_list[1][0][1]
    assert delete_params == {"trial_id": "trial-1"}
    inserted_assets = {call.args[1]["asset_id"] for call in mock_db.execute.call_args_list[2:]}
    assert inserted_assets == {"asset-1", "asset-2"}
