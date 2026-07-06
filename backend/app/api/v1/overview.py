from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, get_current_user
from app.database import get_db
from app.services.overview_service import OverviewService

router = APIRouter()


@router.get("", summary="Get aggregated dashboard overview stats")
async def get_overview(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[CurrentUser, Depends(get_current_user)],
) -> dict:
    data = await OverviewService(db).get_stats()
    return {"success": True, "data": data}
