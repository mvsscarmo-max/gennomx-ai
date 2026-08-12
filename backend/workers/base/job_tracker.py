"""Registers and updates IngestionJob records in the database."""

import json
import uuid

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from workers.base.connector import ConnectorResult

logger = structlog.get_logger(__name__)


class JobTracker:
    """Creates and updates IngestionJob records for auditability."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_job(
        self,
        data_source_slug: str,
        job_type: str = "incremental",
        celery_task_id: str | None = None,
        metadata: dict | None = None,
    ) -> str:
        """Insert a pending IngestionJob and return its ID."""
        job_id = str(uuid.uuid4())
        source_row = (
            await self.db.execute(
                text("SELECT id::text FROM data_sources WHERE slug = :slug"),
                {"slug": data_source_slug},
            )
        ).fetchone()
        data_source_id = str(source_row[0]) if source_row else None

        await self.db.execute(
            text("""
                INSERT INTO ingestion_jobs
                   (id, data_source_id, data_source_slug, job_type, celery_task_id,
                    status, metadata, created_at, updated_at)
                VALUES
                   (:id, :data_source_id, :slug, :job_type, :celery_id,
                    'pending', CAST(:metadata AS jsonb), now(), now())
            """),
            {
                "id": job_id,
                "data_source_id": data_source_id,
                "slug": data_source_slug,
                "job_type": job_type,
                "celery_id": celery_task_id,
                "metadata": json.dumps(metadata) if metadata else None,
            },
        )
        await self.db.commit()
        logger.info("job_created", job_id=job_id, source=data_source_slug, type=job_type)
        return job_id

    async def start_job(self, job_id: str) -> None:
        await self.db.execute(
            text(
                "UPDATE ingestion_jobs SET status = 'running', started_at = now(), "
                "updated_at = now() WHERE id = :id"
            ),
            {"id": job_id},
        )
        await self.db.commit()

    async def complete_job(
        self,
        job_id: str,
        result: ConnectorResult,
        *,
        status: str | None = None,
        update_source: bool = True,
    ) -> None:
        d = result.to_job_dict()
        status = status or ("success" if result.success else "partial")
        await self.db.execute(
            text("""
                UPDATE ingestion_jobs SET
                  status = :status,
                  finished_at = now(),
                  updated_at = now(),
                  duration_seconds = :duration,
                  records_fetched = :fetched,
                  records_inserted = :inserted,
                  records_updated = :updated,
                  records_rejected = :rejected,
                  records_skipped = :skipped,
                  error_type = :error_type,
                  error_summary = :error_summary,
                  error_detail = CAST(:error_detail AS jsonb),
                  metadata = CAST(:metadata AS jsonb)
                WHERE id = :id
            """),
            {
                "id": job_id,
                "status": status,
                "duration": d["duration_seconds"],
                "fetched": d["records_fetched"],
                "inserted": d["records_inserted"],
                "updated": d["records_updated"],
                "rejected": d["records_rejected"],
                "skipped": d["records_skipped"],
                "error_type": d["error_type"],
                "error_summary": d["error_summary"],
                "error_detail": json.dumps(d["error_detail"]) if d["error_detail"] else None,
                "metadata": json.dumps(d["metadata"]) if d["metadata"] else None,
            },
        )
        if update_source:
            if status == "success":
                await self.db.execute(
                    text("""
                        UPDATE data_sources
                        SET last_successful_run = now(), connector_status = 'active',
                            updated_at = now()
                        WHERE slug = :slug
                    """),
                    {"slug": result.source_slug},
                )
            elif status == "failed":
                await self.db.execute(
                    text("""
                        UPDATE data_sources
                        SET last_failed_run = now(), connector_status = 'error',
                            updated_at = now()
                        WHERE slug = :slug
                    """),
                    {"slug": result.source_slug},
                )
            else:
                # A bounded or partially parsed run is operationally useful but must not
                # advance the incremental cursor or be presented as a source failure.
                await self.db.execute(
                    text("""
                        UPDATE data_sources
                        SET connector_status = 'active', updated_at = now()
                        WHERE slug = :slug
                    """),
                    {"slug": result.source_slug},
                )
        await self.db.commit()
        logger.info(
            "job_completed",
            job_id=job_id,
            status=status,
            inserted=d["records_inserted"],
            duration=d["duration_seconds"],
        )
