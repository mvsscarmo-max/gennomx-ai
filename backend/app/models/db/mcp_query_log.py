from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import TimestampedBase


class MCPQueryLog(TimestampedBase):
    """Audit log for every MCP tool call."""

    __tablename__ = "mcp_query_logs"

    timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    requesting_client: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # chatgpt | claude | private_agent
    user_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    organization_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    input_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    normalized_arguments: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    result_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # success | error | rate_limited | blocked
    error_type: Mapped[str | None] = mapped_column(String(200), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    source_entities_accessed: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    entity_types_accessed: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)

    safety_flags: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    ai_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)

    __table_args__ = (
        Index("ix_mcp_log_tool_client", "tool_name", "requesting_client"),
        Index("ix_mcp_log_timestamp", "timestamp"),
        Index("ix_mcp_log_status", "status"),
    )
