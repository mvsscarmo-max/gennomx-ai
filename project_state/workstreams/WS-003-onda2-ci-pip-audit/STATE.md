---
id: WS-003
title: "Onda 2: CI verde apos pip-audit"
objective: "O origin/main tem Security Scan verde com aiohttp e cryptography acima das CVEs do run 32669664058"
status: active
created_at: "2026-09-01"
updated_at: "2026-09-02"
risk_level: 3
current_phase:
  vlaeg: G
active_plan: PLAN-004
active_tasks: [T-016]
agents:
  - id: cursor-grok-4.6
    harness: cursor
    session_id: "onda2-ci-2b"
    last_seen: "2026-09-02T02:42:00Z"
branch: "main"
worktree: "C:/Users/marcu/Desktop/Projetos IA/Criação de sites/New GennonX Claude 2.0/GennomX AI"
base_commit: "0185ccf83ae383b535ac440a2db1583fa2b06f89"
current_commit: "ac74e3e028727d0288922b66cb5f91fd8960b5d8"
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

- [x] T-014 — Pinos aiohttp/cryptography, push e CI (PLAN-004) — `concluída` → EVIDENCE.md#E-001
- [x] T-015 — Lock overlay 1.1.0 em bytes LF + CI protocol (ad-hoc 2B.1) — `concluída` → run 33583382886 Protocol overlay success
- [ ] T-016 — npm audit e mypy/numpy no runner 3.12 (ad-hoc 2B.2) — `em andamento` → EVIDENCE.md#E-003

## Skills selecionadas

```yaml
selected_skills:
  - name: no-workarounds
    version: 1.0.0
    reason: causa raiz do npm ci e do mypy aclose, nao silenciar jobs
    trigger: corrigir codigo
    mandatory: true
  - name: deslop
    version: 1.0.0
    reason: commit de T-016
    trigger: commitar
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

- Frontend lint e backend lint no GitHub após este SHA (run `33583382886` falhou nesses dois; protocol e Security Scan já verdes).
- G13 / RC / G14.

## Digest

### 2026-09-02 — cursor-grok-4.6
- Feito: T-015 verde no Linux (Protocol overlay). T-016 local: override `browserslist@4.28.7` removido e lock com a árvore real; `types-redis` 4 removido para o `py.typed` do redis 6. mypy 138/0; `npx npm@10.8.2 ci` 0; audit 0.
- Pendente: push; jobs lint no GitHub; G13/RC/G14. F-069 da raiz permanece aberto.
- Proxima acao: push e conferir frontend-lint e backend-lint.

### 2026-09-01 — cursor-grok-4.6
- Feito: piso aiohttp 3.14.3 e cryptography 50.0.1.
- Pendente: commit, push, CI.
- Proxima acao: push e conferir Security Scan.

## Ponteiros

- Plano: PLAN-004 · Evidencia: EVIDENCE.md · Ledger: EVENTS.jsonl
