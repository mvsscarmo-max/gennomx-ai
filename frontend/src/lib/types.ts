// ── Pagination ────────────────────────────────────────────────────────────────

export interface PaginationMeta {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  meta: PaginationMeta;
}

// ── DrugAsset ─────────────────────────────────────────────────────────────────

export interface DrugAssetSummary {
  id: string;
  primary_name: string;
  aliases: string[];
  inn: string | null;
  modality: string | null;
  development_stage: string | null;
  indication_names: string[];
  target_symbols: string[];
  sponsor_names: string[];
  source_confidence: number | null;
  updated_at: string | null;
}

export interface DrugAssetDetail extends DrugAssetSummary {
  mechanism_of_action: string | null;
  external_ids: Record<string, string> | null;
  regulatory_status_summary: Record<string, unknown> | null;
  data_completeness_score: number | null;
  created_at: string | null;
}

// ── Company ───────────────────────────────────────────────────────────────────

export interface CompanySummary {
  id: string;
  legal_name: string;
  aliases: string[];
  company_type: string | null;
  country: string | null;
  website: string | null;
  asset_count: number;
  active_trial_count: number;
  updated_at: string | null;
}

export interface IndicationSummary {
  id: string;
  preferred_name: string;
  aliases: string[];
  therapeutic_area: string | null;
  ontology_ids: Record<string, string>;
  parent_indication_id: string | null;
  updated_at: string | null;
}

export interface TargetSummary {
  id: string;
  symbol: string;
  name: string | null;
  aliases: string[];
  organism: string | null;
  target_type: string | null;
  external_ids: Record<string, string>;
  open_targets_score: number | null;
  associated_indication_ids: string[];
  updated_at: string | null;
}

export interface McpAuditSummary {
  id: string;
  timestamp: string | null;
  tool_name: string;
  requesting_client: string | null;
  result_count: number | null;
  latency_ms: number | null;
  status: string | null;
  error_type: string | null;
  entity_types_accessed: string[];
  safety_flags: string[];
}

export interface SecurityEventSummary {
  id: string;
  timestamp: string | null;
  event_type: string;
  severity: string | null;
  actor_type: string | null;
  endpoint_or_tool: string | null;
  description: string | null;
  action_taken: string | null;
  status: string | null;
}

// ── ClinicalTrial ─────────────────────────────────────────────────────────────

export interface TrialSummary {
  id: string;
  nct_id: string;
  title: string;
  phase: string | null;
  phase_normalized: string | null;
  status: string | null;
  status_normalized: string | null;
  sponsor: string | null;
  conditions: string[];
  enrollment: number | null;
  start_date: string | null;
  primary_completion_date: string | null;
  countries: string[];
  updated_at: string | null;
}

// ── DataSource ────────────────────────────────────────────────────────────────

export interface DataSourceSummary {
  id: string;
  name: string;
  slug: string;
  category: string | null;
  access_method: string | null;
  license_status: string | null;
  connector_status: string | null;
  is_enabled: boolean;
  last_successful_run: string | null;
  last_failed_run: string | null;
  updated_at: string | null;
}

// ── IngestionJob ──────────────────────────────────────────────────────────────

export interface IngestionJobSummary {
  id: string;
  source_slug: string;
  job_type: string;
  status: string;
  celery_task_id: string | null;
  started_at: string | null;
  finished_at: string | null;
  duration_seconds: number | null;
  records_fetched: number;
  records_inserted: number;
  records_updated: number;
  records_rejected: number;
  error_type: string | null;
  error_summary: string | null;
  updated_at: string | null;
}

// ── Overview stats ────────────────────────────────────────────────────────────

export interface OverviewStats {
  total_assets: number;
  total_companies: number;
  total_trials: number;
  active_sources: number;
  last_ingest: string | null;
}
