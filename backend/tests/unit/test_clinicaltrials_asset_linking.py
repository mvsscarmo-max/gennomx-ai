"""Unit tests for ClinicalTrials.gov asset linking helpers."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from tests.conftest import FakeResult, FakeRow
from workers.tasks.ingest import (
    _extract_asset_candidates,
    _merge_unique,
    _select_development_stage,
    _upsert_drug_assets_from_trial,
    link_existing_trials_to_assets,
)


@pytest.mark.unit
class TestClinicalTrialsAssetLinking:
    def test_extract_asset_candidates_filters_non_therapeutic_interventions(self):
        parsed = SimpleNamespace(
            interventions=[
                {"type": "DRUG", "name": "  Tirzepatide ", "other_names": ["LY3298176"]},
                {"type": "PLACEBO", "name": "Placebo"},
                {"type": "BIOLOGICAL", "name": "Pembrolizumab", "other_names": []},
                {"type": "BEHAVIORAL", "name": "Exercise"},
            ]
        )

        candidates = _extract_asset_candidates(parsed)

        assert candidates == [
            {"primary_name": "Tirzepatide", "aliases": ["LY3298176"], "modality": "DRUG"},
            {"primary_name": "Pembrolizumab", "aliases": [], "modality": "BIOLOGICAL"},
        ]

    def test_merge_unique_is_case_insensitive_and_keeps_first_spelling(self):
        assert _merge_unique(["Keytruda"], [" keytruda ", "Pembrolizumab"]) == [
            "Keytruda",
            "Pembrolizumab",
        ]

    def test_select_development_stage_keeps_more_advanced_phase(self):
        assert _select_development_stage("PHASE3", "PHASE1") == "PHASE3"
        assert _select_development_stage("PHASE1", "PHASE2") == "PHASE2"

    async def test_upsert_drug_assets_from_trial_inserts_new_asset(self, mock_db):
        parsed = SimpleNamespace(
            nct_id="NCT00000001",
            phase_normalized="PHASE2",
            sponsor_name="Acme Bio",
            conditions=["Melanoma"],
            interventions=[{"type": "DRUG", "name": "Asset A", "other_names": ["Alias A"]}],
        )
        mock_db.execute = AsyncMock(
            side_effect=[
                FakeResult([]),
                FakeResult([]),
                FakeResult([]),
            ]
        )

        asset_ids = await _upsert_drug_assets_from_trial(
            db=mock_db,
            parsed=parsed,
            source_document_id="source-doc-1",
        )

        assert len(asset_ids) == 1
        insert_params = mock_db.execute.call_args_list[1][0][1]
        assert insert_params["primary_name"] == "Asset A"
        assert insert_params["aliases"] == ["Alias A"]
        assert insert_params["indication_names"] == ["Melanoma"]
        assert insert_params["sponsor_names"] == ["Acme Bio"]
        assert insert_params["development_stage"] == "PHASE2"

    async def test_link_existing_trials_to_assets_updates_trial_links(self, mock_db):
        mock_db.execute = AsyncMock(
            side_effect=[
                FakeResult(
                    [
                        FakeRow(
                            "trial-1",
                            "NCT00000001",
                            "PHASE2",
                            "Acme Bio",
                            ["Melanoma"],
                            [{"type": "DRUG", "name": "Asset A", "other_names": []}],
                            "source-doc-1",
                        )
                    ]
                ),
                FakeResult([]),
                FakeResult([]),
                FakeResult([]),
                FakeResult([]),
            ]
        )

        result = await link_existing_trials_to_assets(mock_db, limit=10)

        assert result["linked_trials"] == 1
        assert result["linked_assets"] == 1
        update_params = mock_db.execute.call_args_list[-1][0][1]
        assert update_params["trial_id"] == "trial-1"
        assert len(update_params["drug_asset_ids"]) == 1
        mock_db.commit.assert_awaited_once()
