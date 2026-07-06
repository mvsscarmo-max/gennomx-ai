from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, get_current_user, require_admin
from app.core.responses import paginated
from app.database import get_db
from app.services.source_service import SourceService

router = APIRouter()


@router.get("", summary="List ingestion jobs")
async def list_jobs(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[CurrentUser, Depends(get_current_user)],
    source_id: UUID | None = Query(None),
    source_slug: str | None = Query(None),
    status: str | None = Query(None, description="running | success | failed | partial"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    service = SourceService(db)
    items, total = await service.list_jobs(
        source_id=source_id,
        source_slug=source_slug,
        status=status,
        page=page,
        page_size=page_size,
    )
    return paginated(items, total, page, page_size)


@router.get("/worker-status", summary="Get Celery worker status")
async def worker_status(
    _user: Annotated[CurrentUser, Depends(get_current_user)],
) -> dict:
    try:
        from workers.celery_app import celery_app

        inspect = celery_app.control.inspect(timeout=3.0)
        stats = inspect.stats()
        active = inspect.active()
        if stats is None or active is None:
            # inspect() returning None means no workers responded in time —
            # distinct from "responded with zero workers".
            return {
                "success": False,
                "data": {"state": "unknown", "workers": [], "worker_count": 0, "active_tasks": 0},
            }
        return {
            "success": True,
            "data": {
                "state": "ok",
                "workers": list(stats.keys()),
                "worker_count": len(stats),
                "active_tasks": sum(len(v) for v in active.values()),
            },
        }
    except Exception:
        return {
            "success": False,
            "data": {"state": "unknown", "workers": [], "worker_count": 0, "active_tasks": 0},
        }


def _retry_task_for_source(source_slug: str, job_type: str):
    if source_slug == "clinicaltrials_gov":
        from workers.tasks.ingest import run_clinicaltrials_ingest

        return run_clinicaltrials_ingest.delay(job_type=job_type)
    if source_slug in ("pubmed", "pubmed_pmc"):
        from workers.tasks.ingest import run_pubmed_ingest

        return run_pubmed_ingest.delay(job_type=job_type)
    if source_slug == "openfda":
        from workers.tasks.ingest import run_openfda_ingest

        return run_openfda_ingest.delay(job_type=job_type)
    if source_slug == "dailymed":
        from workers.tasks.ingest import run_dailymed_ingest

        return run_dailymed_ingest.delay(job_type=job_type)
    if source_slug == "open_targets":
        from workers.tasks.ingest import run_opentargets_ingest

        return run_opentargets_ingest.delay(job_type=job_type)
    if source_slug == "ema":
        from workers.tasks.ingest import run_ema_ingest

        return run_ema_ingest.delay(job_type=job_type)
    return None


@router.post("/{job_id}/retry", summary="Retry a failed job")
async def retry_job(
    job_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[CurrentUser, Depends(require_admin)],
) -> dict:
    service = SourceService(db)
    job = await service.get_job_detail(job_id)
    source_slug = job["source_slug"]

    try:
        task = _retry_task_for_source(source_slug, job["job_type"] or "incremental")
    except Exception as e:
        return {
            "success": False,
            "message": f"Could not schedule retry for job {job_id}: {e}",
        }

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"Retry is not implemented for source '{source_slug}'",
        )

    return {
        "success": True,
        "message": f"Retry scheduled for job {job_id}",
        "data": {"celery_task_id": task.id, "source_slug": source_slug},
    }
