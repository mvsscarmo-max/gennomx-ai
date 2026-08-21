---
workstream_id: WS-NNN
source_agent: ""          # harness/modelo que gerou
target_agent: ""          # "qualquer" quando não há destinatário definido
created_at: ""            # AAAA-MM-DDTHH:MM:SSZ
branch: ""
worktree: ""
commit: ""                # obrigatório; "none" só em projeto sem Git, e isso fica declarado
objective: ""
current_state: ""         # uma frase: onde o trabalho parou
completed: []             # SOMENTE itens com evidência apontada
modified_files: []
decisions: []             # D-NNN
findings: []              # F-NNN
failed_attempts: []       # o que foi tentado e não funcionou — impede repetir o beco
tests_executed: []
tests_passed: []
tests_failed: []
not_validated: []         # escrito e nunca rodado; suposição de pé
open_questions: []
risks: []
next_actions: []          # ações, não intenções
pending_gates: []
context_pointers: []      # caminhos, nunca conteúdo
---

# Handoff — WS-NNN

## Estado atual

<uma frase: onde o trabalho parou e por quê>

## Concluído com evidência

| Item | Evidência |
|---|---|
| | `EVIDENCE.md#<âncora>` |

Item sem evidência apontada **não entra aqui** — vai para "Não validado".

## Tentativas que falharam

| O que foi tentado | Por que não funcionou | Vale tentar de novo? |
|---|---|---|

## Não validado

- <o que foi escrito e nunca rodou>
- <teste que não foi executado>
- <suposição que ficou de pé>

Vazio só quando tudo foi de fato provado. Vazio por otimismo é o defeito que este bloco existe
para impedir.

## Próximas ações

1. <ação concreta: "rodar X e corrigir Y">

## Gates pendentes

- G<NN> — <o que falta>

## Ponteiros de contexto

- `project_state/workstreams/WS-NNN/STATE.md`
- `project_state/workstreams/WS-NNN/EVIDENCE.md`
- `project_state/plans/PLAN-NNN-<slug>.md`

---

**Validade:** este handoff é atual somente enquanto `commit` for igual a `current_commit` no
`STATE.md` vigente. Commit apenas ancestral indica proveniência histórica, não atualidade —
revalide antes de agir.
Verificado pelo validador de estado.
