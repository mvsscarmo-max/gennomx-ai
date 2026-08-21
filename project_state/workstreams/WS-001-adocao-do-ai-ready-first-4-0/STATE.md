---
id: WS-001
title: "Adocao do AI Ready First 4.0"
objective: "A GennomX AI opera sob AI Ready First 4.0.0 com AGENTS.md residente enxuto e validadores verdes"
status: active
created_at: "2026-08-21"
updated_at: "2026-08-21"
risk_level: 3
current_phase:
  vlaeg: not-applicable  # V | L | A | E | G | cross-cutting | not-applicable
active_plan: PLAN-002
active_tasks: [T-012]
agents:
  - harness: cursor
    session_id: "t207"
    last_seen: "2026-08-21T20:35:04Z"
branch: "ws-t207-ia-ready-4.0"
worktree: "C:/Users/marcu/Desktop/Projetos IA/worktrees-t207/gennomx-ai"
base_commit: "f4cd794f2e92bb96f2ab33c38825c57b396aa936"
current_commit: "f4cd794f2e92bb96f2ab33c38825c57b396aa936"
validated_commit: "f4cd794f2e92bb96f2ab33c38825c57b396aa936"
open_questions: []
risks: []
pending_gates: [G5, G13, G14]
last_handoff: null
---

# WS-001 — Adocao do AI Ready First 4.0

## Objetivo

A GennomX AI opera sob AI Ready First 4.0.0 com AGENTS.md residente enxuto e validadores verdes

## Fases VLAEG

| Fase | Estado | Observação |
|---|---|---|
| V — Visão | não aplicável | |
| L — Link | não aplicável | |
| A — Arquitetura | aplicável | |
| E — Estilo | não aplicável | |
| G — Gatilho | não aplicável | |

Estados: `aplicável` · `parcial` · `não aplicável` · `obrigatória por risco`.
Declarar `não aplicável` é resposta legítima — presumir não é.

## Tarefas

- [ ] T-012 — Instalar protocolo 4.0 e registrar estado local (PLAN-002) — `em andamento` por cli

## Skills selecionadas

```yaml
selected_skills:
  - name: writing-agents-md
    version: 1.0.0
    reason: AGENTS.md residente 4.0
    trigger: editar AGENTS.md
    expected_output: nucleo abaixo de 6000 caracteres
    mandatory: true
  - name: no-workarounds
    version: 1.0.0
    reason: nao silenciar validador
    trigger: correcao
    expected_output: finding onde o verde nao fecha
    mandatory: true
  - name: memory-privacy
    version: 1.0.0
    reason: ledger local
    trigger: EVENTS.jsonl
    expected_output: evento allowlisted
    mandatory: true
  - name: workstream-management
    version: 1.1.0
    reason: WS local da adocao
    trigger: nova linha de trabalho
    expected_output: STATE/EVIDENCE/EVENTS
    mandatory: true

skipped_skills:
  - name: cycle-review
    reason: RC desta WS fica para o fechamento; T-207 na raiz ainda nao pediu motor
    approved_by: pending-human
```

## Bloqueios

- Nenhum bloqueio tecnico local. Commit, RC e G14 aguardam o fundador.

## Riscos abertos

- Validador 4.0 em codigo/docs pre-existentes → finding, nao workaround

## Gates pendentes

- G5 — pendente desde a ativação
- G13 — pendente desde a ativação
- G14 — pendente desde a ativação

## Não validado

- 22 erros (13 ai-ready + 9 links) triados em F-006. Sem commit. G13/RC/G14.

Este bloco existe para não virar nota de rodapé. Vazio só quando de fato tudo foi provado.

## Digest das sessões

Resumo operacional curto. Histórico completo vive em `EVENTS.jsonl`; prova vive em `EVIDENCE.md`.

### 2026-08-21 — cursor-grok-4.6
- Feito: Kit 4.0.2 + bundle federado 1.0.0 + AGENTS/PROJECT/WS locais
- Pendente: commit, G13 no tip, RC, G14
- Proxima acao: revisar divergencias triadas e commitar se o fundador autorizar

## Ponteiros

- Plano ativo: `project_state/plans/PLAN-002-*.md`
- Decisões relacionadas: D-007
- Findings relacionados: F-006
- Evidência: `EVIDENCE.md`
- Ledger: `EVENTS.jsonl`
- Último handoff: `HANDOFF.md`
