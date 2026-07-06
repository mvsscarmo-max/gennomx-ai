"""Unit tests for the Open Targets connector: parser, normalizer, and healthcheck."""

import httpx
import pytest

from workers.connectors.opentargets.normalizer import OpenTargetsNormalizer
from workers.connectors.opentargets.parser import OpenTargetsParser

SAMPLE_ROW = {
    "score": 0.87,
    "target": {
        "id": "ENSG00000141510",
        "approvedSymbol": "TP53",
        "approvedName": "tumor protein p53",
        "biotype": "protein_coding",
        "synonyms": [{"label": "p53"}, {"label": "LFS1"}],
        "proteinIds": [{"id": "P04637", "source": "uniprot_swissprot"}],
    },
}


@pytest.mark.unit
@pytest.mark.connector
class TestOpenTargetsParser:
    def test_parses_symbol_and_name(self):
        parsed = OpenTargetsParser().parse_associated_target_row(SAMPLE_ROW, "NSCLC")
        assert parsed.symbol == "TP53"
        assert parsed.name == "tumor protein p53"
        assert parsed.external_id == "ENSG00000141510"
        assert parsed.disease_name == "NSCLC"

    def test_parses_aliases_from_synonyms(self):
        parsed = OpenTargetsParser().parse_associated_target_row(SAMPLE_ROW, "NSCLC")
        assert "p53" in parsed.aliases
        assert "LFS1" in parsed.aliases

    def test_parses_uniprot_from_swissprot_source_only(self):
        row = {
            "score": 0.5,
            "target": {
                "id": "ENSG0001",
                "approvedSymbol": "X",
                "proteinIds": [
                    {"id": "OTHER1", "source": "ensembl_PRO"},
                    {"id": "P99999", "source": "uniprot_swissprot"},
                ],
            },
        }
        parsed = OpenTargetsParser().parse_associated_target_row(row, None)
        assert parsed.uniprot_id == "P99999"

    def test_score_bounds(self):
        parsed = OpenTargetsParser().parse_associated_target_row(SAMPLE_ROW, "NSCLC")
        assert parsed.open_targets_score == 0.87


@pytest.mark.unit
@pytest.mark.connector
class TestOpenTargetsNormalizer:
    def test_normalize_maps_biotype_and_external_ids(self):
        parsed = OpenTargetsParser().parse_associated_target_row(SAMPLE_ROW, "NSCLC")
        normalized = OpenTargetsNormalizer().normalize(parsed)
        assert normalized["symbol"] == "TP53"
        assert normalized["target_type"] == "protein"
        assert normalized["external_ids"]["ensembl"] == "ENSG00000141510"
        assert normalized["external_ids"]["uniprot"] == "P04637"
        assert normalized["associated_indication_names"] == ["NSCLC"]

    def test_normalize_defaults_unknown_biotype_to_gene(self):
        parsed = OpenTargetsParser().parse_associated_target_row(
            {"score": 0.1, "target": {"id": "X", "approvedSymbol": "X", "biotype": "unknown"}},
            None,
        )
        normalized = OpenTargetsNormalizer().normalize(parsed)
        assert normalized["target_type"] == "gene"
        assert normalized["associated_indication_names"] == []


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

    async def post(self, *args, **kwargs):
        if self._exc is not None:
            raise self._exc
        return FakeResponse(self._payload)


@pytest.mark.unit
@pytest.mark.connector
class TestOpenTargetsHealthcheck:
    def _connector(self):
        from workers.connectors.opentargets.connector import OpenTargetsConnector

        return OpenTargetsConnector()

    async def test_ok(self, monkeypatch):
        from workers.connectors.opentargets import connector as mod

        monkeypatch.setattr(
            mod.httpx,
            "AsyncClient",
            lambda **kw: FakeClient(
                payload={"data": {"meta": {"apiVersion": {"x": 24, "y": 0, "z": 0}}}}
            ),
        )
        result = await self._connector().healthcheck()
        assert result.ok is True
        assert result.status == "ok"

    async def test_graphql_errors_marked_error(self, monkeypatch):
        from workers.connectors.opentargets import connector as mod

        monkeypatch.setattr(
            mod.httpx,
            "AsyncClient",
            lambda **kw: FakeClient(payload={"data": None, "errors": [{"message": "bad"}]}),
        )
        result = await self._connector().healthcheck()
        assert result.ok is False
        assert result.status == "error"

    async def test_timeout(self, monkeypatch):
        from workers.connectors.opentargets import connector as mod

        monkeypatch.setattr(
            mod.httpx, "AsyncClient", lambda **kw: FakeClient(exc=httpx.TimeoutException("slow"))
        )
        result = await self._connector().healthcheck()
        assert result.ok is False
        assert result.status == "unreachable"

    async def test_config_error(self, monkeypatch):
        from workers.connectors.opentargets import connector as mod

        monkeypatch.setattr(mod, "OPEN_TARGETS_URL", "")
        result = await self._connector().healthcheck()
        assert result.ok is False
        assert result.status == "config_error"
