"""Initial schema — all core entities

Revision ID: 0001
Revises:
Create Date: 2026-06-09
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ─── Extensions ──────────────────────────────────────────────────────────
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # ─── drug_assets ─────────────────────────────────────────────────────────
    op.create_table(
        "drug_assets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("primary_name", sa.String(500), nullable=False),
        sa.Column("aliases", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("inn", sa.String(300), nullable=True),
        sa.Column("modality", sa.String(100), nullable=True),
        sa.Column("mechanism_of_action", sa.String(500), nullable=True),
        sa.Column("development_stage", sa.String(100), nullable=True),
        sa.Column("external_ids", postgresql.JSONB(), nullable=True),
        sa.Column("indication_names", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("target_symbols", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("sponsor_names", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("regulatory_status_summary", postgresql.JSONB(), nullable=True),
        sa.Column("source_confidence", sa.Float(), nullable=True),
        sa.Column("data_completeness_score", sa.Float(), nullable=True),
        sa.Column("primary_source_id", sa.String(200), nullable=True),
        sa.Column("ingestion_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("search_vector", sa.Text(), nullable=True),
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
    )
    op.create_index("ix_drug_assets_primary_name", "drug_assets", ["primary_name"])
    op.execute(
        "CREATE INDEX ix_drug_assets_primary_name_trgm ON drug_assets "
        "USING gin (primary_name gin_trgm_ops)"
    )
    op.execute("CREATE INDEX ix_drug_assets_aliases ON drug_assets USING gin (aliases)")
    op.execute("CREATE INDEX ix_drug_assets_external_ids ON drug_assets USING gin (external_ids)")

    # ─── companies ───────────────────────────────────────────────────────────
    op.create_table(
        "companies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("legal_name", sa.String(500), nullable=False),
        sa.Column("aliases", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("company_type", sa.String(100), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("investor_relations_url", sa.String(500), nullable=True),
        sa.Column("pipeline_url", sa.String(500), nullable=True),
        sa.Column("external_ids", postgresql.JSONB(), nullable=True),
        sa.Column("asset_count", sa.Integer(), nullable=True),
        sa.Column("active_trial_count", sa.Integer(), nullable=True),
        sa.Column("ingestion_metadata", postgresql.JSONB(), nullable=True),
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
    )
    op.create_index("ix_companies_legal_name", "companies", ["legal_name"])

    # ─── indications ─────────────────────────────────────────────────────────
    op.create_table(
        "indications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("preferred_name", sa.String(500), nullable=False),
        sa.Column("aliases", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("therapeutic_area", sa.String(200), nullable=True),
        sa.Column("ontology_ids", postgresql.JSONB(), nullable=True),
        sa.Column("parent_indication_id", sa.String(50), nullable=True),
        sa.Column("ingestion_metadata", postgresql.JSONB(), nullable=True),
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
    )
    op.create_index("ix_indications_preferred_name", "indications", ["preferred_name"])
    op.create_index("ix_indications_therapeutic_area", "indications", ["therapeutic_area"])

    # ─── targets ─────────────────────────────────────────────────────────────
    op.create_table(
        "targets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("symbol", sa.String(100), nullable=False),
        sa.Column("name", sa.String(500), nullable=True),
        sa.Column("aliases", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("organism", sa.String(100), nullable=True),
        sa.Column("target_type", sa.String(100), nullable=True),
        sa.Column("external_ids", postgresql.JSONB(), nullable=True),
        sa.Column("open_targets_score", sa.Float(), nullable=True),
        sa.Column("associated_indication_ids", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("ingestion_metadata", postgresql.JSONB(), nullable=True),
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
    )
    op.create_index("ix_targets_symbol", "targets", ["symbol"])

    # ─── clinical_trials ──────────────────────────────────────────────────────
    op.create_table(
        "clinical_trials",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("nct_id", sa.String(50), nullable=True, unique=True),
        sa.Column("eudract_number", sa.String(50), nullable=True),
        sa.Column("other_ids", postgresql.JSONB(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("brief_title", sa.Text(), nullable=True),
        sa.Column("official_title", sa.Text(), nullable=True),
        sa.Column("phase", sa.String(50), nullable=True),
        sa.Column("phase_normalized", sa.String(50), nullable=True),
        sa.Column("status", sa.String(100), nullable=True),
        sa.Column("status_normalized", sa.String(50), nullable=True),
        sa.Column("sponsor_name", sa.String(500), nullable=True),
        sa.Column("sponsor_company_id", sa.String(50), nullable=True),
        sa.Column("collaborators", postgresql.JSONB(), nullable=True),
        sa.Column("conditions", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("indication_ids", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("interventions", postgresql.JSONB(), nullable=True),
        sa.Column("drug_asset_ids", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("arms", postgresql.JSONB(), nullable=True),
        sa.Column("enrollment", sa.Integer(), nullable=True),
        sa.Column("enrollment_type", sa.String(50), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("primary_completion_date", sa.Date(), nullable=True),
        sa.Column("completion_date", sa.Date(), nullable=True),
        sa.Column("last_update_date", sa.Date(), nullable=True),
        sa.Column("countries", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("locations", postgresql.JSONB(), nullable=True),
        sa.Column("eligibility_criteria", sa.Text(), nullable=True),
        sa.Column("minimum_age", sa.String(50), nullable=True),
        sa.Column("maximum_age", sa.String(50), nullable=True),
        sa.Column("sex", sa.String(20), nullable=True),
        sa.Column("registry_source", sa.String(100), nullable=True),
        sa.Column("source_document_id", sa.String(50), nullable=True),
        sa.Column("raw_payload_hash", sa.String(64), nullable=True),
        sa.Column("ingestion_metadata", postgresql.JSONB(), nullable=True),
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
    )
    op.create_index("ix_ct_nct_id", "clinical_trials", ["nct_id"])
    op.create_index(
        "ix_ct_phase_status", "clinical_trials", ["phase_normalized", "status_normalized"]
    )
    op.execute("CREATE INDEX ix_ct_conditions ON clinical_trials USING gin (conditions)")
    op.execute("CREATE INDEX ix_ct_drug_asset_ids ON clinical_trials USING gin (drug_asset_ids)")

    # ─── endpoints ───────────────────────────────────────────────────────────
    op.create_table(
        "endpoints",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("trial_id", sa.String(50), nullable=False),
        sa.Column("arm_id", sa.String(50), nullable=True),
        sa.Column("endpoint_name", sa.Text(), nullable=False),
        sa.Column("endpoint_type", sa.String(50), nullable=True),
        sa.Column("category", sa.String(200), nullable=True),
        sa.Column("timepoint", sa.String(200), nullable=True),
        sa.Column("measurement_unit", sa.String(200), nullable=True),
        sa.Column("source_evidence_id", sa.String(50), nullable=True),
        sa.Column("ingestion_metadata", postgresql.JSONB(), nullable=True),
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
    )
    op.create_index("ix_endpoints_trial_id", "endpoints", ["trial_id"])
    op.create_index("ix_endpoints_type", "endpoints", ["endpoint_type"])

    # ─── trial_results ────────────────────────────────────────────────────────
    op.create_table(
        "trial_results",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("trial_id", sa.String(50), nullable=False),
        sa.Column("endpoint_id", sa.String(50), nullable=True),
        sa.Column("arm_id", sa.String(50), nullable=True),
        sa.Column("arm_label", sa.String(500), nullable=True),
        sa.Column("result_value", sa.Text(), nullable=True),
        sa.Column("comparator_value", sa.Text(), nullable=True),
        sa.Column("statistical_measure", sa.String(200), nullable=True),
        sa.Column("p_value", sa.Float(), nullable=True),
        sa.Column("confidence_interval_lower", sa.Float(), nullable=True),
        sa.Column("confidence_interval_upper", sa.Float(), nullable=True),
        sa.Column("hazard_ratio", sa.Float(), nullable=True),
        sa.Column("odds_ratio", sa.Float(), nullable=True),
        sa.Column("timepoint", sa.String(200), nullable=True),
        sa.Column("population", sa.Text(), nullable=True),
        sa.Column("n_analyzed", sa.Integer(), nullable=True),
        sa.Column("raw_result", postgresql.JSONB(), nullable=True),
        sa.Column("source_evidence_id", sa.String(50), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("extraction_method", sa.String(50), nullable=True),
        sa.Column("ingestion_metadata", postgresql.JSONB(), nullable=True),
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
    )
    op.create_index("ix_trial_results_trial_id", "trial_results", ["trial_id"])
    op.create_index("ix_trial_results_endpoint_id", "trial_results", ["endpoint_id"])

    # ─── adverse_events ───────────────────────────────────────────────────────
    op.create_table(
        "adverse_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("drug_asset_id", sa.String(50), nullable=True),
        sa.Column("trial_id", sa.String(50), nullable=True),
        sa.Column("source_type", sa.String(50), nullable=True),
        sa.Column("event_name", sa.String(500), nullable=False),
        sa.Column("meddra_code", sa.String(50), nullable=True),
        sa.Column("grade", sa.String(50), nullable=True),
        sa.Column("seriousness", sa.String(50), nullable=True),
        sa.Column("incidence_rate", sa.Float(), nullable=True),
        sa.Column("comparator_incidence_rate", sa.Float(), nullable=True),
        sa.Column("n_events", sa.Integer(), nullable=True),
        sa.Column("n_subjects_at_risk", sa.Integer(), nullable=True),
        sa.Column("population", sa.Text(), nullable=True),
        sa.Column("source_evidence_id", sa.String(50), nullable=True),
        sa.Column("ingestion_metadata", postgresql.JSONB(), nullable=True),
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
    )
    op.create_index("ix_ae_drug_asset_id", "adverse_events", ["drug_asset_id"])
    op.create_index("ix_ae_event_name", "adverse_events", ["event_name"])

    # ─── regulatory_approvals ─────────────────────────────────────────────────
    op.create_table(
        "regulatory_approvals",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("drug_asset_id", sa.String(50), nullable=False),
        sa.Column("indication_id", sa.String(50), nullable=True),
        sa.Column("indication_name", sa.String(500), nullable=True),
        sa.Column("region", sa.String(100), nullable=True),
        sa.Column("agency", sa.String(100), nullable=True),
        sa.Column("approval_status", sa.String(100), nullable=True),
        sa.Column("approval_date", sa.Date(), nullable=True),
        sa.Column("submission_date", sa.Date(), nullable=True),
        sa.Column("pathway", sa.String(100), nullable=True),
        sa.Column("special_designations", postgresql.JSONB(), nullable=True),
        sa.Column("label_url", sa.String(1000), nullable=True),
        sa.Column("regulatory_document_id", sa.String(50), nullable=True),
        sa.Column("source_evidence_id", sa.String(50), nullable=True),
        sa.Column("application_number", sa.String(200), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(), nullable=True),
        sa.Column("ingestion_metadata", postgresql.JSONB(), nullable=True),
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
    )
    op.create_index("ix_reg_drug_asset_id", "regulatory_approvals", ["drug_asset_id"])
    op.create_index("ix_reg_agency_status", "regulatory_approvals", ["agency", "approval_status"])

    # ─── publications ─────────────────────────────────────────────────────────
    op.create_table(
        "publications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("journal", sa.String(500), nullable=True),
        sa.Column("publication_date", sa.Date(), nullable=True),
        sa.Column("publication_type", sa.String(100), nullable=True),
        sa.Column("doi", sa.String(200), nullable=True, unique=True),
        sa.Column("pmid", sa.String(50), nullable=True, unique=True),
        sa.Column("pmcid", sa.String(50), nullable=True),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column("authors", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("keywords", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("linked_trial_ids", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("linked_asset_ids", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("linked_indication_ids", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("source_url", sa.String(1000), nullable=True),
        sa.Column("open_access", sa.Boolean(), nullable=True),
        sa.Column("ingestion_metadata", postgresql.JSONB(), nullable=True),
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
    )
    op.create_index("ix_publications_publication_date", "publications", ["publication_date"])
    op.create_index("ix_publications_doi", "publications", ["doi"])
    op.create_index("ix_publications_pmid", "publications", ["pmid"])

    # ─── source_documents ─────────────────────────────────────────────────────
    op.create_table(
        "source_documents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("data_source_id", sa.String(50), nullable=True),
        sa.Column("source_type", sa.String(100), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("url", sa.String(2000), nullable=True),
        sa.Column("file_path", sa.String(2000), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_storage_path", sa.String(2000), nullable=True),
        sa.Column("processed_storage_path", sa.String(2000), nullable=True),
        sa.Column("license_status", sa.String(100), nullable=True),
        sa.Column("language", sa.String(20), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
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
    )
    op.create_index("ix_source_doc_content_hash", "source_documents", ["content_hash"])
    op.create_index("ix_source_doc_data_source_id", "source_documents", ["data_source_id"])

    # ─── evidence_snippets ────────────────────────────────────────────────────
    op.create_table(
        "evidence_snippets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("source_document_id", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=True),
        sa.Column("entity_id", sa.String(50), nullable=True),
        sa.Column("entity_field", sa.String(200), nullable=True),
        sa.Column("text_excerpt", sa.Text(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("section", sa.String(500), nullable=True),
        sa.Column("extraction_method", sa.String(50), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
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
    )
    op.create_index("ix_evidence_entity", "evidence_snippets", ["entity_type", "entity_id"])
    op.create_index("ix_evidence_source_doc", "evidence_snippets", ["source_document_id"])

    # ─── data_sources ─────────────────────────────────────────────────────────
    op.create_table(
        "data_sources",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("access_method", sa.String(50), nullable=True),
        sa.Column("official_url", sa.String(1000), nullable=True),
        sa.Column("api_url", sa.String(1000), nullable=True),
        sa.Column("license_status", sa.String(50), nullable=True),
        sa.Column("update_frequency", sa.String(50), nullable=True),
        sa.Column("connector_status", sa.String(50), nullable=True, server_default="inactive"),
        sa.Column("compliance_notes", sa.Text(), nullable=True),
        sa.Column("owner", sa.String(200), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("last_successful_run", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failed_run", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column("connector_config", postgresql.JSONB(), nullable=True),
        sa.Column("health_metrics", postgresql.JSONB(), nullable=True),
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
    )
    op.create_index("ix_data_source_slug", "data_sources", ["slug"])

    # ─── ingestion_jobs ───────────────────────────────────────────────────────
    op.create_table(
        "ingestion_jobs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("data_source_id", sa.String(50), nullable=True),
        sa.Column("data_source_slug", sa.String(100), nullable=True),
        sa.Column("job_type", sa.String(100), nullable=True),
        sa.Column("celery_task_id", sa.String(200), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("records_fetched", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("records_inserted", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("records_updated", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("records_rejected", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("records_skipped", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("error_type", sa.String(200), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("error_detail", postgresql.JSONB(), nullable=True),
        sa.Column("ai_cost_usd", sa.Float(), nullable=True),
        sa.Column("data_quality_score", sa.Float(), nullable=True),
        sa.Column("test_status", sa.String(50), nullable=True),
        sa.Column("raw_log_path", sa.String(2000), nullable=True),
        sa.Column("raw_payload_hash", sa.String(64), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
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
    )
    op.create_index(
        "ix_ingestion_job_source_status", "ingestion_jobs", ["data_source_slug", "status"]
    )
    op.create_index("ix_ingestion_job_created_at", "ingestion_jobs", ["created_at"])

    # ─── mcp_query_logs ───────────────────────────────────────────────────────
    op.create_table(
        "mcp_query_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tool_name", sa.String(100), nullable=False),
        sa.Column("requesting_client", sa.String(100), nullable=True),
        sa.Column("user_id", sa.String(100), nullable=True),
        sa.Column("organization_id", sa.String(100), nullable=True),
        sa.Column("input_hash", sa.String(64), nullable=True),
        sa.Column("normalized_arguments", postgresql.JSONB(), nullable=True),
        sa.Column("result_count", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("error_type", sa.String(200), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("source_entities_accessed", postgresql.JSONB(), nullable=True),
        sa.Column("entity_types_accessed", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("safety_flags", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("ai_cost_usd", sa.Float(), nullable=True),
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
    )
    op.create_index("ix_mcp_log_tool_client", "mcp_query_logs", ["tool_name", "requesting_client"])
    op.create_index("ix_mcp_log_timestamp", "mcp_query_logs", ["timestamp"])
    op.create_index("ix_mcp_log_status", "mcp_query_logs", ["status"])

    # ─── security_events ──────────────────────────────────────────────────────
    op.create_table(
        "security_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(20), nullable=True),
        sa.Column("actor_type", sa.String(50), nullable=True),
        sa.Column("actor_id", sa.String(200), nullable=True),
        sa.Column("source_ip_hash", sa.String(64), nullable=True),
        sa.Column("endpoint_or_tool", sa.String(500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("action_taken", sa.String(200), nullable=True),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
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
    )
    op.create_index(
        "ix_security_event_type_severity", "security_events", ["event_type", "severity"]
    )
    op.create_index("ix_security_event_timestamp", "security_events", ["timestamp"])

    # ─── Seed data_sources with MVP connectors ─────────────────────────────
    op.execute("""
        INSERT INTO data_sources (id, name, slug, category, access_method, official_url, api_url,
                                   license_status, update_frequency, connector_status, is_enabled, created_at, updated_at)
        VALUES
          (gen_random_uuid(), 'ClinicalTrials.gov', 'clinicaltrials_gov', 'clinical_trials', 'api',
           'https://clinicaltrials.gov', 'https://clinicaltrials.gov/api/v2',
           'open', 'daily', 'inactive', false, now(), now()),
          (gen_random_uuid(), 'PubMed / PMC', 'pubmed_pmc', 'scientific', 'api',
           'https://pubmed.ncbi.nlm.nih.gov', 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/',
           'open', 'daily', 'inactive', false, now(), now()),
          (gen_random_uuid(), 'openFDA', 'openfda', 'regulatory', 'api',
           'https://open.fda.gov', 'https://api.fda.gov',
           'open', 'daily', 'inactive', false, now(), now()),
          (gen_random_uuid(), 'DailyMed', 'dailymed', 'regulatory', 'api',
           'https://dailymed.nlm.nih.gov/dailymed', 'https://dailymed.nlm.nih.gov/dailymed/services/',
           'open', 'daily', 'inactive', false, now(), now()),
          (gen_random_uuid(), 'EMA', 'ema', 'regulatory', 'api',
           'https://www.ema.europa.eu', 'https://www.ema.europa.eu/en/medicines',
           'open', 'weekly', 'inactive', false, now(), now()),
          (gen_random_uuid(), 'Open Targets', 'open_targets', 'genomics', 'api',
           'https://www.opentargets.org', 'https://api.platform.opentargets.org/api/v4/graphql',
           'open', 'weekly', 'inactive', false, now(), now()),
          (gen_random_uuid(), 'ANVISA', 'anvisa', 'regulatory', 'api',
           'https://www.gov.br/anvisa', 'https://consultas.anvisa.gov.br',
           'open', 'weekly', 'inactive', false, now(), now())
        ON CONFLICT (slug) DO NOTHING;
    """)


def downgrade() -> None:
    op.drop_table("security_events")
    op.drop_table("mcp_query_logs")
    op.drop_table("ingestion_jobs")
    op.drop_table("data_sources")
    op.drop_table("evidence_snippets")
    op.drop_table("source_documents")
    op.drop_table("publications")
    op.drop_table("regulatory_approvals")
    op.drop_table("adverse_events")
    op.drop_table("trial_results")
    op.drop_table("endpoints")
    op.drop_table("clinical_trials")
    op.drop_table("targets")
    op.drop_table("indications")
    op.drop_table("companies")
    op.drop_table("drug_assets")
