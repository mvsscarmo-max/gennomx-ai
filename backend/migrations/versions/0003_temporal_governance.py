"""Add bitemporal assertions and deterministic persistence governance.

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-20
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


SCORE_CHECK = "{0} IS NULL OR ({0} >= 0 AND {0} <= 1)"


def upgrade() -> None:
    op.add_column("source_documents", sa.Column("external_record_id", sa.String(300)))
    op.add_column("source_documents", sa.Column("source_updated_at", sa.DateTime(timezone=True)))
    op.create_index(
        "uq_source_document_version",
        "source_documents",
        ["data_source_id", "external_record_id", "content_hash"],
        unique=True,
        postgresql_where=sa.text("external_record_id IS NOT NULL AND content_hash IS NOT NULL"),
    )
    op.add_column("clinical_trials", sa.Column("source_updated_at", sa.DateTime(timezone=True)))
    op.add_column(
        "clinical_trials",
        sa.Column("lifecycle_status", sa.String(50), nullable=False, server_default="active"),
    )
    op.add_column(
        "clinical_trials",
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.create_index(
        "ix_trials_current_status",
        "clinical_trials",
        ["status_normalized", "source_updated_at"],
        postgresql_where=sa.text("is_current = true"),
    )

    op.add_column("drug_assets", sa.Column("current_development_stage", sa.String(100)))
    op.add_column("drug_assets", sa.Column("max_historical_stage", sa.String(100)))
    op.add_column(
        "drug_assets",
        sa.Column("development_status", sa.String(50), nullable=False, server_default="unknown"),
    )
    op.execute(
        "UPDATE drug_assets SET current_development_stage = development_stage, "
        "max_historical_stage = development_stage"
    )

    for column in (
        sa.Column("valid_from", sa.DateTime(timezone=True)),
        sa.Column("valid_to", sa.DateTime(timezone=True)),
        sa.Column(
            "system_from",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("system_to", sa.DateTime(timezone=True)),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("lifecycle_status", sa.String(50), nullable=False, server_default="active"),
    ):
        op.add_column("clinical_trial_assets", column)
    op.create_index(
        "ix_trial_assets_current",
        "clinical_trial_assets",
        ["trial_id", "is_current"],
        postgresql_where=sa.text("is_current = true"),
    )
    op.create_table(
        "clinical_trial_asset_history",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "trial_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinical_trials.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("drug_assets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("source_documents.id", ondelete="SET NULL"),
        ),
        sa.Column("valid_from", sa.DateTime(timezone=True)),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=False),
        sa.Column("system_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("system_to", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lifecycle_status", sa.String(50), nullable=False, server_default="superseded"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_trial_asset_history_trial", "clinical_trial_asset_history", ["trial_id", "valid_to"]
    )

    op.create_table(
        "field_assertions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_path", sa.String(300), nullable=False),
        sa.Column("granularity_key", sa.String(500), nullable=False, server_default="default"),
        sa.Column("value_json", postgresql.JSONB()),
        sa.Column("value_hash", sa.String(64), nullable=False),
        sa.Column(
            "source_document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("source_documents.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "evidence_snippet_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("evidence_snippets.id", ondelete="SET NULL"),
        ),
        sa.Column("source_record_id", sa.String(300)),
        sa.Column("source_version", sa.String(200)),
        sa.Column("source_updated_at", sa.DateTime(timezone=True)),
        sa.Column(
            "observed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("valid_from", sa.DateTime(timezone=True)),
        sa.Column("valid_to", sa.DateTime(timezone=True)),
        sa.Column(
            "system_from",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("system_to", sa.DateTime(timezone=True)),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("lifecycle_status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("update_type", sa.String(50), nullable=False),
        sa.Column(
            "supersedes_assertion_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("field_assertions.id", ondelete="SET NULL"),
        ),
        sa.Column("replacement_reason", sa.Text()),
        sa.Column("extraction_method", sa.String(50), nullable=False),
        sa.Column("extractor_version", sa.String(100)),
        sa.Column("normalizer_version", sa.String(100)),
        sa.Column("rule_set_version", sa.String(100), nullable=False),
        sa.Column("authority_score", sa.Float()),
        sa.Column("confidence_score", sa.Float()),
        sa.Column("relevance_score", sa.Float()),
        sa.Column("freshness_score", sa.Float()),
        sa.Column("completeness_score", sa.Float()),
        sa.Column("conflict_status", sa.String(50), nullable=False, server_default="none"),
        sa.Column("review_status", sa.String(50), nullable=False, server_default="unreviewed"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(SCORE_CHECK.format("authority_score"), name="ck_assertion_authority"),
        sa.CheckConstraint(SCORE_CHECK.format("confidence_score"), name="ck_assertion_confidence"),
        sa.CheckConstraint(SCORE_CHECK.format("relevance_score"), name="ck_assertion_relevance"),
        sa.CheckConstraint(SCORE_CHECK.format("freshness_score"), name="ck_assertion_freshness"),
        sa.CheckConstraint(
            SCORE_CHECK.format("completeness_score"), name="ck_assertion_completeness"
        ),
    )
    op.create_index(
        "ix_assertion_current",
        "field_assertions",
        ["entity_type", "entity_id", "field_path", "is_current"],
    )
    op.create_index("ix_assertion_source_updated", "field_assertions", ["source_updated_at"])
    op.create_index(
        "uq_assertion_one_current",
        "field_assertions",
        ["entity_type", "entity_id", "field_path", "granularity_key"],
        unique=True,
        postgresql_where=sa.text("is_current = true"),
    )

    op.create_table(
        "data_conflicts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_path", sa.String(300), nullable=False),
        sa.Column(
            "current_assertion_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("field_assertions.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "candidate_assertion_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("field_assertions.id", ondelete="SET NULL"),
        ),
        sa.Column("conflict_type", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="open"),
        sa.Column("resolution_reason", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_conflict_open", "data_conflicts", ["status", "severity"])

    op.create_table(
        "manual_corrections",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_path", sa.String(300), nullable=False),
        sa.Column(
            "previous_assertion_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("field_assertions.id", ondelete="SET NULL"),
        ),
        sa.Column("proposed_value", postgresql.JSONB()),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "evidence_snippet_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("evidence_snippets.id", ondelete="SET NULL"),
        ),
        sa.Column("requested_by", sa.String(200), nullable=False),
        sa.Column("review_status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("reviewed_by", sa.String(200)),
        sa.Column(
            "resulting_assertion_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("field_assertions.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    for table in (
        "field_assertions",
        "data_conflicts",
        "manual_corrections",
        "clinical_trial_asset_history",
    ):
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
        op.execute(
            f"CREATE POLICY \"backend_read_{table}\" ON \"{table}\" FOR SELECT TO PUBLIC USING (current_user IN ('gennomx_app', 'gennomx_worker', 'gennomx_readonly'))"
        )
        op.execute(
            f"CREATE POLICY \"worker_write_{table}\" ON \"{table}\" FOR ALL TO PUBLIC USING (current_user = 'gennomx_worker') WITH CHECK (current_user = 'gennomx_worker')"
        )

    # Tighten installations that already ran the original 0002 policies. Privileged
    # migration/hosting roles must never be accepted by application data policies.
    legacy_tables = (
        "drug_assets",
        "companies",
        "indications",
        "targets",
        "clinical_trials",
        "endpoints",
        "trial_results",
        "adverse_events",
        "regulatory_approvals",
        "publications",
        "source_documents",
        "evidence_snippets",
        "data_sources",
        "ingestion_jobs",
        "mcp_query_logs",
        "security_events",
        "clinical_trial_assets",
    )
    for table in legacy_tables:
        op.execute(f'DROP POLICY IF EXISTS "backend_read_{table}" ON "{table}"')
        op.execute(f'DROP POLICY IF EXISTS "worker_write_{table}" ON "{table}"')
        op.execute(
            f"CREATE POLICY \"backend_read_{table}\" ON \"{table}\" FOR SELECT TO PUBLIC USING (current_user IN ('gennomx_app', 'gennomx_worker', 'gennomx_readonly'))"
        )
        op.execute(
            f"CREATE POLICY \"worker_write_{table}\" ON \"{table}\" FOR ALL TO PUBLIC USING (current_user = 'gennomx_worker') WITH CHECK (current_user = 'gennomx_worker')"
        )
    for table in ("mcp_query_logs", "security_events"):
        op.execute(f'DROP POLICY IF EXISTS "app_write_{table}" ON "{table}"')
        op.execute(
            f'CREATE POLICY "app_write_{table}" ON "{table}" FOR INSERT TO PUBLIC WITH CHECK (current_user = \'gennomx_app\')'
        )
    op.execute("""
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gennomx_readonly') THEN
            GRANT SELECT ON field_assertions, data_conflicts, manual_corrections,
              clinical_trial_asset_history TO gennomx_readonly;
          END IF;
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gennomx_app') THEN
            GRANT SELECT ON field_assertions, data_conflicts, manual_corrections,
              clinical_trial_asset_history TO gennomx_app;
          END IF;
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gennomx_worker') THEN
            GRANT SELECT, INSERT, UPDATE, DELETE ON field_assertions, data_conflicts,
              manual_corrections, clinical_trial_asset_history TO gennomx_worker;
          END IF;
        END
        $$;
    """)


def downgrade() -> None:
    for table in ("manual_corrections", "data_conflicts", "field_assertions"):
        op.drop_table(table)
    op.drop_table("clinical_trial_asset_history")
    op.drop_index("ix_trial_assets_current", table_name="clinical_trial_assets")
    for column in (
        "lifecycle_status",
        "is_current",
        "system_to",
        "system_from",
        "valid_to",
        "valid_from",
    ):
        op.drop_column("clinical_trial_assets", column)
    op.drop_column("drug_assets", "development_status")
    op.drop_column("drug_assets", "max_historical_stage")
    op.drop_column("drug_assets", "current_development_stage")
    op.drop_index("ix_trials_current_status", table_name="clinical_trials")
    op.drop_column("clinical_trials", "is_current")
    op.drop_column("clinical_trials", "lifecycle_status")
    op.drop_column("clinical_trials", "source_updated_at")
    op.drop_index("uq_source_document_version", table_name="source_documents")
    op.drop_column("source_documents", "source_updated_at")
    op.drop_column("source_documents", "external_record_id")
