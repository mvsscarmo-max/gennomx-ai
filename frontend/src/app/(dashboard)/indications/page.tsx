"use client";

import { CatalogList, StringBadges } from "@/components/catalog/catalog-list";
import { indicationsApi } from "@/lib/api";
import type { IndicationSummary } from "@/lib/types";
import { formatRelative } from "@/lib/utils";

export default function IndicationsPage() {
  return <CatalogList<IndicationSummary>
    title="Indicações" description="Condições clínicas e áreas terapêuticas normalizadas"
    searchPlaceholder="Buscar condição ou alias..." emptyLabel="Nenhuma indicação encontrada"
    load={indicationsApi.list} itemKey={(item) => item.id}
    columns={[
      { label: "Indicação", render: (item) => <div><strong>{item.preferred_name}</strong><StringBadges values={item.aliases} /></div> },
      { label: "Área terapêutica", render: (item) => item.therapeutic_area ?? "—" },
      { label: "Ontologias", render: (item) => <StringBadges values={Object.entries(item.ontology_ids).map(([key, value]) => `${key}: ${value}`)} /> },
      { label: "Atualizado", render: (item) => formatRelative(item.updated_at) },
    ]}
  />;
}
