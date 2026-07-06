from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, get_current_user
from app.core.responses import paginated
from app.database import get_db
from app.services.source_service import SourceService

router = APIRouter()


@router.get("", summary="List data sources and connector status")
async def list_sources(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[CurrentUser, Depends(get_current_user)],
    status: str | None = Query(None, description="active | inactive | error"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> dict:
    service = SourceService(db)
    items, total = await service.list_sources(status=status, page=page, page_size=page_size)
    return paginated(items, total, page, page_size)
