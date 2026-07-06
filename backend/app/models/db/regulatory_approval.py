from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import TemporalProjectionMixin, TimestampedBase


class RegulatoryApproval(TemporalProjectionMixin, TimestampedBase):
    """Regulatory decision or approval status by region/agency."""

    __tablename__ = "regulatory_approvals"

    drug_asset_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("drug_assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    indication_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("indications.id", ondelete="SET NULL"), nullable=True
    )
    indication_name: Mapped[str | None] = mapped_column(String(500), nullable=True)

    region: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    agency: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # FDA | EMA | ANVISA | HC | TGA | PMDA
    approval_status: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )  # approved | rejected | pending | withdrawn | accelerated

    approval_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    submission_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    pathway: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # standard | accelerated | breakthrough | conditional
    special_designations: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # e.g. ["breakthrough_therapy", "orphan_drug", "fast_track"]

    label_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    regulatory_document_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("source_documents.id", ondelete="SET NULL"), nullable=True
    )
    source_evidence_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("evidence_snippets.id", ondelete="SET NULL"), nullable=True
    )
    application_number: Mapped[str | None] = mapped_column(String(200), nullable=True)

    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ingestion_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_reg_drug_asset_id", "drug_asset_id"),
        Index("ix_reg_agency_status", "agency", "approval_status"),
    )
