from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_read
from app.core.responses import paginated
from app.database import get_db
from app.services.catalog_service import CatalogService

router = APIRouter()


@router.get("", summary="List indications / therapeutic areas")
async def list_indications(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[CurrentUser, Depends(require_read)],
    q: str | None = Query(None, max_length=200),
    therapeutic_area: str | None = Query(None, max_length=200),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    items, total = await CatalogService(db).list_indications(
        q=q, therapeutic_area=therapeutic_area, page=page, page_size=page_size
    )
    return paginated(items, total, page, page_size)


@router.get("/{indication_id}", summary="Get indication detail")
async def get_indication(
    indication_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[CurrentUser, Depends(require_read)],
) -> dict:
    return {"success": True, "data": await CatalogService(db).get_indication(indication_id)}
