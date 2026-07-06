"""Unit tests for MCP server auth and rate limiting logic."""

import time

import pytest
from fastapi import HTTPException


@pytest.mark.unit
class TestMCPAuthentication:
    def test_empty_mcp_token_raises_401(self):
        """Empty X-MCP-Token header must be rejected."""
        from app.mcp.server import _authenticate_mcp

        with pytest.raises(HTTPException) as exc_info:
            _authenticate_mcp(None)
        assert exc_info.value.status_code == 401

    def test_invalid_token_raises_401(self):
        from app.mcp.server import _authenticate_mcp

        with pytest.raises(HTTPException) as exc_info:
            _authenticate_mcp("definitely-not-a-valid-token-xyz999")
        assert exc_info.value.status_code == 401

    def test_valid_test_token_accepted(self):
        """Tokens set via env var in conftest should be accepted."""
        from app.config import get_settings
        from app.mcp.server import _authenticate_mcp

        settings = get_settings()
        # The conftest sets MCP_TOKEN_CHATGPT=test-chatgpt-token
        client = _authenticate_mcp(settings.MCP_TOKEN_CHATGPT)
        assert client == "chatgpt"


@pytest.mark.unit
class TestMCPRateLimiter:
    def test_rate_limiter_allows_first_call(self):
        """First call to a fresh token should not raise."""
        from app.mcp.server import _check_rate_limit, _rate_buckets

        token = f"test-fresh-{time.time()}"
        _rate_buckets.pop(token, None)
        _check_rate_limit(token)  # Should not raise

    def test_rate_limiter_blocks_after_limit_exceeded(self):
        """Filling the bucket beyond the limit should raise 429."""
        from app.config import get_settings
        from app.mcp.server import _check_rate_limit, _rate_buckets

        settings = get_settings()
        limit = settings.MCP_RATE_LIMIT_PER_MINUTE

        token = f"test-overflow-{time.time()}"
        # Pre-fill with exactly `limit` recent timestamps
        _rate_buckets[token] = [time.time()] * limit

        with pytest.raises(HTTPException) as exc_info:
            _check_rate_limit(token)
        assert exc_info.value.status_code == 429

    def test_rate_limiter_ignores_old_timestamps(self):
        """Timestamps older than the window should be pruned and not count."""
        from app.config import get_settings
        from app.mcp.server import _check_rate_limit, _rate_buckets

        settings = get_settings()
        limit = settings.MCP_RATE_LIMIT_PER_MINUTE

        token = f"test-old-timestamps-{time.time()}"
        old = time.time() - 120  # 2 minutes ago — outside 60s window
        _rate_buckets[token] = [old] * limit

        # Should NOT raise — all old timestamps are out of window
        _check_rate_limit(token)


@pytest.mark.unit
class TestMCPBlocklist:
    def test_blocked_tools_are_rejected_by_name(self):
        """The in-function blocklist must include dangerous tool names."""
        import inspect

        from app.mcp import server

        source = inspect.getsource(server.mcp_call)
        assert "admin" in source
        assert "execute_sql" in source
        assert "delete" in source
        assert "update" in source
        assert "insert" in source


@pytest.mark.unit
class TestMCPDispatch:
    async def test_dispatch_passes_explicit_db_session(self, mock_db, monkeypatch):
        """MCP tools must receive the FastAPI-injected DB session, not request.state."""
        from app.mcp import server

        received = {}

        async def fake_tool(arguments, db=None):
            received["arguments"] = arguments
            received["db"] = db
            return {"data": [{"ok": True}], "count": 1}

        monkeypatch.setattr(server.tools, "search_drugs", fake_tool)

        result = await server._dispatch_tool("search_drugs", {"query": "abc"}, mock_db)

        assert result["count"] == 1
        assert received["arguments"] == {"query": "abc"}
        assert received["db"] is mock_db


@pytest.mark.unit
class TestMCPAuthorization:
    def test_scope_allows_configured_tool(self, monkeypatch):
        from app.config import get_settings
        from app.mcp.server import _authorize_tool

        monkeypatch.setenv("MCP_SCOPES_CHATGPT", "search_drugs")
        get_settings.cache_clear()
        _authorize_tool("chatgpt", "search_drugs")

    def test_scope_denies_unconfigured_tool(self, monkeypatch):
        from app.config import get_settings
        from app.mcp.server import _authorize_tool

        monkeypatch.setenv("MCP_SCOPES_CHATGPT", "search_drugs")
        get_settings.cache_clear()
        with pytest.raises(HTTPException) as exc_info:
            _authorize_tool("chatgpt", "find_trials")
        assert exc_info.value.status_code == 403

    def test_extract_accessed_entities_is_bounded(self):
        from app.mcp.server import _extract_accessed_entities

        entities, types = _extract_accessed_entities(
            {"trials": [{"nct_id": f"NCT{i:08d}"} for i in range(150)]}
        )
        assert len(entities) == 100
        assert types == ["trial"]
