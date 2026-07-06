from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import TimestampedBase


class SourceDocument(TimestampedBase):
    """Preserved reference to an original source document or resource."""

    __tablename__ = "source_documents"

    data_source_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("data_sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # api_response | pdf | html | csv | xml | json | manual_upload

    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    # Content hash for deduplication and integrity
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    external_record_id: Mapped[str | None] = mapped_column(String(300), nullable=True)
    source_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Storage paths by layer
    raw_storage_path: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    processed_storage_path: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    license_status: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # open | licensed | restricted | unknown
    language: Mapped[str | None] = mapped_column(String(20), nullable=True, default="en")

    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    __table_args__ = (
        Index("ix_source_doc_content_hash", "content_hash"),
        Index("ix_source_doc_data_source_id", "data_source_id"),
    )
