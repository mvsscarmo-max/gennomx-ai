import type {
  DataSourceSummary,
  CompanySummary,
  DrugAssetDetail,
  DrugAssetSummary,
  IngestionJobSummary,
  IndicationSummary,
  McpAuditSummary,
  OverviewStats,
  PaginatedResponse,
  TrialSummary,
  TargetSummary,
  SecurityEventSummary,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Core fetcher ───────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  let accessToken: string | undefined;
  if (typeof window !== "undefined") {
    const { getSupabaseBrowserClient } = await import("./supabase-browser");
    const { data } = await getSupabaseBrowserClient().auth.getSession();
    accessToken = data.session?.access_token;
  }
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const detail = (err as { detail?: string | { message?: string } }).detail;
    throw new Error(typeof detail === "string" ? detail : detail?.message ?? "API error");
  }

  return res.json() as Promise<T>;
}

type QueryParams = object;

function toQuery(params: QueryParams): string {
  const q = new URLSearchParams();
  for (const [key, val] of Object.entries(params)) {
    if (val !== null && val !== undefined && val !== "") {
      q.set(key, String(val));
    }
  }
  const qs = q.toString();
  return qs ? `?${qs}` : "";
}

// ── Assets ────────────────────────────────────────────────────────────────────

export interface AssetFilters {
  q?: string;
  indication?: string;
  target?: string;
  company?: string;
  phase?: string;
  page?: number;
  page_size?: number;
}

export const assetsApi = {
  list: (filters: AssetFilters = {}) =>
    apiFetch<PaginatedResponse<DrugAssetSummary>>(
      `/api/v1/assets${toQuery(filters)}`
    ),

  detail: (id: string) =>
    apiFetch<{ success: boolean; data: DrugAssetDetail }>(
      `/api/v1/assets/${id}`
    ),
};

// ── Trials ────────────────────────────────────────────────────────────────────

export interface TrialFilters {
  q?: string;
  nct_id?: string;
  phase?: string;
  status?: string;
  sponsor?: string;
  indication?: string;
  page?: number;
  page_size?: number;
}

export const trialsApi = {
  list: (filters: TrialFilters = {}) =>
    apiFetch<PaginatedResponse<TrialSummary>>(
      `/api/v1/trials${toQuery(filters)}`
    ),
};

export const companiesApi = {
  list: (filters: { q?: string; company_type?: string; country?: string; page?: number; page_size?: number } = {}) =>
    apiFetch<PaginatedResponse<CompanySummary>>(`/api/v1/companies${toQuery(filters)}`),
};

export const indicationsApi = {
  list: (filters: { q?: string; therapeutic_area?: string; page?: number; page_size?: number } = {}) =>
    apiFetch<PaginatedResponse<IndicationSummary>>(`/api/v1/indications${toQuery(filters)}`),
};

export const targetsApi = {
  list: (filters: { q?: string; target_type?: string; page?: number; page_size?: number } = {}) =>
    apiFetch<PaginatedResponse<TargetSummary>>(`/api/v1/targets${toQuery(filters)}`),
};

export const auditApi = {
  mcp: (filters: { status?: string; tool_name?: string; page?: number; page_size?: number } = {}) =>
    apiFetch<PaginatedResponse<McpAuditSummary>>(`/api/v1/audit/mcp${toQuery(filters)}`),
  security: (filters: { severity?: string; status?: string; page?: number; page_size?: number } = {}) =>
    apiFetch<PaginatedResponse<SecurityEventSummary>>(`/api/v1/audit/security${toQuery(filters)}`),
};

// ── Sources ───────────────────────────────────────────────────────────────────

export const sourcesApi = {
  list: () =>
    apiFetch<PaginatedResponse<DataSourceSummary>>(`/api/v1/sources`),
};

// ── Jobs ──────────────────────────────────────────────────────────────────────

export const jobsApi = {
  list: (filters: { source_slug?: string; status?: string; page?: number; page_size?: number } = {}) =>
    apiFetch<PaginatedResponse<IngestionJobSummary>>(
      `/api/v1/jobs${toQuery(filters)}`
    ),

  workerStatus: () =>
    apiFetch<{ success: boolean; data: { worker_count: number; active_tasks: number } }>(
      `/api/v1/jobs/worker-status`
    ),
};

// ── Health ────────────────────────────────────────────────────────────────────

export const healthApi = {
  check: () =>
    apiFetch<{ status: string; environment: string; version: string }>(`/health`),
};

export interface GovernanceStatus {
  scraper_domains: Array<{
    domain: string;
    owner: string;
    robots_policy: string;
    requests_per_minute: number;
    max_concurrency: number;
    active: boolean;
    kill_switch: boolean;
  }>;
  retention_policies: Array<{
    resource_type: string;
    hot_days: number;
    archive_after_days: number | null;
    delete_after_days: number | null;
    archive_destination: string | null;
    active: boolean;
  }>;
  active_legal_holds: Array<{
    id: string;
    resource_type: string;
    resource_id: string | null;
    reason: string;
  }>;
  archive_manifests: Array<{
    id: string;
    resource_type: string;
    record_count: number;
    status: string;
    dry_run: boolean;
    storage_uri: string | null;
  }>;
}

export const governanceApi = {
  status: () => apiFetch<GovernanceStatus>("/api/v1/governance/status"),
  pauseDomain: (domain: string) =>
    apiFetch<{ domain: string; status: string }>(
      `/api/v1/governance/scraper-domains/${encodeURIComponent(domain)}/pause`,
      { method: "POST" }
    ),
  runRetention: (dryRun: boolean) =>
    apiFetch<{ task_id: string; status: string }>("/api/v1/governance/retention/run", {
      method: "POST",
      body: JSON.stringify({ dry_run: dryRun, batch_size: 1000 }),
    }),
};

// ── Overview ──────────────────────────────────────────────────────────────────

export const overviewApi = {
  stats: () =>
    apiFetch<{ success: boolean; data: OverviewStats }>("/api/v1/overview").then(
      (response) => response.data,
    ),
};
