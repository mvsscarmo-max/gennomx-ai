from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, get_current_user
from app.core.responses import paginated
from app.database import get_db
from app.models.schemas.drug_asset import DrugAssetDetail
from app.services.asset_service import AssetService

router = APIRouter()


@router.get("", summary="List drug assets")
async def list_assets(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[CurrentUser, Depends(get_current_user)],
    q: str | None = Query(None, description="Full-text search query"),
    indication: str | None = Query(None),
    target: str | None = Query(None),
    company: str | None = Query(None),
    phase: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    service = AssetService(db)
    items, total = await service.list_assets(
        q=q,
        indication=indication,
        target=target,
        company=company,
        phase=phase,
        page=page,
        page_size=page_size,
    )
    return paginated(items, total, page, page_size)


@router.get("/{asset_id}", summary="Get drug asset detail", response_model=DrugAssetDetail)
async def get_asset(
    asset_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[CurrentUser, Depends(get_current_user)],
) -> DrugAssetDetail:
    service = AssetService(db)
    return DrugAssetDetail.model_validate(await service.get_asset_detail(asset_id))
