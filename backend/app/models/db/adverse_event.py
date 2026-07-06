from uuid import UUID

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import TemporalProjectionMixin, TimestampedBase


class AdverseEvent(TemporalProjectionMixin, TimestampedBase):
    """Adverse event or safety finding."""

    __tablename__ = "adverse_events"

    drug_asset_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("drug_assets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    trial_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("clinical_trials.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # trial | faers | label | publication

    event_name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    meddra_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    grade: Mapped[str | None] = mapped_column(String(50), nullable=True)
    seriousness: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # serious | non_serious
    incidence_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    comparator_incidence_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    n_events: Mapped[int | None] = mapped_column(Integer, nullable=True)
    n_subjects_at_risk: Mapped[int | None] = mapped_column(Integer, nullable=True)
    population: Mapped[str | None] = mapped_column(Text, nullable=True)

    source_evidence_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("evidence_snippets.id", ondelete="SET NULL"), nullable=True
    )
    ingestion_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_ae_drug_asset_id", "drug_asset_id"),
        Index("ix_ae_event_name", "event_name"),
    )
