---
id: WS-003
title: "Onda 2: CI verde apos pip-audit"
objective: "O origin/main tem Security Scan verde com aiohttp e cryptography acima das CVEs do run 32669664058"
status: active
created_at: "2026-09-01"
updated_at: "2026-09-01"
risk_level: 3
current_phase:
  vlaeg: G
active_plan: PLAN-004
active_tasks: [T-014]
agents:
  - id: cursor-grok-4.6
    harness: cursor
    session_id: "onda2-local"
    last_seen: "2026-09-01T06:20:00Z"
branch: "main"
worktree: "C:/Users/marcu/Desktop/Projetos IA/Criação de sites/New GennonX Claude 2.0/GennomX AI"
base_commit: "0185ccf83ae383b535ac440a2db1583fa2b06f89"
current_commit: "0185ccf83ae383b535ac440a2db1583fa2b06f89"
validated_commit: "0185ccf83ae383b535ac440a2db1583fa2b06f89"
open_questions: []
risks:
  - "pip-audit local no Windows falhou por encoding do pip --version; a prova e o run Linux no GitHub"
pending_gates: [G5, G13, G14]
last_handoff: null
---

# WS-003 — Onda 2: CI verde apos pip-audit

## Objetivo

O `origin/main` tem o job Security Scan verde com `aiohttp` e `cryptography` acima das CVEs do run `32669664058`.

## Fases VLAEG

| Fase | Estado | Observação |
|---|---|---|
| V — Visão | não aplicável | Onda 2 PLAN-027 |
| L — Link | não aplicável | |
| A — Arquitetura | aplicável | piso de dependência |
| E — Estilo | não aplicável | |
| G — Gatilho | obrigatória por risco | G13/RC/G14 no fechamento |

## Tarefas

- [ ] T-014 — Pinos aiohttp/cryptography, push e CI (PLAN-004) — `em andamento`

## Skills selecionadas

```yaml
selected_skills:
  - name: no-workarounds
    version: 1.0.0
    reason: causa raiz e o pino velho, nao silenciar pip-audit
    trigger: corrigir codigo
    mandatory: true
  - name: memory-privacy
    version: 1.0.0
    reason: ledger sem segredo
    trigger: EVENTS.jsonl
    mandatory: true
  - name: workstream-management
    version: 1.1.0
    reason: linha local da Onda 2
    trigger: nova workstream
    mandatory: true
skipped_skills:
  - name: cycle-review
    reason: RC no fechamento; D-008 cobre motor ausente desta fatia de CI
    approved_by: protocolo (gate de fechamento)
```

## Bloqueios

_nenhum_

## Riscos abertos

- Prova local de pip-audit no Windows quebra no decode do `pip --version`; CI Linux e a autoridade.

## Gates pendentes

- G5 / G13 / G14 — fechamento

## Não validado

- Run GitHub do SHA ainda nao empurrado.

## Digest

### 2026-09-01 — cursor-grok-4.6
- Feito: piso aiohttp 3.14.3 e cryptography 50.0.1.
- Pendente: commit, push, CI.
- Proxima acao: push e conferir Security Scan.

## Ponteiros

- Plano: PLAN-004 · Evidencia: EVIDENCE.md · Ledger: EVENTS.jsonl
