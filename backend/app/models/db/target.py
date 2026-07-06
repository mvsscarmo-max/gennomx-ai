from sqlalchemy import Index, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import TimestampedBase


class Target(TimestampedBase):
    """Biological target (gene, protein, pathway)."""

    __tablename__ = "targets"

    symbol: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    aliases: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    organism: Mapped[str | None] = mapped_column(String(100), nullable=True, default="Homo sapiens")
    target_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # gene | protein | pathway | receptor

    external_ids: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # e.g. {"ensembl": "ENSG00000139618", "uniprot": "P38398", "ncbi_gene": "672"}

    # Evidence summary from Open Targets
    open_targets_score: Mapped[float | None] = mapped_column(nullable=True)
    associated_indication_ids: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)

    ingestion_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_targets_symbol_trgm", "symbol", postgresql_using="gin"),
        Index("ix_targets_external_ids", "external_ids", postgresql_using="gin"),
    )
