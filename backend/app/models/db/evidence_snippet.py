from uuid import UUID

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import TimestampedBase


class EvidenceSnippet(TimestampedBase):
    """Text excerpt extracted from a source document, linked to an entity."""

    __tablename__ = "evidence_snippets"

    source_document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("source_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Linked entity (polymorphic reference)
    entity_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # drug_asset | clinical_trial | trial_result | regulatory_approval
    entity_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    entity_field: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )  # which field this evidence supports

    text_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section: Mapped[str | None] = mapped_column(String(500), nullable=True)

    extraction_method: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # automatic | ai_extracted | human_reviewed | regex
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    __table_args__ = (
        Index("ix_evidence_entity", "entity_type", "entity_id"),
        Index("ix_evidence_source_doc", "source_document_id"),
    )
