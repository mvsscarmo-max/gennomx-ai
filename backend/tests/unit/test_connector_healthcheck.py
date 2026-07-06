"""Unit tests for connector healthcheck (VLAEG phase L — Link)."""

import httpx
import pytest

from workers.base.connector import BaseConnector, HealthcheckResult


@pytest.mark.unit
class TestHealthcheckResult:
    def test_defaults(self):
        r = HealthcheckResult("some_source")
        assert r.source_slug == "some_source"
        assert r.ok is False
        assert r.status == "unknown"
        assert r.latency_ms is None

    def test_to_dict_shape(self):
        r = HealthcheckResult("some_source")
        r.ok = True
        r.status = "ok"
        r.latency_ms = 12.345
        d = r.to_dict()
        assert d["source_slug"] == "some_source"
        assert d["ok"] is True
        assert d["status"] == "ok"
        assert d["latency_ms"] == 12.3
        assert "checked_at" in d


@pytest.mark.unit
class TestBaseConnectorDefaultHealthcheck:
    async def test_default_ok_when_config_valid(self):
        class Dummy(BaseConnector):
            SOURCE_SLUG = "dummy"

            async def run(self, job_type="incremental", **kwargs):  # pragma: no cover
                ...

            def validate_config(self) -> bool:
                return True

        result = await Dummy().healthcheck()
        assert result.ok is True
        assert result.status == "ok"

    async def test_default_config_error(self):
        class Dummy(BaseConnector):
            SOURCE_SLUG = "dummy"

            async def run(self, job_type="incremental", **kwargs):  # pragma: no cover
                ...

            def validate_config(self) -> bool:
                return False

        result = await Dummy().healthcheck()
        assert result.ok is False
        assert result.status == "config_error"


# ── ClinicalTrials.gov healthcheck with mocked httpx ──────────────────────────


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeClient:
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
        return _FakeResponse(self._payload)


@pytest.mark.unit
@pytest.mark.connector
class TestClinicalTrialsHealthcheck:
    def _connector(self):
        from workers.connectors.clinicaltrials.connector import ClinicalTrialsConnector

        return ClinicalTrialsConnector()

    async def test_ok(self, monkeypatch):
        from workers.connectors.clinicaltrials import connector as mod

        monkeypatch.setattr(
            mod.httpx, "AsyncClient", lambda **kw: _FakeClient(payload={"studies": [{"x": 1}]})
        )
        result = await self._connector().healthcheck()
        assert result.ok is True
        assert result.status == "ok"
        assert result.latency_ms is not None

    async def test_unexpected_shape(self, monkeypatch):
        from workers.connectors.clinicaltrials import connector as mod

        monkeypatch.setattr(
            mod.httpx, "AsyncClient", lambda **kw: _FakeClient(payload={"unexpected": True})
        )
        result = await self._connector().healthcheck()
        assert result.ok is False
        assert result.status == "error"

    async def test_timeout(self, monkeypatch):
        from workers.connectors.clinicaltrials import connector as mod

        monkeypatch.setattr(
            mod.httpx,
            "AsyncClient",
            lambda **kw: _FakeClient(exc=httpx.TimeoutException("slow")),
        )
        result = await self._connector().healthcheck()
        assert result.ok is False
        assert result.status == "unreachable"

    async def test_config_error(self, monkeypatch):
        from workers.connectors.clinicaltrials import connector as mod

        monkeypatch.setattr(mod, "CT_API_BASE", "")
        result = await self._connector().healthcheck()
        assert result.ok is False
        assert result.status == "config_error"
