from sqlalchemy import Index, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import TimestampedBase


class Company(TimestampedBase):
    """Pharmaceutical/biotech company, sponsor, or research institution."""

    __tablename__ = "companies"

    legal_name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    aliases: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    company_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # pharma | biotech | academic | cro | other
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    investor_relations_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pipeline_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # External identifiers
    external_ids: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # e.g. {"sec_cik": "0001234567", "lei": "...", "gleif": "..."}

    # Denormalized
    asset_count: Mapped[int | None] = mapped_column(nullable=True)
    active_trial_count: Mapped[int | None] = mapped_column(nullable=True)

    # Traceability
    ingestion_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_companies_legal_name_trgm", "legal_name", postgresql_using="gin"),
        Index("ix_companies_aliases", "aliases", postgresql_using="gin"),
    )
