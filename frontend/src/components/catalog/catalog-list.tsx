"use client";

import { useCallback, useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SearchInput } from "@/components/ui/search-input";
import { Pagination } from "@/components/ui/pagination";
import { SkeletonRow } from "@/components/ui/skeleton";
import type { PaginatedResponse } from "@/lib/types";

export type CatalogColumn<T> = {
  label: string;
  render: (item: T) => React.ReactNode;
};

type Props<T> = {
  title: string;
  description: string;
  searchPlaceholder: string;
  emptyLabel: string;
  load: (filters: { q?: string; page: number; page_size: number }) => Promise<PaginatedResponse<T>>;
  columns: CatalogColumn<T>[];
  itemKey: (item: T) => string;
};

const PAGE_SIZE = 20;

export function CatalogList<T>({ title, description, searchPlaceholder, emptyLabel, load, columns, itemKey }: Props<T>) {
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const [result, setResult] = useState<PaginatedResponse<T> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setResult(await load({ ...(q ? { q } : {}), page, page_size: PAGE_SIZE }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao carregar dados");
    } finally {
      setLoading(false);
    }
  }, [load, page, q]);

  useEffect(() => {
    const timer = setTimeout(refresh, q ? 300 : 0);
    return () => clearTimeout(timer);
  }, [refresh, q]);
  useEffect(() => setPage(1), [q]);

  const items = result?.data ?? [];
  return (
    <div className="max-w-7xl mx-auto space-y-5">
      <div>
        <h1 className="page-title">{title}</h1>
        <p className="text-sm text-slate-500 mt-0.5">{description}{result ? ` · ${result.meta.total} registros` : ""}</p>
      </div>
      <Card padding="md">
        <SearchInput value={q} onChange={setQ} placeholder={searchPlaceholder} className="max-w-xl" />
      </Card>
      <Card padding="none" className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead><tr className="border-b border-slate-100 bg-slate-50/70">
              {columns.map((column) => <th key={column.label} className="table-header px-5 py-3 text-left">{column.label}</th>)}
            </tr></thead>
            <tbody className="divide-y divide-slate-50">
              {loading && Array.from({ length: 5 }).map((_, index) => (
                <tr key={index}><td colSpan={columns.length} className="px-5 py-3"><SkeletonRow /></td></tr>
              ))}
              {!loading && error && <tr><td colSpan={columns.length} className="px-5 py-10 text-center text-sm text-danger">{error}</td></tr>}
              {!loading && !error && items.length === 0 && <tr><td colSpan={columns.length} className="px-5 py-10 text-center text-sm text-slate-500">{emptyLabel}</td></tr>}
              {!loading && items.map((item) => (
                <tr key={itemKey(item)} className="hover:bg-slate-50/60">
                  {columns.map((column) => <td key={column.label} className="px-5 py-3.5 text-sm text-slate-700">{column.render(item)}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!loading && items.length > 0 && <div className="px-5 py-3 border-t border-slate-100">
          <Pagination page={page} total_pages={result?.meta.total_pages ?? 1} onPage={setPage} />
        </div>}
      </Card>
    </div>
  );
}

export function StringBadges({ values }: { values: string[] }) {
  if (!values.length) return <span className="text-slate-300">—</span>;
  return <div className="flex flex-wrap gap-1">{values.slice(0, 2).map((value) => <Badge key={value} variant="slate">{value}</Badge>)}</div>;
}
