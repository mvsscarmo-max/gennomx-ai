"""Operationalize metadata, corrections, retention, and scraper governance.

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-21
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def _govern_table(table: str, *, app_insert: bool = False) -> None:
    op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
    op.execute(
        f'CREATE POLICY "backend_read_{table}" ON "{table}" FOR SELECT TO PUBLIC '
        "USING (current_user IN ('gennomx_app', 'gennomx_worker', 'gennomx_readonly'))"
    )
    op.execute(
        f'CREATE POLICY "worker_write_{table}" ON "{table}" FOR ALL TO PUBLIC '
        "USING (current_user = 'gennomx_worker') "
        "WITH CHECK (current_user = 'gennomx_worker')"
    )
    if app_insert:
        op.execute(
            f'CREATE POLICY "app_insert_{table}" ON "{table}" FOR INSERT TO PUBLIC '
            "WITH CHECK (current_user = 'gennomx_app')"
        )


def upgrade() -> None:
    for table in (
        "endpoints",
        "trial_results",
        "adverse_events",
        "regulatory_approvals",
        "publications",
    ):
        op.add_column(table, sa.Column("valid_from", sa.DateTime(timezone=True)))
        op.add_column(table, sa.Column("valid_to", sa.DateTime(timezone=True)))
        op.add_column(
            table,
            sa.Column(
                "system_from",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )
        op.add_column(table, sa.Column("system_to", sa.DateTime(timezone=True)))
        op.add_column(
            table, sa.Column("is_current", sa.Boolean(), nullable=False, server_default="true")
        )
        op.add_column(
            table,
            sa.Column("lifecycle_status", sa.String(50), nullable=False, server_default="active"),
        )
        op.create_index(
            f"ix_{table}_current", table, ["is_current"], postgresql_where=sa.text("is_current")
        )
    op.execute("""
        CREATE UNIQUE INDEX uq_endpoint_granularity_current
        ON endpoints (
          trial_id, COALESCE(arm_id::text, ''), lower(endpoint_name), COALESCE(timepoint, '')
        ) WHERE is_current = true
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_trial_result_granularity_current
        ON trial_results (
          trial_id, COALESCE(endpoint_id::text, ''), COALESCE(arm_id::text, ''),
          COALESCE(timepoint, ''), COALESCE(population, '')
        ) WHERE is_current = true
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_adverse_event_granularity_current
        ON adverse_events (
          COALESCE(trial_id::text, ''), COALESCE(drug_asset_id::text, ''),
          lower(event_name), COALESCE(grade, ''), COALESCE(population, '')
        ) WHERE is_current = true
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_regulatory_granularity_current
        ON regulatory_approvals (
          drug_asset_id, COALESCE(indication_id::text, ''), COALESCE(region, ''),
          COALESCE(agency, ''), COALESCE(application_number, '')
        ) WHERE is_current = true
    """)
    for column in (
        sa.Column("data_class", sa.String(50), nullable=False, server_default="operational"),
        sa.Column("source_type", sa.String(50)),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="50"),
        sa.Column(
            "evidence_maturity", sa.String(50), nullable=False, server_default="unclassified"
        ),
        sa.Column("novelty_score", sa.Float()),
        sa.Column("clinical_impact_score", sa.Float()),
        sa.Column("validation_status", sa.String(30), nullable=False, server_default="unvalidated"),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
    ):
        op.add_column("field_assertions", column)
    op.create_check_constraint(
        "ck_assertion_priority", "field_assertions", "priority >= 0 AND priority <= 100"
    )
    op.create_check_constraint(
        "ck_assertion_novelty",
        "field_assertions",
        "novelty_score IS NULL OR (novelty_score >= 0 AND novelty_score <= 1)",
    )
    op.create_check_constraint(
        "ck_assertion_clinical_impact",
        "field_assertions",
        "clinical_impact_score IS NULL OR "
        "(clinical_impact_score >= 0 AND clinical_impact_score <= 1)",
    )
    op.create_index(
        "ix_assertion_expiry",
        "field_assertions",
        ["expires_at"],
        postgresql_where=sa.text("is_current = true AND expires_at IS NOT NULL"),
    )

    op.add_column("manual_corrections", sa.Column("granularity_key", sa.String(500)))
    op.add_column("manual_corrections", sa.Column("decision_reason", sa.Text()))
    op.add_column("manual_corrections", sa.Column("reviewed_at", sa.DateTime(timezone=True)))
    op.create_index(
        "ix_manual_corrections_pending",
        "manual_corrections",
        ["review_status", "created_at"],
    )

    op.create_table(
        "retention_policies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("resource_type", sa.String(100), nullable=False, unique=True),
        sa.Column("hot_days", sa.Integer(), nullable=False),
        sa.Column("archive_after_days", sa.Integer()),
        sa.Column("delete_after_days", sa.Integer()),
        sa.Column("archive_destination", sa.String(500)),
        sa.Column("policy_version", sa.String(100), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
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
        sa.CheckConstraint("hot_days >= 0", name="ck_retention_hot_days"),
        sa.CheckConstraint(
            "archive_after_days IS NULL OR archive_after_days >= hot_days",
            name="ck_retention_archive_window",
        ),
        sa.CheckConstraint(
            "delete_after_days IS NULL OR archive_after_days IS NULL OR delete_after_days >= archive_after_days",
            name="ck_retention_delete_window",
        ),
    )
    op.create_table(
        "legal_holds",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.String(500)),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(200), nullable=False),
        sa.Column(
            "starts_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("released_at", sa.DateTime(timezone=True)),
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
    op.create_index(
        "ix_legal_hold_active", "legal_holds", ["resource_type", "resource_id", "released_at"]
    )
    op.create_table(
        "archive_manifests",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True)),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("record_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("content_checksum", sa.String(64)),
        sa.Column("storage_uri", sa.String(1000)),
        sa.Column("status", sa.String(30), nullable=False, server_default="planned"),
        sa.Column("dry_run", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("policy_version", sa.String(100), nullable=False),
        sa.Column("error_detail", postgresql.JSONB()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
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
        sa.CheckConstraint("record_count >= 0", name="ck_archive_manifest_count"),
    )
    op.create_index(
        "ix_archive_manifest_status", "archive_manifests", ["resource_type", "status", "window_end"]
    )
    op.create_table(
        "archive_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "manifest_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("archive_manifests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.String(500), nullable=False),
        sa.Column(
            "archived_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("resource_type", "resource_id", name="uq_archive_item_resource"),
    )
    op.create_index("ix_archive_items_manifest", "archive_items", ["manifest_id"])

    op.create_table(
        "scraper_domain_policies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("domain", sa.String(253), nullable=False, unique=True),
        sa.Column("owner", sa.String(200), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("legal_basis", sa.Text(), nullable=False),
        sa.Column("terms_reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("robots_policy", sa.String(30), nullable=False),
        sa.Column("requests_per_minute", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("max_concurrency", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "allowed_schemes",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[\"https\"]'::jsonb"),
        ),
        sa.Column(
            "allowed_hosts",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("kill_switch", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("consecutive_auth_failures", sa.Integer(), nullable=False, server_default="0"),
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
        sa.CheckConstraint("requests_per_minute BETWEEN 1 AND 600", name="ck_scraper_rate"),
        sa.CheckConstraint("max_concurrency BETWEEN 1 AND 20", name="ck_scraper_concurrency"),
    )
    op.create_table(
        "scraper_access_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "domain_policy_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("scraper_domain_policies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("url_hash", sa.String(64), nullable=False),
        sa.Column("outcome", sa.String(50), nullable=False),
        sa.Column("http_status", sa.Integer()),
        sa.Column("detail", postgresql.JSONB()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_scraper_events_domain_time", "scraper_access_events", ["domain_policy_id", "created_at"]
    )

    for table in (
        "retention_policies",
        "legal_holds",
        "archive_items",
        "archive_manifests",
        "scraper_domain_policies",
        "scraper_access_events",
    ):
        _govern_table(table)

    op.execute(
        "CREATE POLICY app_curate_manual_corrections ON manual_corrections "
        "FOR ALL TO PUBLIC USING (current_user = 'gennomx_app') "
        "WITH CHECK (current_user = 'gennomx_app')"
    )
    op.execute(
        "CREATE POLICY app_curate_field_assertions ON field_assertions "
        "FOR ALL TO PUBLIC USING (current_user = 'gennomx_app') "
        "WITH CHECK (current_user = 'gennomx_app')"
    )
    op.execute(
        "CREATE POLICY app_manage_legal_holds ON legal_holds "
        "FOR ALL TO PUBLIC USING (current_user = 'gennomx_app') "
        "WITH CHECK (current_user = 'gennomx_app')"
    )
    op.execute(
        "CREATE POLICY app_manage_scraper_domains ON scraper_domain_policies "
        "FOR ALL TO PUBLIC USING (current_user = 'gennomx_app') "
        "WITH CHECK (current_user = 'gennomx_app')"
    )

    op.execute("""
        INSERT INTO retention_policies
            (resource_type, hot_days, archive_after_days, delete_after_days,
             archive_destination, policy_version)
        VALUES
            ('field_assertions', 3650, 3650, NULL, 'object://archive/assertions', '2026-06-21.1'),
            ('source_documents', 2555, 2555, NULL, 'object://raw', '2026-06-21.1'),
            ('ingestion_jobs', 180, 365, 1825, 'object://archive/jobs', '2026-06-21.1'),
            ('mcp_query_logs', 90, 180, 1825, 'object://archive/mcp', '2026-06-21.1'),
            ('security_events', 180, 365, 1825, 'object://archive/security', '2026-06-21.1')
        ON CONFLICT (resource_type) DO NOTHING
    """)

    op.execute("""
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gennomx_app') THEN
            GRANT SELECT ON retention_policies, legal_holds, archive_manifests,
              archive_items, scraper_domain_policies, scraper_access_events TO gennomx_app;
            GRANT INSERT, UPDATE ON legal_holds TO gennomx_app;
            GRANT INSERT, UPDATE ON scraper_domain_policies TO gennomx_app;
            GRANT INSERT, UPDATE ON manual_corrections, field_assertions TO gennomx_app;
          END IF;
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gennomx_worker') THEN
            GRANT SELECT, INSERT, UPDATE, DELETE ON retention_policies, legal_holds,
              archive_manifests, archive_items, scraper_domain_policies,
              scraper_access_events TO gennomx_worker;
          END IF;
        END
        $$;
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS app_curate_field_assertions ON field_assertions")
    op.execute("DROP POLICY IF EXISTS app_curate_manual_corrections ON manual_corrections")
    for table in (
        "scraper_access_events",
        "scraper_domain_policies",
        "archive_items",
        "archive_manifests",
        "legal_holds",
        "retention_policies",
    ):
        op.drop_table(table)
    op.drop_index("ix_manual_corrections_pending", table_name="manual_corrections")
    for column in ("reviewed_at", "decision_reason", "granularity_key"):
        op.drop_column("manual_corrections", column)
    op.drop_index("ix_assertion_expiry", table_name="field_assertions")
    op.drop_constraint("ck_assertion_clinical_impact", "field_assertions", type_="check")
    op.drop_constraint("ck_assertion_novelty", "field_assertions", type_="check")
    op.drop_constraint("ck_assertion_priority", "field_assertions", type_="check")
    for column in (
        "archived_at",
        "expires_at",
        "validation_status",
        "clinical_impact_score",
        "novelty_score",
        "evidence_maturity",
        "priority",
        "source_type",
        "data_class",
    ):
        op.drop_column("field_assertions", column)
    for index in (
        "uq_regulatory_granularity_current",
        "uq_adverse_event_granularity_current",
        "uq_trial_result_granularity_current",
        "uq_endpoint_granularity_current",
    ):
        op.execute(f'DROP INDEX IF EXISTS "{index}"')
    for table in (
        "publications",
        "regulatory_approvals",
        "adverse_events",
        "trial_results",
        "endpoints",
    ):
        op.drop_index(f"ix_{table}_current", table_name=table)
        for column in (
            "lifecycle_status",
            "is_current",
            "system_to",
            "system_from",
            "valid_to",
            "valid_from",
        ):
            op.drop_column(table, column)
