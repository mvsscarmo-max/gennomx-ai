"""Service layer for DataSource and IngestionJob queries."""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError


class SourceService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_sources(
        self,
        status: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[dict], int]:
        filters = []
        params: dict = {"offset": (page - 1) * page_size, "limit": page_size}

        if status:
            filters.append("connector_status = :status")
            params["status"] = status

        where = f"WHERE {' AND '.join(filters)}" if filters else ""

        count = (
            await self.db.execute(text(f"SELECT COUNT(*) FROM data_sources {where}"), params)
        ).scalar() or 0

        rows = (
            await self.db.execute(
                text(f"""
            SELECT id::text, name, slug, category, access_method, license_status,
                   connector_status, is_enabled, last_successful_run, last_failed_run,
                   updated_at
            FROM data_sources {where}
            ORDER BY name
            LIMIT :limit OFFSET :offset
        """),
                params,
            )
        ).fetchall()

        items = [
            {
                "id": r[0],
                "name": r[1],
                "slug": r[2],
                "category": r[3],
                "access_method": r[4],
                "license_status": r[5],
                "connector_status": r[6],
                "is_enabled": r[7],
                "last_successful_run": r[8].isoformat() if r[8] else None,
                "last_failed_run": r[9].isoformat() if r[9] else None,
                "updated_at": r[10].isoformat() if r[10] else None,
            }
            for r in rows
        ]
        return items, count

    async def get_source_detail(self, source_id: UUID) -> dict:
        row = (
            await self.db.execute(
                text("""
                SELECT id::text, name, slug, category, official_url, api_url,
                       access_method, license_status, compliance_notes,
                       connector_status, is_enabled, last_successful_run,
                       last_failed_run, connector_config, health_metrics, updated_at
                FROM data_sources
                WHERE id = :id::uuid
            """),
                {"id": str(source_id)},
            )
        ).fetchone()

        if not row:
            raise NotFoundError("DataSource", str(source_id))

        return {
            "id": row[0],
            "name": row[1],
            "slug": row[2],
            "category": row[3],
            "official_url": row[4],
            "api_url": row[5],
            "access_method": row[6],
            "license_status": row[7],
            "compliance_notes": row[8],
            "connector_status": row[9],
            "is_enabled": row[10],
            "last_successful_run": row[11].isoformat() if row[11] else None,
            "last_failed_run": row[12].isoformat() if row[12] else None,
            "connector_config": row[13],
            "health_metrics": row[14],
            "updated_at": row[15].isoformat() if row[15] else None,
        }

    async def list_jobs(
        self,
        source_id: UUID | None = None,
        source_slug: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[dict], int]:
        filters = []
        params: dict = {"offset": (page - 1) * page_size, "limit": page_size}

        if source_id:
            filters.append("data_source_id = :source_id")
            params["source_id"] = str(source_id)
        if source_slug:
            filters.append("data_source_slug = :slug")
            params["slug"] = source_slug
        if status:
            filters.append("status = :status")
            params["status"] = status

        where = f"WHERE {' AND '.join(filters)}" if filters else ""

        total = (
            await self.db.execute(text(f"SELECT COUNT(*) FROM ingestion_jobs {where}"), params)
        ).scalar() or 0

        rows = (
            await self.db.execute(
                text(f"""
                SELECT id::text, data_source_slug, job_type, status, celery_task_id,
                       started_at, finished_at, duration_seconds,
                       records_fetched, records_inserted, records_updated,
                       records_rejected, error_type, error_summary, updated_at
                FROM ingestion_jobs {where}
                ORDER BY started_at DESC NULLS LAST
                LIMIT :limit
                OFFSET :offset
            """),
                params,
            )
        ).fetchall()

        items = [
            {
                "id": r[0],
                "source_slug": r[1],
                "job_type": r[2],
                "status": r[3],
                "celery_task_id": r[4],
                "started_at": r[5].isoformat() if r[5] else None,
                "finished_at": r[6].isoformat() if r[6] else None,
                "duration_seconds": r[7],
                "records_fetched": r[8],
                "records_inserted": r[9],
                "records_updated": r[10],
                "records_rejected": r[11],
                "error_type": r[12],
                "error_summary": r[13],
                "updated_at": r[14].isoformat() if r[14] else None,
            }
            for r in rows
        ]
        return items, total

    async def get_job_detail(self, job_id: UUID) -> dict:
        row = (
            await self.db.execute(
                text("""
                SELECT id::text, data_source_id, data_source_slug, job_type, status,
                       celery_task_id, started_at, finished_at, duration_seconds,
                       records_fetched, records_inserted, records_updated,
                       records_rejected, records_skipped, error_type, error_summary,
                       error_detail, metadata, updated_at
                FROM ingestion_jobs
                WHERE id = :job_id::uuid
            """),
                {"job_id": str(job_id)},
            )
        ).fetchone()

        if not row:
            raise NotFoundError("IngestionJob", str(job_id))

        return {
            "id": row[0],
            "data_source_id": row[1],
            "source_slug": row[2],
            "job_type": row[3],
            "status": row[4],
            "celery_task_id": row[5],
            "started_at": row[6].isoformat() if row[6] else None,
            "finished_at": row[7].isoformat() if row[7] else None,
            "duration_seconds": row[8],
            "records_fetched": row[9],
            "records_inserted": row[10],
            "records_updated": row[11],
            "records_rejected": row[12],
            "records_skipped": row[13],
            "error_type": row[14],
            "error_summary": row[15],
            "error_detail": row[16],
            "metadata": row[17],
            "updated_at": row[18].isoformat() if row[18] else None,
        }
