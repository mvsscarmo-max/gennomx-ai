from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import TimestampedBase


class ManualCorrection(TimestampedBase):
    __tablename__ = "manual_corrections"

    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    field_path: Mapped[str] = mapped_column(String(300), nullable=False)
    granularity_key: Mapped[str | None] = mapped_column(String(500))
    previous_assertion_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("field_assertions.id", ondelete="SET NULL")
    )
    proposed_value: Mapped[dict | list | str | int | float | bool | None] = mapped_column(JSONB)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_snippet_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("evidence_snippets.id", ondelete="SET NULL")
    )
    requested_by: Mapped[str] = mapped_column(String(200), nullable=False)
    review_status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    reviewed_by: Mapped[str | None] = mapped_column(String(200))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision_reason: Mapped[str | None] = mapped_column(Text)
    resulting_assertion_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("field_assertions.id", ondelete="SET NULL")
    )
