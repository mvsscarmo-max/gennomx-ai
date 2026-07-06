"""Unit tests for the DailyMed connector: parser, normalizer, and healthcheck."""

import httpx
import pytest

from workers.connectors.dailymed.normalizer import DailyMedNormalizer
from workers.connectors.dailymed.parser import DailyMedParser

SAMPLE_RECORD = {
    "setid": "abc-123",
    "title": "ATENOLOL- atenolol tablet, film coated",
    "published_date": "2020-05-01T00:00:00",
}


@pytest.mark.unit
@pytest.mark.connector
class TestDailyMedParser:
    def test_parses_asset_name_from_title(self):
        parsed = DailyMedParser().parse_record(SAMPLE_RECORD)
        assert parsed.asset_name == "Atenolol"
        assert parsed.external_id == "abc-123"

    def test_builds_label_url(self):
        parsed = DailyMedParser().parse_record(SAMPLE_RECORD)
        assert parsed.label_url == (
            "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=abc-123"
        )

    def test_parses_published_date(self):
        from datetime import date

        parsed = DailyMedParser().parse_record(SAMPLE_RECORD)
        assert parsed.published_date == date(2020, 5, 1)

    def test_title_without_separator_falls_back_to_full_title(self):
        parsed = DailyMedParser().parse_record({"setid": "x", "title": "Simple Name Only"})
        assert parsed.asset_name == "Simple Name Only"

    def test_missing_setid_or_title_yields_none(self):
        parsed = DailyMedParser().parse_record({})
        assert parsed.external_id is None
        assert parsed.asset_name is None


@pytest.mark.unit
@pytest.mark.connector
class TestDailyMedNormalizer:
    def test_normalize_maps_to_regulatory_shape(self):
        parsed = DailyMedParser().parse_record(SAMPLE_RECORD)
        normalized = DailyMedNormalizer().normalize(parsed)
        assert normalized["agency"] == "FDA"
        assert normalized["region"] == "US"
        assert normalized["approval_status"] == "approved"
        assert normalized["application_number"] is None
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
class TestDailyMedHealthcheck:
    def _connector(self):
        from workers.connectors.dailymed.connector import DailyMedConnector

        return DailyMedConnector()

    async def test_ok(self, monkeypatch):
        from workers.connectors.dailymed import connector as mod

        monkeypatch.setattr(
            mod.httpx,
            "AsyncClient",
            lambda **kw: FakeClient(payload={"data": [], "metadata": {"total_elements": 10}}),
        )
        result = await self._connector().healthcheck()
        assert result.ok is True
        assert result.status == "ok"

    async def test_unexpected_shape(self, monkeypatch):
        from workers.connectors.dailymed import connector as mod

        monkeypatch.setattr(
            mod.httpx, "AsyncClient", lambda **kw: FakeClient(payload={"unexpected": True})
        )
        result = await self._connector().healthcheck()
        assert result.ok is False
        assert result.status == "error"

    async def test_timeout(self, monkeypatch):
        from workers.connectors.dailymed import connector as mod

        monkeypatch.setattr(
            mod.httpx, "AsyncClient", lambda **kw: FakeClient(exc=httpx.TimeoutException("slow"))
        )
        result = await self._connector().healthcheck()
        assert result.ok is False
        assert result.status == "unreachable"

    async def test_config_error(self, monkeypatch):
        from workers.connectors.dailymed import connector as mod

        monkeypatch.setattr(mod, "DAILYMED_API_BASE", "")
        result = await self._connector().healthcheck()
        assert result.ok is False
        assert result.status == "config_error"
