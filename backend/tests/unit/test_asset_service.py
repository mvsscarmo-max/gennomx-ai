"""Unit tests for AssetService."""

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError
from app.services.asset_service import AssetService
from tests.conftest import FakeResult, FakeRow


@pytest.mark.unit
class TestAssetServiceListAssets:
    async def test_returns_empty_when_no_rows(self, mock_db):
        mock_db.execute = AsyncMock(
            side_effect=[
                FakeResult([], scalar_value=0),
                FakeResult([]),
            ]
        )
        service = AssetService(mock_db)
        items, total = await service.list_assets()

        assert total == 0
        assert items == []

    async def test_returns_items_with_correct_shape(self, mock_db):
        now = datetime(2026, 1, 1)
        row = FakeRow(
            str(uuid4()),
            "Semaglutide",
            ["OZempic", "Wegovy"],
            "semaglutide",
            "Small molecule",
            "Phase 3",
            ["Obesity", "T2D"],
            ["GLP1R"],
            ["Novo Nordisk"],
            0.95,
            now,
        )
        mock_db.execute = AsyncMock(
            side_effect=[
                FakeResult([], scalar_value=1),
                FakeResult([row]),
            ]
        )
        service = AssetService(mock_db)
        items, total = await service.list_assets()

        assert total == 1
        assert len(items) == 1
        item = items[0]
        assert item["primary_name"] == "Semaglutide"
        assert item["aliases"] == ["OZempic", "Wegovy"]
        assert item["source_confidence"] == 0.95
        assert item["updated_at"] == now.isoformat()

    async def test_applies_q_filter(self, mock_db):
        mock_db.execute = AsyncMock(
            side_effect=[
                FakeResult([], scalar_value=0),
                FakeResult([]),
            ]
        )
        service = AssetService(mock_db)
        await service.list_assets(q="sema")

        # Verify SQL was called twice (count + data) with params including q
        assert mock_db.execute.call_count == 2
        first_call_params = mock_db.execute.call_args_list[0][0][1]
        assert "q" in first_call_params
        assert "%sema%" in first_call_params["q"]

    async def test_applies_phase_filter(self, mock_db):
        """A2 regression: `phase` must reach the SQL filter, not be silently dropped."""
        mock_db.execute = AsyncMock(
            side_effect=[
                FakeResult([], scalar_value=0),
                FakeResult([]),
            ]
        )
        service = AssetService(mock_db)
        await service.list_assets(phase="phase1")

        count_sql = mock_db.execute.call_args_list[0][0][0]
        first_call_params = mock_db.execute.call_args_list[0][0][1]
        assert "development_stage" in str(count_sql)
        assert first_call_params["phase"] == "PHASE1"

    async def test_pagination_offset(self, mock_db):
        mock_db.execute = AsyncMock(
            side_effect=[
                FakeResult([], scalar_value=0),
                FakeResult([]),
            ]
        )
        service = AssetService(mock_db)
        await service.list_assets(page=3, page_size=10)

        first_call_params = mock_db.execute.call_args_list[0][0][1]
        assert first_call_params["offset"] == 20  # (page-1)*page_size = 2*10
        assert first_call_params["limit"] == 10


@pytest.mark.unit
class TestAssetServiceGetDetail:
    async def test_raises_not_found_when_missing(self, mock_db):
        mock_db.execute = AsyncMock(return_value=FakeResult([]))
        service = AssetService(mock_db)

        with pytest.raises(NotFoundError):
            await service.get_asset_detail(uuid4())

    async def test_returns_detail_dict(self, mock_db):
        now = datetime(2026, 1, 15)
        asset_id = str(uuid4())
        row = FakeRow(
            asset_id,
            "Tirzepatide",
            ["Mounjaro"],
            "tirzepatide",
            "Biologic",
            "GIP/GLP-1 dual agonist",
            "Phase 4",
            {"nct": "NCT123"},
            ["T2D"],
            ["GLP1R", "GIPR"],
            ["Eli Lilly"],
            {"us": "approved"},
            0.92,
            0.88,
            None,
            now,
            now,
        )
        mock_db.execute = AsyncMock(return_value=FakeResult([row]))
        service = AssetService(mock_db)
        result = await service.get_asset_detail(uuid4())

        assert result["primary_name"] == "Tirzepatide"
        assert result["mechanism_of_action"] == "GIP/GLP-1 dual agonist"
        assert result["source_confidence"] == 0.92
