---
id: WS-001
title: "Adocao do AI Ready First 4.0"
objective: "A GennomX AI opera sob AI Ready First 4.0.0 com AGENTS.md residente enxuto e validadores verdes"
status: completed
created_at: "2026-08-21"
updated_at: "2026-08-21"
risk_level: 3
current_phase:
  vlaeg: not-applicable  # V | L | A | E | G | cross-cutting | not-applicable
active_plan: PLAN-002
active_tasks: []
agents:
  - harness: cursor
    session_id: "t207"
    last_seen: "2026-08-21T23:48:00Z"
branch: "ws-t207-ia-ready-4.0"
worktree: "C:/Users/marcu/Desktop/Projetos IA/worktrees-t207/gennomx-ai"
base_commit: "f4cd794f2e92bb96f2ab33c38825c57b396aa936"
current_commit: "83fa67bf0f57e3bf413920d50ef19afc2019aa46"
validated_commit: "83fa67bf0f57e3bf413920d50ef19afc2019aa46"
open_questions: []
risks: []
pending_gates: []
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

- [x] T-012 — Instalar protocolo 4.0 e registrar estado local (PLAN-002) — `concluída` → EVIDENCE.md#E-006

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

  - name: cycle-review
    version: 1.0.0
    reason: risco 3 — RC + G14 no fechamento
    trigger: fechamento
    expected_output: AUD-001
    mandatory: true

  - name: deslop
    version: 1.0.0
    reason: fechamento de tarefa de codigo
    trigger: commit
    expected_output: G5
    mandatory: true

skipped_skills: []
```

## Bloqueios

- Nenhum.

## Riscos abertos

- Nenhum aberto nesta WS. F-006 (sandbox historico, credential-pair e links) foi endereçado no tip.

## Gates pendentes

- NENHUM

## Não validado

- Fast-forward de `main` após este fechamento.
- `python federation/protocol/core/protocol.py verify` — bundle-drift (`tests/test_protocol.py` ausente).

## Digest das sessões

Resumo operacional curto. Histórico completo vive em `EVENTS.jsonl`; prova vive em `EVIDENCE.md`.

### 2026-08-21 — cursor-grok-4.6
- Feito: Kit 4.0.2, validadores verdes, RC AUD-001 (GPT 5.6 SOL), correção R-01…R-04, G14
- Pendente: FF de `main`
- Proxima acao: nenhuma nesta WS

## Ponteiros

- Plano ativo: `project_state/plans/PLAN-002-*.md`
- Decisões relacionadas: D-007
- Findings relacionados: F-006
- Evidência: `EVIDENCE.md`
- Ledger: `EVENTS.jsonl`
- Último handoff: `HANDOFF.md`
