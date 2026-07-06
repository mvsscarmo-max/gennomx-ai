from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import TimestampedBase


class IngestionJob(TimestampedBase):
    """Record of a single data ingestion execution."""

    __tablename__ = "ingestion_jobs"

    data_source_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("data_sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    data_source_slug: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    job_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # full_sync | incremental | reprocess | manual

    celery_task_id: Mapped[str | None] = mapped_column(String(200), nullable=True)

    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending", index=True
    )  # pending | running | success | failed | partial | cancelled

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Volume metrics
    records_fetched: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    records_inserted: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    records_updated: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    records_rejected: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    records_skipped: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)

    # Error tracking
    error_type: Mapped[str | None] = mapped_column(String(200), nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_detail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Quality & AI cost
    ai_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    test_status: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # passed | failed | skipped

    # Artifacts
    raw_log_path: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    raw_payload_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    __table_args__ = (
        Index("ix_ingestion_job_source_status", "data_source_slug", "status"),
        Index("ix_ingestion_job_created_at", "created_at"),
    )
