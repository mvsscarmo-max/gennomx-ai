"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { governanceApi, type GovernanceStatus } from "@/lib/api";

export default function GovernancePage() {
  const [data, setData] = useState<GovernanceStatus | null>(null);
  const [message, setMessage] = useState<string>("");
  const [confirmingRetention, setConfirmingRetention] = useState(false);

  async function refresh() {
    setData(await governanceApi.status());
  }

  useEffect(() => {
    refresh().catch((error: unknown) =>
      setMessage(error instanceof Error ? error.message : "Falha ao carregar governança")
    );
  }, []);

  async function pause(domain: string) {
    await governanceApi.pauseDomain(domain);
    setMessage(`Kill switch ativado para ${domain}`);
    await refresh();
  }

  async function runRetention(dryRun: boolean) {
    const result = await governanceApi.runRetention(dryRun);
    setMessage(`Retenção enfileirada: ${result.task_id}`);
  }

  async function confirmRunRetention() {
    setConfirmingRetention(false);
    await runRetention(false);
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Governança de Dados</h1>
          <p className="text-sm text-slate-500 mt-1">
            Retenção, legal holds, manifestos e kill switches de coleta
          </p>
        </div>
        <div className="flex gap-2">
          <button className="btn-secondary" onClick={() => runRetention(true)}>
            Simular retenção
          </button>
          <button className="btn-danger" onClick={() => setConfirmingRetention(true)}>
            Executar retenção
          </button>
        </div>
      </div>

      {message && <div className="rounded-lg bg-slate-100 p-3 text-sm">{message}</div>}

      <ConfirmDialog
        open={confirmingRetention}
        tone="danger"
        title="Executar retenção de dados"
        description="Esta ação aplica as políticas de retenção agora, arquivando ou excluindo permanentemente os registros elegíveis. Não há undo. Use 'Simular retenção' primeiro se não tiver certeza do impacto."
        confirmLabel="Executar mesmo assim"
        cancelLabel="Cancelar"
        onConfirm={confirmRunRetention}
        onCancel={() => setConfirmingRetention(false)}
      />

      <Card>
        <CardHeader><CardTitle>Domínios de coleta</CardTitle></CardHeader>
        <div className="space-y-3">
          {(data?.scraper_domains ?? []).map((domain) => (
            <div key={domain.domain} className="flex items-center justify-between border-b pb-3">
              <div>
                <strong>{domain.domain}</strong>
                <p className="text-xs text-slate-500">
                  {domain.owner} · {domain.requests_per_minute}/min · concorrência {domain.max_concurrency}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={domain.active && !domain.kill_switch ? "success" : "danger"}>
                  {domain.kill_switch ? "pausado" : domain.active ? "ativo" : "inativo"}
                </Badge>
                {!domain.kill_switch && (
                  <button className="btn-secondary" onClick={() => pause(domain.domain)}>
                    Acionar kill switch
                  </button>
                )}
              </div>
            </div>
          ))}
          {!data?.scraper_domains.length && <p className="text-sm text-slate-500">Nenhum domínio autorizado.</p>}
        </div>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Políticas de retenção</CardTitle></CardHeader>
          <div className="space-y-2 text-sm">
            {(data?.retention_policies ?? []).map((policy) => (
              <div key={policy.resource_type} className="flex justify-between border-b py-2">
                <span>{policy.resource_type}</span>
                <span className="text-slate-500">
                  quente {policy.hot_days}d · arquivo {policy.archive_after_days ?? "—"}d · exclusão {policy.delete_after_days ?? "nunca"}
                </span>
              </div>
            ))}
          </div>
        </Card>
        <Card>
          <CardHeader><CardTitle>Legal holds ativos</CardTitle></CardHeader>
          <div className="space-y-2 text-sm">
            {(data?.active_legal_holds ?? []).map((hold) => (
              <div key={hold.id} className="border-b py-2">
                <strong>{hold.resource_type}</strong>
                <p className="text-slate-500">{hold.reason}</p>
              </div>
            ))}
            {!data?.active_legal_holds.length && <p className="text-slate-500">Nenhum legal hold ativo.</p>}
          </div>
        </Card>
      </div>
    </div>
  );
}
