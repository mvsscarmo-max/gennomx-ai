from uuid import UUID

from sqlalchemy import Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import TemporalProjectionMixin, TimestampedBase


class TrialResult(TemporalProjectionMixin, TimestampedBase):
    """Quantitative result associated with a trial endpoint and arm."""

    __tablename__ = "trial_results"

    trial_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("clinical_trials.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    endpoint_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("endpoints.id", ondelete="SET NULL"), nullable=True
    )
    arm_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    arm_label: Mapped[str | None] = mapped_column(String(500), nullable=True)

    result_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    comparator_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    statistical_measure: Mapped[str | None] = mapped_column(String(200), nullable=True)
    p_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_interval_lower: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_interval_upper: Mapped[float | None] = mapped_column(Float, nullable=True)
    hazard_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    odds_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    timepoint: Mapped[str | None] = mapped_column(String(200), nullable=True)
    population: Mapped[str | None] = mapped_column(Text, nullable=True)
    n_analyzed: Mapped[int | None] = mapped_column(nullable=True)

    # Full raw result data (for complex structures)
    raw_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    source_evidence_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("evidence_snippets.id", ondelete="SET NULL"), nullable=True
    )
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    extraction_method: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # automatic | ai_extracted | human_reviewed

    ingestion_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_trial_results_trial_id", "trial_id"),
        Index("ix_trial_results_endpoint_id", "endpoint_id"),
    )
