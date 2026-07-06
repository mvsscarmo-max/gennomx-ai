"use client";

import { CatalogList, StringBadges } from "@/components/catalog/catalog-list";
import { targetsApi } from "@/lib/api";
import type { TargetSummary } from "@/lib/types";
import { formatRelative } from "@/lib/utils";

export default function TargetsPage() {
  return <CatalogList<TargetSummary>
    title="Targets" description="Genes, proteínas e vias biológicas estruturadas"
    searchPlaceholder="Buscar símbolo, nome ou alias..." emptyLabel="Nenhum target encontrado"
    load={targetsApi.list} itemKey={(item) => item.id}
    columns={[
      { label: "Símbolo", render: (item) => <strong className="font-mono">{item.symbol}</strong> },
      { label: "Nome", render: (item) => <div>{item.name ?? "—"}<StringBadges values={item.aliases} /></div> },
      { label: "Tipo", render: (item) => item.target_type ?? "—" },
      { label: "Organismo", render: (item) => item.organism ?? "—" },
      { label: "Open Targets", render: (item) => item.open_targets_score == null ? "—" : `${(item.open_targets_score * 100).toFixed(0)}%` },
      { label: "Atualizado", render: (item) => formatRelative(item.updated_at) },
    ]}
  />;
}
