import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { serverSourcesApi } from "@/lib/api-server";
import type { DataSourceSummary } from "@/lib/types";
import { formatRelative } from "@/lib/utils";

export const metadata = { title: "Fontes de Dados" };
export const dynamic = "force-dynamic";

const statusVariantMap: Record<string, "success" | "warning" | "danger" | "slate"> = {
  active: "success",
  inactive: "slate",
  error: "danger",
  pending: "warning",
};

export default async function SourcesPage() {
  let sources: DataSourceSummary[] = [];
  try {
    const res = await serverSourcesApi.list();
    sources = res.data;
  } catch {
    sources = [];
  }

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      <h1 className="page-title">Fontes de Dados</h1>

      <div className="grid grid-cols-1 gap-4">
        {sources.length === 0 && (
          <Card padding="lg" className="text-center text-sm text-slate-500">
            Nenhuma fonte configurada
          </Card>
        )}
        {sources.map((s) => (
          <Card key={s.id} padding="md" hover className="flex items-start gap-5">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="section-title">{s.name}</h2>
                <Badge variant={statusVariantMap[s.connector_status ?? ""] ?? "slate"}>
                  {s.connector_status ?? "—"}
                </Badge>
                {!s.is_enabled && <Badge variant="slate">Desativada</Badge>}
              </div>
              <p className="text-xs text-slate-500 font-mono mt-0.5">{s.slug}</p>

              <dl className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                <div>
                  <dt className="text-xs text-slate-500 uppercase tracking-wide">Categoria</dt>
                  <dd className="text-slate-700">{s.category ?? "—"}</dd>
                </div>
                <div>
                  <dt className="text-xs text-slate-500 uppercase tracking-wide">Acesso</dt>
                  <dd className="text-slate-700">{s.access_method ?? "—"}</dd>
                </div>
                <div>
                  <dt className="text-xs text-slate-500 uppercase tracking-wide">Última execução</dt>
                  <dd className="text-slate-700">{formatRelative(s.last_successful_run)}</dd>
                </div>
                <div>
                  <dt className="text-xs text-slate-500 uppercase tracking-wide">Última falha</dt>
                  <dd className={s.last_failed_run ? "text-danger" : "text-slate-300"}>
                    {s.last_failed_run ? formatRelative(s.last_failed_run) : "—"}
                  </dd>
                </div>
              </dl>
            </div>

            <div className="flex-shrink-0 text-right">
              <Badge variant={s.license_status === "open" ? "success" : "warning"}>
                {s.license_status ?? "—"}
              </Badge>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
