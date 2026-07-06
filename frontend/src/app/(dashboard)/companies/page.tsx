"use client";

import { ExternalLink } from "lucide-react";
import { CatalogList, StringBadges } from "@/components/catalog/catalog-list";
import { companiesApi } from "@/lib/api";
import type { CompanySummary } from "@/lib/types";
import { formatNumber, formatRelative, safeExternalUrl } from "@/lib/utils";

export default function CompaniesPage() {
  return <CatalogList<CompanySummary>
    title="Empresas" description="Sponsors, biotechs e organizações de pesquisa"
    searchPlaceholder="Buscar razão social ou alias..." emptyLabel="Nenhuma empresa encontrada"
    load={companiesApi.list} itemKey={(item) => item.id}
    columns={[
      { label: "Empresa", render: (item) => <div><strong>{item.legal_name}</strong><StringBadges values={item.aliases} /></div> },
      { label: "Tipo", render: (item) => item.company_type ?? "—" },
      { label: "País", render: (item) => item.country ?? "—" },
      { label: "Ativos", render: (item) => formatNumber(item.asset_count) },
      { label: "Trials ativos", render: (item) => formatNumber(item.active_trial_count) },
      { label: "Atualizado", render: (item) => formatRelative(item.updated_at) },
      { label: "Site", render: (item) => { const url = safeExternalUrl(item.website); return url ? <a href={url} target="_blank" rel="noreferrer" aria-label={`Abrir site de ${item.legal_name}`}><ExternalLink className="h-4 w-4" /></a> : "—"; } },
    ]}
  />;
}
