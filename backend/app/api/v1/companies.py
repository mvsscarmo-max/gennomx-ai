from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, get_current_user
from app.core.responses import paginated
from app.database import get_db
from app.services.company_service import CompanyService

router = APIRouter()


@router.get("", summary="List companies")
async def list_companies(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[CurrentUser, Depends(get_current_user)],
    q: str | None = Query(None),
    company_type: str | None = Query(None),
    country: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    service = CompanyService(db)
    items, total = await service.list_companies(
        q=q, company_type=company_type, country=country, page=page, page_size=page_size
    )
    return paginated(items, total, page, page_size)


@router.get("/{company_id}", summary="Get company detail and pipeline")
async def get_company(
    company_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[CurrentUser, Depends(get_current_user)],
) -> dict:
    service = CompanyService(db)
    return await service.get_company_detail(company_id)
