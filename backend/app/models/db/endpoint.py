from uuid import UUID

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import TemporalProjectionMixin, TimestampedBase


class Endpoint(TemporalProjectionMixin, TimestampedBase):
    """Clinical trial endpoint definition."""

    __tablename__ = "endpoints"

    trial_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("clinical_trials.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    arm_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    endpoint_name: Mapped[str] = mapped_column(Text, nullable=False)
    endpoint_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # primary | secondary | exploratory | safety
    category: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )  # efficacy | safety | patient_reported | biomarker
    timepoint: Mapped[str | None] = mapped_column(String(200), nullable=True)
    measurement_unit: Mapped[str | None] = mapped_column(String(200), nullable=True)

    source_evidence_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("evidence_snippets.id", ondelete="SET NULL"), nullable=True
    )
    ingestion_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_endpoints_trial_id", "trial_id"),
        Index("ix_endpoints_type", "endpoint_type"),
    )
