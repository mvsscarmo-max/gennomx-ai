"""Create llm_call_logs audit table.

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-23
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "llm_call_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("environment", sa.String(50), nullable=False, server_default="development"),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("task_name", sa.String(200), nullable=False),
        sa.Column("job_id", sa.String(36), nullable=True),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("entity_type", sa.String(100), nullable=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("prompt_hash", sa.String(64), nullable=False),
        sa.Column("input_payload_hash", sa.String(64), nullable=True),
        sa.Column("raw_response_hash", sa.String(64), nullable=True),
        sa.Column("schema_name", sa.String(200), nullable=True),
        sa.Column("schema_valid", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("latency_ms", sa.Float, nullable=False),
        sa.Column("input_tokens", sa.Integer, nullable=True),
        sa.Column("output_tokens", sa.Integer, nullable=True),
        sa.Column("total_tokens", sa.Integer, nullable=True),
        sa.Column("estimated_cost_usd", sa.Float, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="success"),
        sa.Column("error_type", sa.String(200), nullable=True),
        sa.Column("error_detail_sanitized", sa.Text, nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_llm_log_provider_model", "llm_call_logs", ["provider", "model"])
    op.create_index("ix_llm_log_task_status", "llm_call_logs", ["task_name", "status"])
    op.create_index("ix_llm_log_created", "llm_call_logs", ["created_at"])
    op.create_index("ix_llm_call_logs_provider", "llm_call_logs", ["provider"])
    op.create_index("ix_llm_call_logs_model", "llm_call_logs", ["model"])
    op.create_index("ix_llm_call_logs_task_name", "llm_call_logs", ["task_name"])
    op.create_index("ix_llm_call_logs_prompt_hash", "llm_call_logs", ["prompt_hash"])
    op.create_index("ix_llm_call_logs_status", "llm_call_logs", ["status"])
    op.create_index("ix_llm_call_logs_timestamp", "llm_call_logs", ["timestamp"])


def downgrade() -> None:
    op.drop_table("llm_call_logs")
