"""Unit tests for PubMed connector healthcheck (VLAEG phase L — Link)."""

import httpx
import pytest


class FakeResponse:
    def __init__(self, payload=None, text=None):
        self._payload = payload
        self._text = text

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload

    @property
    def text(self):
        return self._text or ""


class FakeClient:
    def __init__(self, *, payload=None, text=None, exc=None, status=200):
        self._payload = payload
        self._text = text
        self._exc = exc
        self._status = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get(self, *args, **kwargs):
        if self._exc is not None:
            raise self._exc
        resp = FakeResponse(self._payload, self._text)
        return resp


@pytest.mark.unit
@pytest.mark.connector
class TestPubMedHealthcheck:
    def _connector(self):
        from workers.connectors.pubmed.connector import PubMedConnector

        return PubMedConnector()

    async def test_ok(self, monkeypatch):
        from workers.connectors.pubmed import connector as mod

        monkeypatch.setattr(
            mod.httpx,
            "AsyncClient",
            lambda **kw: FakeClient(payload={"einforesult": {"dbinfo": {"description": "PubMed"}}}),
        )
        result = await self._connector().healthcheck()
        assert result.ok is True
        assert result.status == "ok"
        assert result.latency_ms is not None

    async def test_unexpected_shape(self, monkeypatch):
        from workers.connectors.pubmed import connector as mod

        monkeypatch.setattr(
            mod.httpx,
            "AsyncClient",
            lambda **kw: FakeClient(payload={"unexpected": True}),
        )
        result = await self._connector().healthcheck()
        assert result.ok is False
        assert result.status == "error"

    async def test_timeout(self, monkeypatch):
        from workers.connectors.pubmed import connector as mod

        monkeypatch.setattr(
            mod.httpx,
            "AsyncClient",
            lambda **kw: FakeClient(exc=httpx.TimeoutException("slow")),
        )
        result = await self._connector().healthcheck()
        assert result.ok is False
        assert result.status == "unreachable"

    async def test_config_error(self, monkeypatch):
        from workers.connectors.pubmed import connector as mod

        monkeypatch.setattr(mod, "PUBMED_API_BASE", "")
        result = await self._connector().healthcheck()
        assert result.ok is False
        assert result.status == "config_error"
