"use client";

import { Badge } from "@/components/ui/badge";
import { CatalogList, StringBadges } from "@/components/catalog/catalog-list";
import { auditApi } from "@/lib/api";
import type { McpAuditSummary } from "@/lib/types";
import { formatNumber, formatRelative } from "@/lib/utils";

const loadMcpLogs = ({ q, ...filters }: { q?: string; page: number; page_size: number }) =>
  auditApi.mcp({ ...filters, tool_name: q });

export default function McpLogsPage() {
  return <CatalogList<McpAuditSummary>
    title="Logs MCP" description="Auditoria sanitizada; argumentos, tokens e identificadores pessoais não são exibidos"
    searchPlaceholder="Filtrar pelo nome exato da ferramenta..." emptyLabel="Nenhuma chamada MCP registrada"
    load={loadMcpLogs} itemKey={(item) => item.id}
    columns={[
      { label: "Ferramenta", render: (item) => <strong className="font-mono">{item.tool_name}</strong> },
      { label: "Cliente", render: (item) => item.requesting_client ?? "—" },
      { label: "Status", render: (item) => <Badge variant={item.status === "success" ? "success" : item.status === "blocked" || item.status === "error" ? "danger" : "warning"}>{item.status ?? "—"}</Badge> },
      { label: "Resultados", render: (item) => formatNumber(item.result_count) },
      { label: "Latência", render: (item) => item.latency_ms == null ? "—" : `${item.latency_ms.toFixed(0)} ms` },
      { label: "Entidades", render: (item) => <StringBadges values={item.entity_types_accessed} /> },
      { label: "Sinais", render: (item) => <StringBadges values={item.safety_flags} /> },
      { label: "Quando", render: (item) => formatRelative(item.timestamp) },
    ]}
  />;
}
