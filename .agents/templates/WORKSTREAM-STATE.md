---
id: WS-NNN
title: ""
objective: ""            # uma frase verificável: o que estará verdadeiro ao terminar
status: proposed         # proposed | active | paused | blocked | completed | cancelled
created_at: ""           # AAAA-MM-DD
updated_at: ""
risk_level: 0            # 0-5, ver docs/ai-ready/risk-levels.md
current_phase:
  vlaeg: not-applicable  # V | L | A | E | G | cross-cutting | not-applicable
active_plan: null        # PLAN-NNN ou null
active_tasks: []         # [T-NNN]
agents:
  - harness: ""
    session_id: ""
    last_seen: ""        # AAAA-MM-DDTHH:MM:SSZ
branch: ""
worktree: ""
base_commit: ""
current_commit: ""
validated_commit: ""      # ponta da linhagem coberta; evidências podem citar ancestrais
open_questions: []
risks: []
pending_gates: []        # [G5, G13, G14, ...] — vazio é pré-condição para fechar
last_handoff: null
---

# WS-NNN — <título>

## Objetivo

<o que estará verdadeiro quando esta linha de trabalho terminar>

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

- [ ] T-NNN — <descrição> (PLAN-NNN | ad-hoc) — `aberta`
- [ ] T-NNN — <descrição> — `em andamento` por <executor>
- [x] T-NNN — <descrição> — `concluída` → evidência: EVIDENCE.md#<âncora>

Estados: `aberta` · `em andamento` · `bloqueada` · `parcial` · `concluída` · `cancelada`.

## Skills selecionadas

```yaml
selected_skills:
  - name: ""
    version: ""
    reason: ""
    trigger: ""
    expected_output: ""
    mandatory: true

skipped_skills:
  - name: ""
    reason: ""          # obrigatório quando um gatilho obrigatório disparou
    approved_by: ""
```

## Bloqueios

- <o que impede, quem ou o que destrava>

## Riscos abertos

- <risco → mitigação prevista>

## Gates pendentes

- G<NN> — <por que ainda não passou>

## Não validado

- <o que foi escrito e nunca rodou; suposição que ficou de pé>

Este bloco existe para não virar nota de rodapé. Vazio só quando de fato tudo foi provado.

## Digest das sessões

Resumo operacional curto. Histórico completo vive em `EVENTS.jsonl`; prova vive em `EVIDENCE.md`.

### AAAA-MM-DD — <agente>
- Feito:
- Pendente:
- Próxima ação:

## Ponteiros

- Plano ativo: `project_state/plans/PLAN-NNN-<slug>.md`
- Decisões relacionadas: D-NNN
- Findings relacionados: F-NNN
- Evidência: `EVIDENCE.md`
- Ledger: `EVENTS.jsonl`
- Último handoff: `HANDOFF.md`
