"""Unit tests for the openFDA connector: parser, normalizer, and healthcheck."""

import httpx
import pytest

from workers.connectors.openfda.normalizer import OpenFDANormalizer
from workers.connectors.openfda.parser import OpenFDAParser

SAMPLE_RECORD = {
    "application_number": "NDA020702",
    "sponsor_name": "PFIZER INC",
    "products": [
        {
            "brand_name": "Lipitor",
            "active_ingredients": [{"name": "atorvastatin calcium", "strength": "10MG"}],
        }
    ],
    "submissions": [
        {
            "submission_status": "AP",
            "submission_status_date": "19961217",
            "review_priority": "STANDARD",
            "submission_class_code_description": "Type 1 - New Molecular Entity",
        },
        {
            "submission_status": "AP",
            "submission_status_date": "20000101",
            "review_priority": "PRIORITY",
            "submission_class_code_description": "Type 5 - Labeling",
        },
    ],
    "openfda": {"brand_name": ["Lipitor"], "generic_name": ["atorvastatin calcium"]},
}


@pytest.mark.unit
@pytest.mark.connector
class TestOpenFDAParser:
    def test_parses_asset_name_and_aliases(self):
        parsed = OpenFDAParser().parse_record(SAMPLE_RECORD)
        assert parsed.asset_name == "Lipitor"
        assert "Atorvastatin Calcium" in parsed.asset_aliases
        assert parsed.application_number == "NDA020702"

    def test_takes_latest_submission_for_status_and_date(self):
        parsed = OpenFDAParser().parse_record(SAMPLE_RECORD)
        assert parsed.approval_status == "approved"
        from datetime import date

        assert parsed.approval_date == date(2000, 1, 1)
        assert parsed.submission_date == date(1996, 12, 17)

    def test_priority_review_becomes_special_designation(self):
        parsed = OpenFDAParser().parse_record(SAMPLE_RECORD)
        assert "priority_review" in parsed.special_designations

    def test_missing_products_yields_no_asset_name(self):
        parsed = OpenFDAParser().parse_record({"application_number": "NDA000000"})
        assert parsed.asset_name is None

    def test_malformed_submission_date_is_ignored(self):
        record = {
            "application_number": "NDA111111",
            "products": [{"brand_name": "Test Drug"}],
            "submissions": [{"submission_status": "AP", "submission_status_date": "not-a-date"}],
        }
        parsed = OpenFDAParser().parse_record(record)
        assert parsed.approval_date is None
        assert parsed.approval_status is None


@pytest.mark.unit
@pytest.mark.connector
class TestOpenFDANormalizer:
    def test_normalize_maps_to_regulatory_shape(self):
        parsed = OpenFDAParser().parse_record(SAMPLE_RECORD)
        normalized = OpenFDANormalizer().normalize(parsed)
        assert normalized["agency"] == "FDA"
        assert normalized["region"] == "US"
        assert normalized["asset_name"] == "Lipitor"
        assert normalized["application_number"] == "NDA020702"
        assert normalized["source_updated_at"] is not None


class FakeResponse:
    def __init__(self, payload=None):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, *, payload=None, exc=None):
        self._payload = payload
        self._exc = exc

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get(self, *args, **kwargs):
        if self._exc is not None:
            raise self._exc
        return FakeResponse(self._payload)


@pytest.mark.unit
@pytest.mark.connector
class TestOpenFDAHealthcheck:
    def _connector(self):
        from workers.connectors.openfda.connector import OpenFDAConnector

        return OpenFDAConnector()

    async def test_ok(self, monkeypatch):
        from workers.connectors.openfda import connector as mod

        monkeypatch.setattr(
            mod.httpx,
            "AsyncClient",
            lambda **kw: FakeClient(payload={"results": [], "meta": {"results": {"total": 1}}}),
        )
        result = await self._connector().healthcheck()
        assert result.ok is True
        assert result.status == "ok"

    async def test_unexpected_shape(self, monkeypatch):
        from workers.connectors.openfda import connector as mod

        monkeypatch.setattr(
            mod.httpx, "AsyncClient", lambda **kw: FakeClient(payload={"unexpected": True})
        )
        result = await self._connector().healthcheck()
        assert result.ok is False
        assert result.status == "error"

    async def test_timeout(self, monkeypatch):
        from workers.connectors.openfda import connector as mod

        monkeypatch.setattr(
            mod.httpx, "AsyncClient", lambda **kw: FakeClient(exc=httpx.TimeoutException("slow"))
        )
        result = await self._connector().healthcheck()
        assert result.ok is False
        assert result.status == "unreachable"

    async def test_config_error(self, monkeypatch):
        from workers.connectors.openfda import connector as mod

        monkeypatch.setattr(mod, "OPENFDA_API_BASE", "")
        result = await self._connector().healthcheck()
        assert result.ok is False
        assert result.status == "config_error"
