from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, get_current_user
from app.core.responses import paginated
from app.database import get_db
from app.services.trial_service import TrialService

router = APIRouter()


@router.get("", summary="List clinical trials")
async def list_trials(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[CurrentUser, Depends(get_current_user)],
    q: str | None = Query(None),
    nct_id: str | None = Query(None),
    phase: str | None = Query(None),
    status: str | None = Query(None),
    sponsor: str | None = Query(None),
    indication: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    service = TrialService(db)
    items, total = await service.list_trials(
        q=q,
        nct_id=nct_id,
        phase=phase,
        status=status,
        sponsor=sponsor,
        indication=indication,
        page=page,
        page_size=page_size,
    )
    return paginated(items, total, page, page_size)


@router.get("/{trial_id}", summary="Get clinical trial detail")
async def get_trial(
    trial_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[CurrentUser, Depends(get_current_user)],
) -> dict:
    service = TrialService(db)
    return await service.get_trial_detail(trial_id)
