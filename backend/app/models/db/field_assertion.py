from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import TimestampedBase


class FieldAssertion(TimestampedBase):
    __tablename__ = "field_assertions"

    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    field_path: Mapped[str] = mapped_column(String(300), nullable=False)
    granularity_key: Mapped[str] = mapped_column(String(500), nullable=False, default="default")
    value_json: Mapped[dict | list | str | int | float | bool | None] = mapped_column(JSONB)
    value_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_document_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("source_documents.id", ondelete="SET NULL")
    )
    evidence_snippet_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("evidence_snippets.id", ondelete="SET NULL")
    )
    source_record_id: Mapped[str | None] = mapped_column(String(300))
    source_version: Mapped[str | None] = mapped_column(String(200))
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    system_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    system_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    lifecycle_status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    update_type: Mapped[str] = mapped_column(String(50), nullable=False)
    supersedes_assertion_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("field_assertions.id", ondelete="SET NULL")
    )
    replacement_reason: Mapped[str | None] = mapped_column(Text)
    extraction_method: Mapped[str] = mapped_column(String(50), nullable=False)
    extractor_version: Mapped[str | None] = mapped_column(String(100))
    normalizer_version: Mapped[str | None] = mapped_column(String(100))
    rule_set_version: Mapped[str] = mapped_column(String(100), nullable=False)
    authority_score: Mapped[float | None] = mapped_column(Float)
    confidence_score: Mapped[float | None] = mapped_column(Float)
    relevance_score: Mapped[float | None] = mapped_column(Float)
    freshness_score: Mapped[float | None] = mapped_column(Float)
    completeness_score: Mapped[float | None] = mapped_column(Float)
    conflict_status: Mapped[str] = mapped_column(String(50), nullable=False, default="none")
    review_status: Mapped[str] = mapped_column(String(50), nullable=False, default="unreviewed")
    data_class: Mapped[str] = mapped_column(String(50), nullable=False, default="operational")
    source_type: Mapped[str | None] = mapped_column(String(50))
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    evidence_maturity: Mapped[str] = mapped_column(
        String(50), nullable=False, default="unclassified"
    )
    novelty_score: Mapped[float | None] = mapped_column(Float)
    clinical_impact_score: Mapped[float | None] = mapped_column(Float)
    validation_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="unvalidated"
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_assertion_current", "entity_type", "entity_id", "field_path", "is_current"),
        Index("ix_assertion_source_updated", "source_updated_at"),
    )
