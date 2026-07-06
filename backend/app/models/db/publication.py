from datetime import date

from sqlalchemy import Date, Index, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import TemporalProjectionMixin, TimestampedBase


class Publication(TemporalProjectionMixin, TimestampedBase):
    """Scientific publication (article, preprint, review)."""

    __tablename__ = "publications"

    title: Mapped[str] = mapped_column(Text, nullable=False)
    journal: Mapped[str | None] = mapped_column(String(500), nullable=True)
    publication_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    publication_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # article | preprint | review | abstract | letter

    doi: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True, unique=True)
    pmid: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True, unique=True)
    pmcid: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    authors: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    keywords: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)

    # Linked entities
    linked_trial_ids: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    linked_asset_ids: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    linked_indication_ids: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)

    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    open_access: Mapped[bool | None] = mapped_column(nullable=True)

    ingestion_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_publications_linked_trials", "linked_trial_ids", postgresql_using="gin"),
        Index("ix_publications_linked_assets", "linked_asset_ids", postgresql_using="gin"),
    )
