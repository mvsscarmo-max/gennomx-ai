import { notFound } from "next/navigation";
import Link from "next/link";
import type { ReactNode } from "react";
import { ArrowLeft, ChevronRight } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { serverAssetsApi } from "@/lib/api-server";
import { formatDate, formatRelative } from "@/lib/utils";

interface Props {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: Props) {
  const { id } = await params;
  try {
    const res = await serverAssetsApi.detail(id);
    const asset = res.data;
    return { title: asset.primary_name };
  } catch {
    return { title: "Ativo não encontrado" };
  }
}

export default async function AssetDetailPage({ params }: Props) {
  const { id } = await params;
  let asset;
  try {
    const res = await serverAssetsApi.detail(id);
    asset = res.data;
  } catch {
    notFound();
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-sm text-slate-500">
        <Link href="/assets" className="hover:text-slate-600 transition-colors">
          Ativos
        </Link>
        <ChevronRight className="h-3.5 w-3.5" />
        <span className="text-slate-600 font-medium">{asset.primary_name}</span>
      </nav>

      {/* Header card */}
      <Card padding="lg">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="page-title">{asset.primary_name}</h1>
            {asset.inn && (
              <p className="text-sm text-slate-500 mt-0.5">INN: {asset.inn}</p>
            )}
            {asset.aliases.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {asset.aliases.map((a) => (
                  <Badge key={a} variant="slate">{a}</Badge>
                ))}
              </div>
            )}
          </div>
          <div className="flex flex-col items-end gap-2 flex-shrink-0">
            {asset.modality && (
              <Badge variant="slate">{asset.modality}</Badge>
            )}
            {asset.source_confidence !== null && asset.source_confidence !== undefined && (
              <span className={`text-xs font-mono tabular-nums font-medium ${
                asset.source_confidence >= 0.8 ? "text-success" :
                asset.source_confidence >= 0.5 ? "text-warning" : "text-danger"
              }`}>
                Confiança: {(asset.source_confidence * 100).toFixed(0)}%
              </span>
            )}
          </div>
        </div>
      </Card>

      {/* Details grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Mechanism & targets */}
        <Card padding="md">
          <CardHeader>
            <CardTitle>Ciência</CardTitle>
          </CardHeader>
          <dl className="space-y-3">
            <DetailRow label="Mecanismo de ação" value={asset.mechanism_of_action} />
            <DetailRow
              label="Targets"
              value={
                asset.target_symbols.length > 0 ? (
                  <div className="flex flex-wrap gap-1">
                    {asset.target_symbols.map((t) => (
                      <Badge key={t} variant="info">{t}</Badge>
                    ))}
                  </div>
                ) : null
              }
            />
          </dl>
        </Card>

        {/* Development */}
        <Card padding="md">
          <CardHeader>
            <CardTitle>Desenvolvimento</CardTitle>
          </CardHeader>
          <dl className="space-y-3">
            <DetailRow label="Estágio" value={asset.development_stage} />
            <DetailRow
              label="Sponsors"
              value={
                asset.sponsor_names.length > 0 ? (
                  <div className="flex flex-wrap gap-1">
                    {asset.sponsor_names.map((s) => (
                      <Badge key={s} variant="slate">{s}</Badge>
                    ))}
                  </div>
                ) : null
              }
            />
          </dl>
        </Card>

        {/* Indications */}
        <Card padding="md">
          <CardHeader>
            <CardTitle>Indicações</CardTitle>
          </CardHeader>
          {asset.indication_names.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {asset.indication_names.map((ind) => (
                <Badge key={ind} variant="slate">{ind}</Badge>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500">Nenhuma indicação registrada</p>
          )}
        </Card>

        {/* Status regulatório */}
        <Card padding="md">
          <CardHeader>
            <CardTitle>Status Regulatório</CardTitle>
          </CardHeader>
          {asset.regulatory_status_summary && Object.keys(asset.regulatory_status_summary).length > 0 ? (
            <RegulatoryStatusSummary data={asset.regulatory_status_summary} />
          ) : (
            <p className="text-sm text-slate-500">Sem dados regulatórios indexados</p>
          )}
        </Card>
      </div>

      {/* Metadata footer */}
      <Card padding="md" className="text-xs text-slate-500 flex flex-wrap gap-4">
        <span>Criado: {formatDate(asset.created_at)}</span>
        <span>Atualizado: {formatRelative(asset.updated_at)}</span>
        {asset.data_completeness_score !== null && (
          <span>Completude: {(asset.data_completeness_score! * 100).toFixed(0)}%</span>
        )}
        <span className="ml-auto font-mono">ID: {asset.id}</span>
      </Card>

      {/* Back link */}
      <Link
        href="/assets"
        className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Voltar para ativos
      </Link>
    </div>
  );
}

function humanizeKey(key: string): string {
  return key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function renderRegulatoryValue(value: unknown): ReactNode {
  if (value === null || value === undefined || value === "") {
    return <span className="text-slate-300">—</span>;
  }
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (Array.isArray(value)) {
    return value.length > 0
      ? value.map((v) => String(v)).join(", ")
      : <span className="text-slate-300">—</span>;
  }
  return (
    <span className="font-mono text-xs text-slate-600">
      {Object.entries(value as Record<string, unknown>)
        .map(([k, v]) => `${humanizeKey(k)}: ${String(v)}`)
        .join(" · ")}
    </span>
  );
}

function RegulatoryStatusSummary({ data }: { data: Record<string, unknown> }) {
  return (
    <dl className="space-y-3">
      {Object.entries(data).map(([key, value]) => (
        <div key={key} className="flex items-start justify-between gap-3">
          <dt className="text-xs font-medium text-slate-500 uppercase tracking-wide">
            {humanizeKey(key)}
          </dt>
          <dd className="text-sm text-slate-700 text-right">{renderRegulatoryValue(value)}</dd>
        </div>
      ))}
    </dl>
  );
}

function DetailRow({
  label,
  value,
}: {
  label: string;
  value: string | null | undefined | ReactNode;
}) {
  return (
    <div>
      <dt className="text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</dt>
      <dd className="mt-0.5 text-sm text-slate-700">
        {value ?? <span className="text-slate-300">—</span>}
      </dd>
    </div>
  );
}
