from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import (
    AI_INGEST_DRY_RUN,
    AI_INGEST_RUN,
    CurrentUser,
    authorize_action,
    get_current_user,
    require_admin,
    require_ingest_run,
    require_read,
)
from app.config import get_settings
from app.core.responses import paginated
from app.database import get_db
from app.services.source_service import SourceService
from workers.storage.raw_payload import preflight_raw_storage
from workers.tasks.source_control import RUNNABLE_SOURCE_SLUGS, schedule_ingestion

router = APIRouter()
settings = get_settings()


class SourceActivationRequest(BaseModel):
    is_enabled: bool


class SourceRunRequest(BaseModel):
    job_type: Literal["incremental", "full_sync"] = "incremental"
    max_records: int = Field(ge=1)
    dry_run: bool = False
    query: str | None = Field(default=None, max_length=500)
    conditions: list[str] | None = Field(default=None, max_length=20)
    interventions: list[str] | None = Field(default=None, max_length=20)


@router.get("", summary="List data sources and connector status")
async def list_sources(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[CurrentUser, Depends(require_read)],
    status: str | None = Query(None, description="active | inactive | error"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> dict:
    service = SourceService(db)
    items, total = await service.list_sources(status=status, page=page, page_size=page_size)
    return paginated(items, total, page, page_size)


@router.patch("/{source_slug}/activation", summary="Enable or disable an ingestion data source")
async def set_source_activation(
    source_slug: str,
    payload: SourceActivationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(require_admin)],
) -> dict:
    if payload.is_enabled and source_slug not in RUNNABLE_SOURCE_SLUGS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Source '{source_slug}' is not approved for ingestion activation",
        )
    source = await SourceService(db).set_source_enabled(
        source_slug, payload.is_enabled, user.user_id
    )
    return {"success": True, "data": source}


@router.post("/{source_slug}/run", summary="Schedule a bounded admin ingestion or dry-run")
async def run_source(
    source_slug: str,
    payload: SourceRunRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> dict:
    authorize_action(
        user,
        AI_INGEST_DRY_RUN if payload.dry_run else AI_INGEST_RUN,
        local_admin=True,
    )
    if source_slug not in RUNNABLE_SOURCE_SLUGS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unknown ingestion source"
        )
    if payload.max_records > settings.INGEST_ADMIN_MAX_RECORDS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"max_records must not exceed {settings.INGEST_ADMIN_MAX_RECORDS}",
        )
    if source_slug not in {"clinicaltrials_gov", "pubmed"} and (
        payload.query or payload.conditions or payload.interventions
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Filters are supported only by ClinicalTrials.gov and PubMed",
        )
    if source_slug == "pubmed" and (payload.conditions or payload.interventions):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="conditions and interventions are supported only by ClinicalTrials.gov",
        )

    service = SourceService(db)
    source = await service.get_source_by_slug(source_slug)
    if not payload.dry_run and not source["is_enabled"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Source is disabled; complete a dry-run and activate it before a real run",
        )

    task_kwargs: dict = {
        "job_type": payload.job_type,
        "max_records": payload.max_records,
        "dry_run": payload.dry_run,
    }
    if source_slug in {"clinicaltrials_gov", "pubmed"}:
        task_kwargs["query"] = payload.query
    if source_slug == "clinicaltrials_gov":
        task_kwargs["conditions"] = payload.conditions
        task_kwargs["interventions"] = payload.interventions
    task = schedule_ingestion(source_slug, **task_kwargs)
    await service.record_ingestion_trigger(
        source_slug,
        user.user_id,
        dry_run=payload.dry_run,
        max_records=payload.max_records,
        job_type=payload.job_type,
    )
    return {
        "success": True,
        "data": {
            "celery_task_id": task.id,
            "source_slug": source_slug,
            "dry_run": payload.dry_run,
            "max_records": payload.max_records,
        },
    }


@router.post("/storage-preflight", summary="Verify raw storage before a real smoke-run")
async def storage_preflight(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(require_ingest_run)],
) -> dict:
    try:
        result = await preflight_raw_storage()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Raw storage preflight failed",
        ) from exc
    await SourceService(db).record_storage_preflight(user.user_id, result)
    return {"success": True, "data": result}
