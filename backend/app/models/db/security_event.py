from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import TimestampedBase


class SecurityEvent(TimestampedBase):
    """Audit trail for security-relevant events."""

    __tablename__ = "security_events"

    timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    event_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # auth_failure | rate_limit | mcp_blocked | upload_rejected | sql_injection_attempt
    severity: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # low | medium | high | critical

    actor_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # user | api_key | mcp_token | anonymous
    actor_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    source_ip_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )  # hashed for privacy

    endpoint_or_tool: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_taken: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )  # blocked | logged | alerted | ignored
    status: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # resolved | open | investigating

    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    __table_args__ = (
        Index("ix_security_event_type_severity", "event_type", "severity"),
        Index("ix_security_event_timestamp", "timestamp"),
    )
