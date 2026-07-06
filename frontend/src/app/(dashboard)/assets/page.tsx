"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ExternalLink } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SearchInput } from "@/components/ui/search-input";
import { Pagination } from "@/components/ui/pagination";
import { SkeletonRow } from "@/components/ui/skeleton";
import { assetsApi, type AssetFilters } from "@/lib/api";
import { formatRelative, formatNumber, phaseLabel } from "@/lib/utils";
import type { DrugAssetSummary, PaginatedResponse } from "@/lib/types";

const PAGE_SIZE = 20;

function AssetsPageContent() {
  const searchParams = useSearchParams();
  const [q, setQ] = useState(() => searchParams.get("q") ?? "");
  const [indication, setIndication] = useState("");
  const [phase, setPhase] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [result, setResult] = useState<PaginatedResponse<DrugAssetSummary> | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchAssets = useCallback(async () => {
    setLoading(true);
    setError(null);
    const filters: AssetFilters = { page, page_size: PAGE_SIZE };
    if (q) filters.q = q;
    if (indication) filters.indication = indication;
    if (phase) filters.phase = phase;

    try {
      const data = await assetsApi.list(filters);
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar ativos");
    } finally {
      setLoading(false);
    }
  }, [q, indication, phase, page]);

  useEffect(() => {
    const t = setTimeout(fetchAssets, q ? 300 : 0);
    return () => clearTimeout(t);
  }, [fetchAssets, q]);

  useEffect(() => { setPage(1); }, [q, indication, phase]);

  const total_pages = result ? Math.ceil(result.meta.total / PAGE_SIZE) : 0;
  const items = result?.data ?? [];

  return (
    <div className="space-y-5 max-w-7xl mx-auto">
      {/* Page header */}
      <div>
        <h1 className="page-title">Ativos Terapêuticos</h1>
        <p className="text-sm text-slate-500 mt-0.5">
          {result ? `${formatNumber(result.meta.total)} ativos indexados` : ""}
        </p>
      </div>

      {/* Filters */}
      <Card padding="md" className="flex flex-wrap items-center gap-3">
        <SearchInput
          value={q}
          onChange={setQ}
          placeholder="Buscar ativo, INN, alias..."
          className="flex-1 min-w-52"
        />
        <input
          type="text"
          value={indication}
          onChange={(e) => setIndication(e.target.value)}
          placeholder="Indicação..."
          className="input w-44"
        />
        <select
          value={phase}
          onChange={(e) => setPhase(e.target.value)}
          className="input w-36"
        >
          <option value="">Fase</option>
          {["PHASE1", "PHASE2", "PHASE3", "PHASE4", "PHASE1_2", "PHASE2_3"].map((p) => (
            <option key={p} value={p}>{phaseLabel(p)}</option>
          ))}
        </select>
        {(q || indication || phase) && (
          <button
            onClick={() => { setQ(""); setIndication(""); setPhase(""); }}
            className="btn-ghost text-xs"
          >
            Limpar filtros
          </button>
        )}
      </Card>

      {/* Table */}
      <Card padding="none" className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50/70">
                <th className="table-header px-5 py-3 text-left">Ativo</th>
                <th className="table-header px-4 py-3 text-left">Modalidade</th>
                <th className="table-header px-4 py-3 text-left">Indicações</th>
                <th className="table-header px-4 py-3 text-left">Sponsor</th>
                <th className="table-header px-4 py-3 text-left">Confiança</th>
                <th className="table-header px-4 py-3 text-left">Atualizado</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {loading &&
                Array.from({ length: 6 }).map((_, i) => (
                  <tr key={i}>
                    <td colSpan={7} className="px-5 py-3">
                      <SkeletonRow />
                    </td>
                  </tr>
                ))}

              {!loading && error && (
                <tr>
                  <td colSpan={7} className="px-5 py-10 text-center text-sm text-danger">
                    {error}
                  </td>
                </tr>
              )}

              {!loading && !error && items.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-5 py-10 text-center text-sm text-slate-500">
                    Nenhum ativo encontrado
                  </td>
                </tr>
              )}

              {!loading &&
                items.map((asset) => (
                  <tr key={asset.id} className="hover:bg-slate-50/60 transition-colors group">
                    <td className="px-5 py-3.5">
                      <div>
                        <p className="text-sm font-semibold text-slate-900 group-hover:text-brand-rose-dark transition-colors">
                          {asset.primary_name}
                        </p>
                        {asset.inn && (
                          <p className="text-xs text-slate-500">{asset.inn}</p>
                        )}
                        {asset.aliases.length > 0 && (
                          <p className="text-xs text-slate-500 truncate max-w-xs">
                            {asset.aliases.slice(0, 2).join(", ")}
                          </p>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      {asset.modality ? (
                        <Badge variant="slate">{asset.modality}</Badge>
                      ) : (
                        <span className="text-slate-300 text-xs">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="flex flex-wrap gap-1 max-w-48">
                        {asset.indication_names.slice(0, 2).map((ind) => (
                          <Badge key={ind} variant="slate" className="truncate max-w-36">
                            {ind}
                          </Badge>
                        ))}
                        {asset.indication_names.length > 2 && (
                          <Badge variant="slate">+{asset.indication_names.length - 2}</Badge>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      <span className="text-sm text-slate-600 truncate block max-w-36">
                        {asset.sponsor_names[0] ?? "—"}
                      </span>
                    </td>
                    <td className="px-4 py-3.5">
                      {asset.source_confidence !== null && asset.source_confidence !== undefined ? (
                        <span className={`text-sm font-mono tabular-nums ${
                          asset.source_confidence >= 0.8 ? "text-success" :
                          asset.source_confidence >= 0.5 ? "text-warning" : "text-danger"
                        }`}>
                          {(asset.source_confidence * 100).toFixed(0)}%
                        </span>
                      ) : (
                        <span className="text-slate-300 text-xs">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3.5">
                      <span className="text-xs text-slate-500">
                        {formatRelative(asset.updated_at)}
                      </span>
                    </td>
                    <td className="px-4 py-3.5">
                      <Link
                        href={`/assets/${asset.id}`}
                        className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded text-slate-500 hover:text-brand-rose"
                        aria-label={`Ver ${asset.primary_name}`}
                      >
                        <ExternalLink className="h-4 w-4" />
                      </Link>
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

export default function AssetsPage() {
  return (
    <Suspense fallback={null}>
      <AssetsPageContent />
    </Suspense>
  );
}
