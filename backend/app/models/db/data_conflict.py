from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import TimestampedBase


class DataConflict(TimestampedBase):
    __tablename__ = "data_conflicts"

    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    field_path: Mapped[str] = mapped_column(String(300), nullable=False)
    current_assertion_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("field_assertions.id", ondelete="SET NULL")
    )
    candidate_assertion_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("field_assertions.id", ondelete="SET NULL")
    )
    conflict_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="open")
    resolution_reason: Mapped[str | None] = mapped_column(Text)
