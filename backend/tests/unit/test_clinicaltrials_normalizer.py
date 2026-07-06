"""Unit tests for ClinicalTrialsNormalizer."""

import pytest

from workers.connectors.clinicaltrials.normalizer import ClinicalTrialsNormalizer


@pytest.mark.unit
class TestNormalizer:
    def setup_method(self):
        self.norm = ClinicalTrialsNormalizer()

    def test_status_map_recruiting(self):
        result = self.norm.STATUS_MAP.get("RECRUITING")
        assert result == "RECRUITING"

    def test_status_map_completed(self):
        result = self.norm.STATUS_MAP.get("COMPLETED")
        assert result == "COMPLETED"

    def test_status_map_unknown_falls_back(self):
        result = self.norm.STATUS_MAP.get("SOME_UNKNOWN_STATUS", "UNKNOWN")
        assert result == "UNKNOWN"

    def test_phase_map_phase_2(self):
        result = self.norm.PHASE_MAP.get("PHASE2")
        assert result in ("PHASE_2", "Phase 2", "PHASE2")

    def test_extract_drug_names_returns_drug_interventions(self):
        from workers.connectors.clinicaltrials.parser import ParsedTrial

        trial = ParsedTrial.__new__(ParsedTrial)
        trial.interventions = [
            {"type": "DRUG", "name": "Tirzepatide"},
            {"type": "PLACEBO", "name": "Placebo"},
            {"type": "BIOLOGICAL", "name": "Pembrolizumab"},
        ]
        names = ClinicalTrialsNormalizer.extract_drug_names(trial)
        assert "Tirzepatide" in names
        assert "Pembrolizumab" in names
        assert "Placebo" not in names

    def test_extract_drug_names_empty_for_no_drug(self):
        from workers.connectors.clinicaltrials.parser import ParsedTrial

        trial = ParsedTrial.__new__(ParsedTrial)
        trial.interventions = [{"type": "BEHAVIORAL", "name": "Exercise"}]
        names = ClinicalTrialsNormalizer.extract_drug_names(trial)
        assert names == []
