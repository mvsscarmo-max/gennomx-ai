from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_security
from app.core.responses import paginated
from app.database import get_db
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/mcp", summary="List sanitized MCP audit records")
async def list_mcp_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[CurrentUser, Depends(require_security)],
    status: str | None = Query(None, max_length=50),
    tool_name: str | None = Query(None, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    items, total = await AuditService(db).list_mcp_logs(
        status=status, tool_name=tool_name, page=page, page_size=page_size
    )
    return paginated(items, total, page, page_size)


@router.get("/security", summary="List sanitized security events")
async def list_security_events(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[CurrentUser, Depends(require_security)],
    severity: str | None = Query(None, max_length=20),
    status: str | None = Query(None, max_length=50),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    items, total = await AuditService(db).list_security_events(
        severity=severity, status=status, page=page, page_size=page_size
    )
    return paginated(items, total, page, page_size)
