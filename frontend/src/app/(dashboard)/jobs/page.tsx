"use client";

import { Badge } from "@/components/ui/badge";
import { CatalogList } from "@/components/catalog/catalog-list";
import { jobsApi } from "@/lib/api";
import type { IngestionJobSummary } from "@/lib/types";
import { formatNumber, formatRelative } from "@/lib/utils";

const loadJobs = ({ q, ...filters }: { q?: string; page: number; page_size: number }) =>
  jobsApi.list({ ...filters, source_slug: q });

export default function JobsPage() {
  return <CatalogList<IngestionJobSummary>
    title="Jobs de Ingestão" description="Execuções, volumes e falhas dos conectores"
    searchPlaceholder="Filtrar pelo slug exato da fonte..." emptyLabel="Nenhum job registrado"
    load={loadJobs} itemKey={(item) => item.id}
    columns={[
      { label: "Fonte", render: (item) => <div><strong>{item.source_slug}</strong><div className="text-xs text-slate-500">{item.job_type}</div></div> },
      { label: "Status", render: (item) => <Badge variant={item.status === "success" ? "success" : item.status === "failed" ? "danger" : item.status === "running" ? "info" : "warning"}>{item.status}</Badge> },
      { label: "Coletados", render: (item) => formatNumber(item.records_fetched) },
      { label: "Inseridos/atualizados", render: (item) => `${formatNumber(item.records_inserted)} / ${formatNumber(item.records_updated)}` },
      { label: "Rejeitados", render: (item) => formatNumber(item.records_rejected) },
      { label: "Início", render: (item) => formatRelative(item.started_at) },
      { label: "Erro", render: (item) => item.error_summary ? <span className="text-danger" title={item.error_summary}>{item.error_type ?? "falha"}</span> : "—" },
    ]}
  />;
}
