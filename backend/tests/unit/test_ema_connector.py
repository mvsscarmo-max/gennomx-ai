"""Unit tests for the EMA connector: XLSX parser, normalizer, and healthcheck."""

from io import BytesIO

import httpx
import pytest

from workers.connectors.ema.normalizer import EMANormalizer
from workers.connectors.ema.parser import EMAParser


def _build_sample_xlsx() -> bytes:
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(
        [
            "Medicine name",
            "International non-proprietary name (INN) / common name",
            "Active substance",
            "Authorisation status",
            "Marketing authorisation date",
            "Therapeutic area (MeSH)",
            "Product number",
            "Orphan medicine",
            "URL",
        ]
    )
    ws.append(
        [
            "Keytruda",
            "pembrolizumab",
            "pembrolizumab",
            "Authorised",
            "2015-07-17",
            "Melanoma",
            "EMEA/H/C/003820",
            "No",
            "https://ema.europa.eu/keytruda",
        ]
    )
    ws.append(["", "", "", "", "", "", "", "", ""])  # blank row must be skipped
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.mark.unit
@pytest.mark.connector
class TestEMAParser:
    def test_parses_medicine_row(self):
        records = list(EMAParser().parse_workbook(_build_sample_xlsx()))
        assert len(records) == 1
        record = records[0]
        assert record.asset_name == "Keytruda"
        assert "Pembrolizumab" in record.asset_aliases
        assert record.approval_status == "approved"
        assert record.product_number == "EMEA/H/C/003820"
        assert record.orphan is False
        assert record.epar_url == "https://ema.europa.eu/keytruda"

    def test_deduplicates_aliases(self):
        records = list(EMAParser().parse_workbook(_build_sample_xlsx()))
        aliases = records[0].asset_aliases
        assert len(aliases) == len({a.casefold() for a in aliases})

    def test_authorisation_date_parsed(self):
        from datetime import date

        records = list(EMAParser().parse_workbook(_build_sample_xlsx()))
        assert records[0].authorisation_date == date(2015, 7, 17)

    def test_missing_header_row_yields_no_records(self):
        import openpyxl

        wb = openpyxl.Workbook()
        buf = BytesIO()
        wb.save(buf)
        records = list(EMAParser().parse_workbook(buf.getvalue()))
        assert records == []


@pytest.mark.unit
@pytest.mark.connector
class TestEMANormalizer:
    def test_normalize_maps_to_regulatory_shape(self):
        records = list(EMAParser().parse_workbook(_build_sample_xlsx()))
        normalized = EMANormalizer().normalize(records[0])
        assert normalized["agency"] == "EMA"
        assert normalized["region"] == "EU"
        assert normalized["approval_status"] == "approved"
        assert normalized["application_number"] == "EMEA/H/C/003820"

    def test_orphan_flag_becomes_special_designation(self):
        record = next(iter(EMAParser().parse_workbook(_build_sample_xlsx())))
        record.orphan = True
        normalized = EMANormalizer().normalize(record)
        assert "orphan_drug" in normalized["special_designations"]


class FakeResponse:
    def __init__(self, status_code=200, headers=None):
        self.status_code = status_code
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=self)


class FakeClient:
    def __init__(self, *, status_code=200, headers=None, exc=None):
        self._status_code = status_code
        self._headers = headers or {}
        self._exc = exc

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def head(self, *args, **kwargs):
        if self._exc is not None:
            raise self._exc
        return FakeResponse(self._status_code, self._headers)

    async def get(self, *args, **kwargs):
        if self._exc is not None:
            raise self._exc
        return FakeResponse(self._status_code, self._headers)


@pytest.mark.unit
@pytest.mark.connector
class TestEMAHealthcheck:
    def _connector(self):
        from workers.connectors.ema.connector import EMAConnector

        return EMAConnector()

    async def test_ok(self, monkeypatch):
        from workers.connectors.ema import connector as mod

        monkeypatch.setattr(
            mod.httpx,
            "AsyncClient",
            lambda **kw: FakeClient(status_code=200, headers={"content-length": "1024"}),
        )
        result = await self._connector().healthcheck()
        assert result.ok is True
        assert result.status == "ok"

    async def test_timeout(self, monkeypatch):
        from workers.connectors.ema import connector as mod

        monkeypatch.setattr(
            mod.httpx, "AsyncClient", lambda **kw: FakeClient(exc=httpx.TimeoutException("slow"))
        )
        result = await self._connector().healthcheck()
        assert result.ok is False
        assert result.status == "unreachable"

    async def test_config_error(self, monkeypatch):
        from workers.connectors.ema import connector as mod

        monkeypatch.setattr(mod, "EMA_EXPORT_URL", "")
        result = await self._connector().healthcheck()
        assert result.ok is False
        assert result.status == "config_error"
