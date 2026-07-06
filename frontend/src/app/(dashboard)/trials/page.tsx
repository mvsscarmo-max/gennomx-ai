"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ExternalLink } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SearchInput } from "@/components/ui/search-input";
import { Pagination } from "@/components/ui/pagination";
import { SkeletonRow } from "@/components/ui/skeleton";
import { trialsApi, type TrialFilters } from "@/lib/api";
import { formatNumber, statusVariant, phaseLabel } from "@/lib/utils";
import type { TrialSummary, PaginatedResponse } from "@/lib/types";

const PAGE_SIZE = 20;

export default function TrialsPage() {
  const [q, setQ] = useState("");
  const [phase, setPhase] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [result, setResult] = useState<PaginatedResponse<TrialSummary> | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchTrials = useCallback(async () => {
    setLoading(true);
    setError(null);
    const filters: TrialFilters = { page, page_size: PAGE_SIZE };
    if (q) filters.q = q;
    if (phase) filters.phase = phase;
    if (status) filters.status = status;
    try {
      setResult(await trialsApi.list(filters));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar ensaios");
    } finally {
      setLoading(false);
    }
  }, [q, phase, status, page]);

  useEffect(() => {
    const t = setTimeout(fetchTrials, q ? 300 : 0);
    return () => clearTimeout(t);
  }, [fetchTrials, q]);
  useEffect(() => { setPage(1); }, [q, phase, status]);

  const items = result?.data ?? [];
  const total_pages = result ? Math.ceil(result.meta.total / PAGE_SIZE) : 0;

  return (
    <div className="space-y-5 max-w-7xl mx-auto">
      <div>
        <h1 className="page-title">Ensaios Clínicos</h1>
        <p className="text-sm text-slate-500 mt-0.5">
          {result ? `${formatNumber(result.meta.total)} ensaios indexados` : ""}
        </p>
      </div>

      <Card padding="md" className="flex flex-wrap items-center gap-3">
        <SearchInput value={q} onChange={setQ} placeholder="NCT ID, título, sponsor..." className="flex-1 min-w-52" />
        <select value={phase} onChange={(e) => setPhase(e.target.value)} className="input w-36">
          <option value="">Fase</option>
          {["PHASE1","PHASE2","PHASE3","PHASE4","PHASE1_2","PHASE2_3"].map((p) => (
            <option key={p} value={p}>{phaseLabel(p)}</option>
          ))}
        </select>
        <select value={status} onChange={(e) => setStatus(e.target.value)} className="input w-44">
          <option value="">Status</option>
          {["RECRUITING","ACTIVE_NOT_RECRUITING","COMPLETED","TERMINATED","WITHDRAWN","NOT_YET_RECRUITING"].map((s) => (
            <option key={s} value={s}>{s.replace(/_/g, " ")}</option>
          ))}
        </select>
        {(q || phase || status) && (
          <button onClick={() => { setQ(""); setPhase(""); setStatus(""); }} className="btn-ghost text-xs">
            Limpar
          </button>
        )}
      </Card>

      <Card padding="none" className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50/70">
                <th className="table-header px-5 py-3 text-left">NCT ID</th>
                <th className="table-header px-4 py-3 text-left">Título</th>
                <th className="table-header px-4 py-3 text-left">Fase</th>
                <th className="table-header px-4 py-3 text-left">Status</th>
                <th className="table-header px-4 py-3 text-left">Sponsor</th>
                <th className="table-header px-4 py-3 text-left">Enroll.</th>
                <th className="table-header px-4 py-3 text-left">Início</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {loading && Array.from({ length: 6 }).map((_, i) => (
                <tr key={i}><td colSpan={7} className="px-5 py-3"><SkeletonRow /></td></tr>
              ))}
              {!loading && error && (
                <tr><td colSpan={7} className="px-5 py-10 text-center text-sm text-danger">{error}</td></tr>
              )}
              {!loading && !error && items.length === 0 && (
                <tr><td colSpan={7} className="px-5 py-10 text-center text-sm text-slate-500">Nenhum ensaio encontrado</td></tr>
              )}
              {!loading && items.map((trial) => (
                <tr key={trial.id} className="hover:bg-slate-50/60 transition-colors">
                  <td className="px-5 py-3.5">
                    <Link href={`https://clinicaltrials.gov/study/${trial.nct_id}`} target="_blank"
                      className="text-sm font-mono text-slate-700 hover:text-brand-rose-dark hover:underline flex items-center gap-1">
                      {trial.nct_id}
                      <ExternalLink className="h-3 w-3" />
                    </Link>
                  </td>
                  <td className="px-4 py-3.5 max-w-xs">
                    <p className="text-sm text-slate-800 line-clamp-2">{trial.title}</p>
                  </td>
                  <td className="px-4 py-3.5">
                    {trial.phase_normalized ? (
                      <Badge variant="slate">{phaseLabel(trial.phase_normalized)}</Badge>
                    ) : <span className="text-slate-300 text-xs">—</span>}
                  </td>
                  <td className="px-4 py-3.5">
                    {trial.status_normalized ? (
                      <Badge variant={statusVariant(trial.status_normalized)}>
                        {trial.status_normalized.replace(/_/g, " ")}
                      </Badge>
                    ) : <span className="text-slate-300 text-xs">—</span>}
                  </td>
                  <td className="px-4 py-3.5">
                    <span className="text-sm text-slate-600 truncate block max-w-40">{trial.sponsor ?? "—"}</span>
                  </td>
                  <td className="px-4 py-3.5">
                    <span className="text-sm text-slate-600 tabular-nums">
                      {trial.enrollment !== null ? formatNumber(trial.enrollment) : "—"}
                    </span>
                  </td>
                  <td className="px-4 py-3.5">
                    <span className="text-xs text-slate-500">{trial.start_date?.slice(0, 7) ?? "—"}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!loading && items.length > 0 && (
          <div className="px-5 py-3 border-t border-slate-100">
            <Pagination page={page} total_pages={total_pages} onPage={setPage} />
          </div>
        )}
      </Card>
    </div>
  );
}
