"""Unit tests for ClinicalTrialsParser."""

import pytest

from workers.connectors.clinicaltrials.parser import ClinicalTrialsParser


@pytest.mark.unit
class TestClinicalTrialsParser:
    def setup_method(self):
        self.parser = ClinicalTrialsParser()

    def _minimal_study(self, overrides: dict | None = None) -> dict:
        base = {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT12345678",
                    "briefTitle": "Test Study",
                    "officialTitle": "Official Test Study Title",
                },
                "statusModule": {
                    "overallStatus": "RECRUITING",
                },
                "sponsorCollaboratorsModule": {
                    "leadSponsor": {"name": "Test Pharma Inc"},
                },
            }
        }
        if overrides:
            for key, val in overrides.items():
                base["protocolSection"][key] = val
        return base

    def test_parses_nct_id(self):
        study = self._minimal_study()
        parsed = self.parser.parse_study(study)
        assert parsed.nct_id == "NCT12345678"

    def test_parses_brief_title(self):
        study = self._minimal_study()
        parsed = self.parser.parse_study(study)
        assert parsed.brief_title == "Test Study"

    def test_parses_status(self):
        study = self._minimal_study()
        parsed = self.parser.parse_study(study)
        assert parsed.status == "RECRUITING"

    def test_parses_sponsor(self):
        study = self._minimal_study()
        parsed = self.parser.parse_study(study)
        assert parsed.sponsor_name == "Test Pharma Inc"

    def test_parses_conditions(self):
        study = self._minimal_study(
            {"conditionsModule": {"conditions": ["Type 2 Diabetes", "Obesity"]}}
        )
        parsed = self.parser.parse_study(study)
        assert "Type 2 Diabetes" in parsed.conditions

    def test_parses_phase(self):
        study = self._minimal_study({"designModule": {"phases": ["PHASE2", "PHASE3"]}})
        parsed = self.parser.parse_study(study)
        assert parsed.phase is not None

    def test_handles_missing_modules_gracefully(self):
        """A study with only the minimum fields should not raise."""
        minimal = {
            "protocolSection": {
                "identificationModule": {"nctId": "NCT99999999"},
                "statusModule": {"overallStatus": "UNKNOWN"},
            }
        }
        parsed = self.parser.parse_study(minimal)
        assert parsed.nct_id == "NCT99999999"
        assert parsed.conditions == []

    def test_parse_date_handles_year_only(self):
        date = self.parser._parse_date("2023")
        assert date is not None
        assert date.year == 2023

    def test_parse_date_handles_year_month(self):
        date = self.parser._parse_date("2024-03")
        assert date is not None
        assert date.month == 3

    def test_parse_date_handles_full_date(self):
        date = self.parser._parse_date("2025-06-15")
        assert date is not None
        assert date.day == 15

    def test_parse_date_returns_none_for_invalid(self):
        date = self.parser._parse_date("not-a-date")
        assert date is None

    def test_parse_date_returns_none_for_empty(self):
        assert self.parser._parse_date("") is None
        assert self.parser._parse_date(None) is None
