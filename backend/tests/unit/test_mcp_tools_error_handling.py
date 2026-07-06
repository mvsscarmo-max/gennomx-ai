"""Regression tests: MCP tool query errors must not leak exception text to clients."""

from unittest.mock import AsyncMock

import pytest

from app.mcp.tools.find_trials import find_trials
from app.mcp.tools.search_drugs import search_drugs

SENSITIVE_DETAIL = 'relation "drug_assets_secret_internal" does not exist at column 42'


@pytest.mark.unit
async def test_search_drugs_sanitizes_db_error():
    db = AsyncMock()
    db.execute.side_effect = Exception(SENSITIVE_DETAIL)

    result = await search_drugs({"query": "example"}, db=db)

    assert result["data"] == []
    assert result["count"] == 0
    assert result["limitations"] == ["Query failed"]
    assert SENSITIVE_DETAIL not in str(result)


@pytest.mark.unit
async def test_find_trials_sanitizes_db_error():
    db = AsyncMock()
    db.execute.side_effect = Exception(SENSITIVE_DETAIL)

    result = await find_trials({"drug_asset": "example"}, db=db)

    assert result["data"] == []
    assert result["count"] == 0
    assert result["limitations"] == ["Query failed"]
    assert SENSITIVE_DETAIL not in str(result)
