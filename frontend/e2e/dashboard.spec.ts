import { expect, test, type Page } from "@playwright/test";

const meta = { total: 1, page: 1, page_size: 20, total_pages: 1, has_next: false, has_previous: false };

async function mockApi(page: Page) {
  await page.route("http://127.0.0.1:8000/api/v1/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    const datasets: Record<string, unknown[]> = {
      "/api/v1/companies": [{ id: "c1", legal_name: "GennomX Biotech", aliases: ["GX Bio"], company_type: "biotech", country: "Brasil", website: "https://example.org", asset_count: 3, active_trial_count: 2, updated_at: "2026-06-20T12:00:00Z" }],
      "/api/v1/indications": [{ id: "i1", preferred_name: "Melanoma", aliases: [], therapeutic_area: "Oncologia", ontology_ids: { mesh: "D008545" }, parent_indication_id: null, updated_at: "2026-06-20T12:00:00Z" }],
      "/api/v1/targets": [{ id: "t1", symbol: "BRAF", name: "B-Raf", aliases: [], organism: "Homo sapiens", target_type: "protein", external_ids: {}, open_targets_score: 0.91, associated_indication_ids: ["i1"], updated_at: "2026-06-20T12:00:00Z" }],
      "/api/v1/jobs": [{ id: "j1", source_slug: "clinicaltrials_gov", job_type: "incremental", status: "success", celery_task_id: null, started_at: "2026-06-20T12:00:00Z", finished_at: "2026-06-20T12:01:00Z", duration_seconds: 60, records_fetched: 20, records_inserted: 10, records_updated: 10, records_rejected: 0, error_type: null, error_summary: null, updated_at: "2026-06-20T12:01:00Z" }],
      "/api/v1/audit/mcp": [{ id: "m1", timestamp: "2026-06-20T12:00:00Z", tool_name: "search_drugs", requesting_client: "claude", result_count: 2, latency_ms: 18, status: "success", error_type: null, entity_types_accessed: ["drug_asset"], safety_flags: [] }],
      "/api/v1/audit/security": [{ id: "s1", timestamp: "2026-06-20T12:00:00Z", event_type: "rate_limit", severity: "medium", actor_type: "mcp_token", endpoint_or_tool: "search_drugs", description: "Limite aplicado", action_taken: "blocked", status: "open" }],
    };
    await route.fulfill({ json: { success: true, data: datasets[path] ?? [], meta } });
  });
}

test.beforeEach(async ({ page }) => mockApi(page));

for (const scenario of [
  ["/ai/companies", "Empresas", "GennomX Biotech"],
  ["/ai/indications", "Indicações", "Melanoma"],
  ["/ai/targets", "Targets", "BRAF"],
  ["/ai/jobs", "Jobs de Ingestão", "clinicaltrials_gov"],
  ["/ai/mcp-logs", "Logs MCP", "search_drugs"],
  ["/ai/security", "Segurança Operacional", "rate_limit"],
] as const) {
  test(`${scenario[1]} renderiza dados da API`, async ({ page }) => {
    await page.goto(scenario[0]);
    await expect(page.getByRole("heading", { name: scenario[1] })).toBeVisible();
    await expect(page.getByText(scenario[2], { exact: true }).first()).toBeVisible();
  });
}

test("busca de empresas atualiza o contrato sem perder a tela", async ({ page }) => {
  await page.goto("/ai/companies");
  await page.getByPlaceholder("Buscar razão social ou alias...").fill("GennomX");
  await expect(page.getByText("GennomX Biotech", { exact: true })).toBeVisible();
});
