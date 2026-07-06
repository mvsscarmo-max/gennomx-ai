"""Add relational integrity and deny-by-default RLS.

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-20
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


UUID_COLUMNS = (
    ("drug_assets", "primary_source_id", True),
    ("indications", "parent_indication_id", True),
    ("clinical_trials", "sponsor_company_id", True),
    ("clinical_trials", "source_document_id", True),
    ("endpoints", "trial_id", False),
    ("endpoints", "source_evidence_id", True),
    ("trial_results", "trial_id", False),
    ("trial_results", "endpoint_id", True),
    ("trial_results", "source_evidence_id", True),
    ("adverse_events", "drug_asset_id", True),
    ("adverse_events", "trial_id", True),
    ("adverse_events", "source_evidence_id", True),
    ("regulatory_approvals", "drug_asset_id", False),
    ("regulatory_approvals", "indication_id", True),
    ("regulatory_approvals", "regulatory_document_id", True),
    ("regulatory_approvals", "source_evidence_id", True),
    ("source_documents", "data_source_id", True),
    ("evidence_snippets", "source_document_id", False),
    ("evidence_snippets", "entity_id", True),
    ("ingestion_jobs", "data_source_id", True),
)

FOREIGN_KEYS = (
    ("fk_asset_primary_source", "drug_assets", "primary_source_id", "source_documents", "SET NULL"),
    ("fk_indication_parent", "indications", "parent_indication_id", "indications", "SET NULL"),
    ("fk_trial_sponsor", "clinical_trials", "sponsor_company_id", "companies", "SET NULL"),
    ("fk_trial_source", "clinical_trials", "source_document_id", "source_documents", "SET NULL"),
    ("fk_endpoint_trial", "endpoints", "trial_id", "clinical_trials", "CASCADE"),
    ("fk_endpoint_evidence", "endpoints", "source_evidence_id", "evidence_snippets", "SET NULL"),
    ("fk_result_trial", "trial_results", "trial_id", "clinical_trials", "CASCADE"),
    ("fk_result_endpoint", "trial_results", "endpoint_id", "endpoints", "SET NULL"),
    ("fk_result_evidence", "trial_results", "source_evidence_id", "evidence_snippets", "SET NULL"),
    ("fk_ae_asset", "adverse_events", "drug_asset_id", "drug_assets", "SET NULL"),
    ("fk_ae_trial", "adverse_events", "trial_id", "clinical_trials", "SET NULL"),
    ("fk_ae_evidence", "adverse_events", "source_evidence_id", "evidence_snippets", "SET NULL"),
    ("fk_reg_asset", "regulatory_approvals", "drug_asset_id", "drug_assets", "CASCADE"),
    ("fk_reg_indication", "regulatory_approvals", "indication_id", "indications", "SET NULL"),
    (
        "fk_reg_document",
        "regulatory_approvals",
        "regulatory_document_id",
        "source_documents",
        "SET NULL",
    ),
    (
        "fk_reg_evidence",
        "regulatory_approvals",
        "source_evidence_id",
        "evidence_snippets",
        "SET NULL",
    ),
    ("fk_source_data_source", "source_documents", "data_source_id", "data_sources", "SET NULL"),
    (
        "fk_evidence_document",
        "evidence_snippets",
        "source_document_id",
        "source_documents",
        "CASCADE",
    ),
    ("fk_job_data_source", "ingestion_jobs", "data_source_id", "data_sources", "SET NULL"),
)

RLS_TABLES = (
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


def upgrade() -> None:
    for table, column, nullable in UUID_COLUMNS:
        op.alter_column(
            table,
            column,
            existing_type=sa.String(),
            type_=postgresql.UUID(as_uuid=True),
            existing_nullable=nullable,
            postgresql_using=f"{column}::uuid",
        )

    for name, child, column, parent, ondelete in FOREIGN_KEYS:
        op.create_foreign_key(
            name,
            child,
            parent,
            [column],
            ["id"],
            ondelete=ondelete,
            deferrable=True,
            initially="DEFERRED",
        )

    op.create_table(
        "clinical_trial_assets",
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
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("trial_id", "asset_id"),
    )
    op.create_index("ix_trial_assets_asset_id", "clinical_trial_assets", ["asset_id"])
    op.execute("""
        INSERT INTO clinical_trial_assets (trial_id, asset_id, source_document_id)
        SELECT DISTINCT trial.id, asset.id, trial.source_document_id
        FROM clinical_trials AS trial
        CROSS JOIN LATERAL unnest(COALESCE(trial.drug_asset_ids, ARRAY[]::text[])) AS linked(id)
        JOIN drug_assets AS asset ON asset.id::text = linked.id
        ON CONFLICT (trial_id, asset_id) DO NOTHING
    """)

    op.create_check_constraint(
        "ck_evidence_confidence_range",
        "evidence_snippets",
        "confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)",
    )
    op.create_check_constraint(
        "ck_asset_confidence_range",
        "drug_assets",
        "source_confidence IS NULL OR (source_confidence >= 0 AND source_confidence <= 1)",
    )
    op.create_check_constraint(
        "ck_asset_completeness_range",
        "drug_assets",
        "data_completeness_score IS NULL OR "
        "(data_completeness_score >= 0 AND data_completeness_score <= 1)",
    )
    op.create_check_constraint(
        "ck_job_nonnegative_counts",
        "ingestion_jobs",
        "COALESCE(records_fetched, 0) >= 0 AND COALESCE(records_inserted, 0) >= 0 "
        "AND COALESCE(records_updated, 0) >= 0 AND COALESCE(records_rejected, 0) >= 0 "
        "AND COALESCE(records_skipped, 0) >= 0",
    )

    for table in RLS_TABLES:
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
        op.execute(
            f'CREATE POLICY "backend_read_{table}" ON "{table}" FOR SELECT TO PUBLIC '
            "USING (current_user IN "
            "('gennomx_app', 'gennomx_worker', 'gennomx_readonly'))"
        )
        op.execute(
            f'CREATE POLICY "worker_write_{table}" ON "{table}" FOR ALL TO PUBLIC '
            "USING (current_user = 'gennomx_worker') "
            "WITH CHECK (current_user = 'gennomx_worker')"
        )

    for table in ("mcp_query_logs", "security_events"):
        op.execute(
            f'CREATE POLICY "app_write_{table}" ON "{table}" FOR INSERT TO PUBLIC '
            "WITH CHECK (current_user = 'gennomx_app')"
        )

    op.execute("""
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gennomx_readonly') THEN
            GRANT SELECT ON ALL TABLES IN SCHEMA public TO gennomx_readonly;
          END IF;
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gennomx_app') THEN
            GRANT SELECT ON ALL TABLES IN SCHEMA public TO gennomx_app;
            GRANT INSERT ON mcp_query_logs, security_events TO gennomx_app;
          END IF;
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gennomx_worker') THEN
            GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public
              TO gennomx_worker;
          END IF;
        END
        $$;
    """)


def downgrade() -> None:
    for table in reversed(RLS_TABLES):
        if table in {"mcp_query_logs", "security_events"}:
            op.execute(f'DROP POLICY "app_write_{table}" ON "{table}"')
        op.execute(f'DROP POLICY "worker_write_{table}" ON "{table}"')
        op.execute(f'DROP POLICY "backend_read_{table}" ON "{table}"')
        op.execute(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY')

    op.drop_constraint("ck_job_nonnegative_counts", "ingestion_jobs", type_="check")
    op.drop_constraint("ck_asset_completeness_range", "drug_assets", type_="check")
    op.drop_constraint("ck_asset_confidence_range", "drug_assets", type_="check")
    op.drop_constraint("ck_evidence_confidence_range", "evidence_snippets", type_="check")

    for name, child, _column, _parent, _ondelete in reversed(FOREIGN_KEYS):
        op.drop_constraint(name, child, type_="foreignkey")

    op.drop_table("clinical_trial_assets")

    for table, column, nullable in reversed(UUID_COLUMNS):
        op.alter_column(
            table,
            column,
            existing_type=postgresql.UUID(as_uuid=True),
            type_=sa.String(length=200 if column == "primary_source_id" else 50),
            existing_nullable=nullable,
            postgresql_using=f"{column}::text",
        )
