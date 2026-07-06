"""Contract test for the complete MCP HTTP request path."""

from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app


@pytest.mark.integration
async def test_mcp_http_call_authenticates_dispatches_and_audits(mock_db, monkeypatch):
    from app.mcp import server

    async def override_db():
        yield mock_db

    monkeypatch.setattr(server, "_check_distributed_rate_limit", AsyncMock())
    monkeypatch.setattr(
        server,
        "_dispatch_tool",
        AsyncMock(
            return_value={
                "data": [{"id": "asset-1", "name": "Example Drug"}],
                "count": 1,
                "limitations": [],
                "gaps": [],
            }
        ),
    )
    persist_log = AsyncMock()
    monkeypatch.setattr(server, "_persist_mcp_log", persist_log)
    app.dependency_overrides[get_db] = override_db

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/mcp/call",
                headers={"X-MCP-Token": "test-chatgpt-token"},
                json={"tool": "search_drugs", "arguments": {"query": "example"}},
            )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["tool"] == "search_drugs"
    assert payload["count"] == 1
    server._dispatch_tool.assert_awaited_once_with("search_drugs", {"query": "example"}, mock_db)
    persist_log.assert_awaited_once()
    mock_db.commit.assert_awaited_once()


@pytest.mark.integration
async def test_mcp_http_call_without_token_rejects_without_db_write(mock_db, monkeypatch):
    """An unauthenticated request is the cheapest attack path and must never

    spend a DB write/commit — only the in-memory pre-auth limiter and a
    structured log line guard against flooding.
    """
    from app.mcp import server

    async def override_db():
        yield mock_db

    monkeypatch.setattr(server, "_check_pre_auth_rate_limit", AsyncMock())
    persist_log = AsyncMock()
    monkeypatch.setattr(server, "_persist_mcp_log", persist_log)
    app.dependency_overrides[get_db] = override_db

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/mcp/call",
                json={"tool": "search_drugs", "arguments": {"query": "example"}},
            )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 401
    persist_log.assert_not_awaited()
    mock_db.execute.assert_not_awaited()
    mock_db.commit.assert_not_awaited()
