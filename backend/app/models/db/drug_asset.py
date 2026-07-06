from uuid import UUID

from sqlalchemy import Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import TimestampedBase


class DrugAsset(TimestampedBase):
    """Canonical therapeutic asset / drug."""

    __tablename__ = "drug_assets"

    # Identity
    primary_name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    aliases: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    inn: Mapped[str | None] = mapped_column(String(300), nullable=True)

    # Classification
    modality: Mapped[str | None] = mapped_column(String(100), nullable=True)
    mechanism_of_action: Mapped[str | None] = mapped_column(String(500), nullable=True)
    development_stage: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # External identifiers (JSONB for flexibility)
    external_ids: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # e.g. {"drugbank": "DB12345", "chembl": "CHEMBL123", "pubchem_cid": "456"}

    # Denormalized summary fields (updated via pipeline)
    indication_names: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    target_symbols: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    sponsor_names: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    regulatory_status_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Data quality
    source_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_completeness_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Traceability
    primary_source_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("source_documents.id", ondelete="SET NULL"), nullable=True
    )
    ingestion_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Full-text search vector (managed by trigger/pipeline)
    search_vector: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # tsvector stored as text for compatibility

    __table_args__ = (
        Index("ix_drug_assets_primary_name_trgm", "primary_name", postgresql_using="gin"),
        Index("ix_drug_assets_aliases", "aliases", postgresql_using="gin"),
        Index("ix_drug_assets_external_ids", "external_ids", postgresql_using="gin"),
    )
