import { Suspense } from "react";
import {
  Activity,
  Beaker,
  Building2,
  ServerCog,
  Stethoscope,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  fetchServerOverviewStats,
  serverJobsApi,
  serverSourcesApi,
} from "@/lib/api-server";
import { formatRelative, formatNumber } from "@/lib/utils";
import type { DataSourceSummary, IngestionJobSummary } from "@/lib/types";

export const metadata = { title: "Visão Geral" };
export const dynamic = "force-dynamic";

async function StatsSection() {
  const stats = await fetchServerOverviewStats().catch(() => ({
    total_assets: 0,
    total_companies: 0,
    total_trials: 0,
    active_sources: 0,
    last_ingest: null,
  }));

  const statItems = [
    { label: "Ativos terapêuticos", value: stats.total_assets, icon: Beaker, color: "text-brand-rose" },
    { label: "Empresas", value: stats.total_companies, icon: Building2, color: "text-slate-600" },
    { label: "Ensaios clínicos", value: stats.total_trials, icon: Stethoscope, color: "text-info" },
    { label: "Fontes ativas", value: stats.active_sources, icon: ServerCog, color: "text-success" },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {statItems.map(({ label, value, icon: Icon, color }) => (
        <Card key={label} padding="md" className="flex items-center gap-4">
          <div className={`flex-shrink-0 p-2.5 rounded-xl bg-slate-50 ${color}`}>
            <Icon className="h-5 w-5" />
          </div>
          <div>
            <p className="stat-value">{formatNumber(value)}</p>
            <p className="stat-label">{label}</p>
          </div>
        </Card>
      ))}
    </div>
  );
}

async function SourcesPanel() {
  let sources: DataSourceSummary[] = [];
  try {
    const res = await serverSourcesApi.list();
    sources = res.data;
  } catch {
    sources = [];
  }

  const statusVariantMap: Record<string, "success" | "warning" | "danger" | "slate"> = {
    active: "success",
    inactive: "slate",
    error: "danger",
    pending: "warning",
  };

  return (
    <Card padding="none" className="overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-100">
        <h2 className="section-title">Fontes de Dados</h2>
      </div>
      {sources.length === 0 ? (
        <div className="px-5 py-8 text-center text-sm text-slate-500">
          Nenhuma fonte configurada
        </div>
      ) : (
        <ul className="divide-y divide-slate-50">
          {sources.map((s) => (
            <li key={s.id} className="px-5 py-3 flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="text-sm font-medium text-slate-800 truncate">{s.name}</p>
                <p className="text-xs text-slate-500 truncate">
                  {s.last_successful_run
                    ? `Última execução: ${formatRelative(s.last_successful_run)}`
                    : "Nunca executada"}
                </p>
              </div>
              <Badge variant={statusVariantMap[s.connector_status ?? ""] ?? "slate"}>
                {s.connector_status ?? "—"}
              </Badge>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

async function RecentJobsPanel() {
  let jobs: IngestionJobSummary[] = [];
  try {
    const res = await serverJobsApi.list();
    jobs = res.data.slice(0, 8);
  } catch {
    jobs = [];
  }

  const statusVariantMap: Record<string, "success" | "warning" | "danger" | "info" | "slate"> = {
    success: "success",
    failed: "danger",
    running: "info",
    partial: "warning",
    pending: "slate",
  };

  return (
    <Card padding="none" className="overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2">
        <Activity className="h-4 w-4 text-slate-500" />
        <h2 className="section-title">Jobs Recentes</h2>
      </div>
      {jobs.length === 0 ? (
        <div className="px-5 py-8 text-center text-sm text-slate-500">
          Nenhum job registrado
        </div>
      ) : (
        <ul className="divide-y divide-slate-50">
          {jobs.map((j) => (
            <li key={j.id} className="px-5 py-3 flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="text-sm font-medium text-slate-800 truncate">{j.source_slug}</p>
                <p className="text-xs text-slate-500">
                  {formatRelative(j.started_at)}
                  {j.records_fetched > 0 && ` · ${formatNumber(j.records_fetched)} registros`}
                </p>
              </div>
              <Badge variant={statusVariantMap[j.status] ?? "slate"}>{j.status}</Badge>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

export default function OverviewPage() {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="page-title">Visão Geral</h1>
        <p className="text-sm text-slate-500 mt-0.5">
          Infraestrutura de dados biomédicos e inteligência competitiva
        </p>
      </div>

      <Suspense
        fallback={
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-20 rounded-card" />
            ))}
          </div>
        }
      >
        <StatsSection />
      </Suspense>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Suspense fallback={<Skeleton className="h-64 rounded-card" />}>
          <SourcesPanel />
        </Suspense>
        <Suspense fallback={<Skeleton className="h-64 rounded-card" />}>
          <RecentJobsPanel />
        </Suspense>
      </div>
    </div>
  );
}
