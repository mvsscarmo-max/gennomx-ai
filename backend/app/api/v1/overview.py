from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_read
from app.database import get_db
from app.services.overview_service import OverviewService

router = APIRouter()


@router.get("", summary="Get aggregated dashboard overview stats")
async def get_overview(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[CurrentUser, Depends(require_read)],
) -> dict:
    data = await OverviewService(db).get_stats()
    return {"success": True, "data": data}
