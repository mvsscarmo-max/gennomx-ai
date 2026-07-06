"use client";

import { Badge } from "@/components/ui/badge";
import { CatalogList } from "@/components/catalog/catalog-list";
import { auditApi } from "@/lib/api";
import type { SecurityEventSummary } from "@/lib/types";
import { formatRelative } from "@/lib/utils";

const loadSecurityEvents = ({ q, ...filters }: { q?: string; page: number; page_size: number }) =>
  auditApi.security({ ...filters, status: q });

export default function SecurityPage() {
  return <CatalogList<SecurityEventSummary>
    title="Segurança Operacional" description="Eventos auditáveis com IPs e identidades sensíveis omitidos"
    searchPlaceholder="Filtrar pelo status exato..." emptyLabel="Nenhum evento de segurança registrado"
    load={loadSecurityEvents} itemKey={(item) => item.id}
    columns={[
      { label: "Evento", render: (item) => <div><strong>{item.event_type}</strong><div className="text-xs text-slate-500">{item.endpoint_or_tool ?? "—"}</div></div> },
      { label: "Severidade", render: (item) => <Badge variant={item.severity === "critical" || item.severity === "high" ? "danger" : item.severity === "medium" ? "warning" : "slate"}>{item.severity ?? "—"}</Badge> },
      { label: "Ator", render: (item) => item.actor_type ?? "—" },
      { label: "Ação", render: (item) => item.action_taken ?? "—" },
      { label: "Status", render: (item) => item.status ?? "—" },
      { label: "Descrição", render: (item) => <span className="line-clamp-2 max-w-sm">{item.description ?? "—"}</span> },
      { label: "Quando", render: (item) => formatRelative(item.timestamp) },
    ]}
  />;
}
