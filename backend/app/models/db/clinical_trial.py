from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import TimestampedBase


class ClinicalTrial(TimestampedBase):
    """Clinical trial record, primarily from ClinicalTrials.gov."""

    __tablename__ = "clinical_trials"

    # Identifiers
    nct_id: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True, index=True)
    eudract_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    other_ids: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Core metadata
    title: Mapped[str] = mapped_column(Text, nullable=False)
    brief_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    official_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    phase: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    phase_normalized: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # PHASE1 | PHASE2 | PHASE3 | PHASE4 | NA

    # Status
    status: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    status_normalized: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # RECRUITING | COMPLETED | TERMINATED | etc.

    # Sponsor
    sponsor_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sponsor_company_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )

    # Collaborators (JSONB array)
    collaborators: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Disease / Condition
    conditions: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    indication_ids: Mapped[list[str] | None] = mapped_column(
        ARRAY(Text), nullable=True
    )  # FK to indications as strings

    # Interventions
    interventions: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    drug_asset_ids: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)

    # Arms
    arms: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Enrollment
    enrollment: Mapped[int | None] = mapped_column(Integer, nullable=True)
    enrollment_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # ACTUAL | ESTIMATED

    # Dates
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    primary_completion_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completion_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_update_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    lifecycle_status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Geography
    countries: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    locations: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Eligibility (stored raw for search)
    eligibility_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    minimum_age: Mapped[str | None] = mapped_column(String(50), nullable=True)
    maximum_age: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sex: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Registry source
    registry_source: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # clinicaltrials_gov | eudract | rebec

    # Traceability
    source_document_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("source_documents.id", ondelete="SET NULL"), nullable=True
    )
    raw_payload_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ingestion_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_ct_nct_id", "nct_id"),
        Index("ix_ct_phase_status", "phase_normalized", "status_normalized"),
        Index("ix_ct_conditions", "conditions", postgresql_using="gin"),
        Index("ix_ct_drug_asset_ids", "drug_asset_ids", postgresql_using="gin"),
    )
