from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_read
from app.core.responses import paginated
from app.database import get_db
from app.services.catalog_service import CatalogService

router = APIRouter()


@router.get("", summary="List biological targets")
async def list_targets(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[CurrentUser, Depends(require_read)],
    q: str | None = Query(None, max_length=200),
    target_type: str | None = Query(None, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    items, total = await CatalogService(db).list_targets(
        q=q, target_type=target_type, page=page, page_size=page_size
    )
    return paginated(items, total, page, page_size)
