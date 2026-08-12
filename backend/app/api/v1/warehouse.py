from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_admin
from app.database import get_db
from app.services.warehouse_coverage_service import WarehouseCoverageService

router = APIRouter()


@router.get("/coverage", summary="Get warehouse coverage and traceability metrics")
async def warehouse_coverage(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[CurrentUser, Depends(require_admin)],
) -> dict:
    return {"success": True, "data": await WarehouseCoverageService(db).get_coverage()}
