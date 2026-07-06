from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import TimestampedBase


class DataSource(TimestampedBase):
    """Registered external data source and its connector configuration."""

    __tablename__ = "data_sources"

    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    category: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # clinical_trials | regulatory | scientific | competitive | genomics

    access_method: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # api | export | upload | scraping | mcp_external
    official_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    api_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    license_status: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # open | licensed | restricted | unknown
    update_frequency: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # daily | weekly | monthly | on_demand

    connector_status: Mapped[str | None] = mapped_column(
        String(50), nullable=True, default="inactive"
    )  # active | inactive | error | maintenance

    compliance_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    last_successful_run: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_failed_run: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    connector_config: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )  # rate limits, pagination, etc.
    health_metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (Index("ix_data_source_slug", "slug"),)
