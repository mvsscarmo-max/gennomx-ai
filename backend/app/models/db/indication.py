from uuid import UUID

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import TimestampedBase


class Indication(TimestampedBase):
    """Disease, clinical condition, or therapeutic area."""

    __tablename__ = "indications"

    preferred_name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    aliases: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    therapeutic_area: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)

    # Ontology mappings
    ontology_ids: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # e.g. {"mesh": "D001249", "icd10": "J45", "snomed": "195967001", "mondo": "MONDO:0004979"}

    # Hierarchy
    parent_indication_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("indications.id", ondelete="SET NULL"), nullable=True
    )

    ingestion_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_indications_preferred_name_trgm", "preferred_name", postgresql_using="gin"),
        Index("ix_indications_aliases", "aliases", postgresql_using="gin"),
        Index("ix_indications_ontology_ids", "ontology_ids", postgresql_using="gin"),
    )
