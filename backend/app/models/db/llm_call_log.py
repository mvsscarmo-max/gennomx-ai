from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.db.base import TimestampedBase


class LLMCallLog(TimestampedBase):
    """Audit log for every internal LLM call (classification, extraction, etc.).

    Does NOT store full prompts — only hashes and operational metadata.
    """

    __tablename__ = "llm_call_logs"

    environment: Mapped[str] = mapped_column(String(50), nullable=False, default="development")
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    task_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    job_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_document_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)

    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    input_payload_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    raw_response_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    schema_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    schema_valid: Mapped[bool] = mapped_column(nullable=False, default=True)

    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="success", index=True)
    error_type: Mapped[str | None] = mapped_column(String(200), nullable=True)
    error_detail_sanitized: Mapped[str | None] = mapped_column(Text, nullable=True)

    timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    __table_args__ = (
        Index("ix_llm_log_provider_model", "provider", "model"),
        Index("ix_llm_log_task_status", "task_name", "status"),
        Index("ix_llm_log_created", "created_at"),
    )
