---
name: workstream-management
description: Cria, retoma, pausa, bloqueia e fecha workstreams — a unidade persistente de continuidade que liga solicitação, plano, tarefa, sessão, evidência e conclusão. Use ao iniciar uma linha de trabalho nova, voltar a uma existente, abrir investigação paralela sem contaminar o trabalho principal, ou encerrar com os gates verdes. Não use para consulta pontual sem trabalho associado, nem para gerar handoff (use session-handoff).
metadata:
  protocol: VLAEG AI Ready First
  layer: memory
  version: 1.1.0
  source: "conceitos de workstream de akitaonrails.com/2026/07/20 (ai-memory 1.17.1)"
  adapted: true
  risk: low
  vlaeg_phases: [cross-cutting]
  triggers:
    - "iniciar linha de trabalho nova"
    - "retomar workstream existente"
    - "abrir investigação paralela isolada"
    - "pausar, bloquear ou fechar workstream"
  negative_triggers:
    - "consulta pontual sem trabalho associado"
    - "gerar handoff (use session-handoff)"
    - "buscar histórico (use memory-recall)"
  produces: ["workstreams/WS-NNN/STATE.md", "linha em WORKSTREAMS.md", "eventos status_change"]
  gates: ["G7", "G8"]
---

# Gerenciar workstreams

A workstream é a linha de trabalho que sobrevive à sessão, ao agente e ao harness. Ela existe
porque o código guarda o que venceu e a sessão guarda por quê — e a sessão pertence ao harness,
que pode mudar amanhã.

Uma workstream por linha de trabalho independente. Investigação paralela ganha a sua, em vez de
contaminar a principal.

## Ramos

| Situação | Vá para |
|---|---|
| Nenhuma workstream ativa e há trabalho a fazer | **Criar** |
| Existe workstream ativa para este trabalho | **Retomar** |
| Encerrando com trabalho aberto | **Pausar** |
| Dependência externa impede seguir | **Bloquear** |
| Gates verdes e objetivo atingido | **Fechar** |

## Criar

1. Determine o próximo `WS-NNN` lendo `project_state/WORKSTREAMS.md`. **IDs nunca são reutilizados**, mesmo os de workstreams canceladas.
2. Crie `project_state/workstreams/WS-NNN-<slug>/` com `STATE.md` a partir de `.agents/templates/WORKSTREAM-STATE.md`, mais `EVENTS.jsonl` e `EVIDENCE.md` vazios. O estado inicial padrão é `proposed`.
3. Preencha `objective` numa frase verificável — "o que estará verdadeiro quando isto terminar". Objetivo vago produz fechamento vago.
4. Classifique o nível de risco por `docs/ai-ready/risk-levels.md` e registre-o. Na dúvida entre dois níveis, suba.
5. Registre `branch`, `worktree` e `base_commit`. Sem Git, use `none` — o protocolo opera degradado, mas a ausência fica declarada.
6. Para ativar no mesmo passo, exija tarefa inicial; em risco ≥ 2, exija também um `PLAN-NNN` existente. Sem esses vínculos, mantenha `proposed`.
7. Acrescente a linha na seção correspondente de `WORKSTREAMS.md` e grave o evento `status_change`.

*Concluído quando:* `STATE.md` existe com objetivo verificável e nível de risco, a linha está no índice e o evento foi gravado.

Bootstrap **mutante**: `python tools/new_workstream.py --title "..." --objective "..." --risk N`
cria `proposed`. Para criar `active`, acrescente `--status active --task "..." --plan PLAN-NNN`;
risco 0–1 pode omitir `--plan`.

## Retomar

1. Leia `STATE.md`.
2. Compare `current_commit` com o `HEAD` atual. Divergiu? O estado descreve outro ponto da história — trate handoff e evidência como `historical` até revalidar.
3. Obtenha o delta pela skill `memory-recall`, não lendo o ledger inteiro.
4. Verifique `agents`: outro executor com `last_seen` de menos de 30 minutos significa trabalho concorrente. Registre o conflito em `open_questions` em vez de escrever por cima — a detecção é cooperativa, não um lock, e esta limitação é declarada.
5. Registre-se em `agents` com harness, sessão e `last_seen`.

*Concluído quando:* o agente está registrado, o delta foi recebido e qualquer divergência de commit está anotada.

## Pausar

1. **Gere o handoff** (`session-handoff`) — pausa sem handoff é perda de contexto disfarçada de organização.
2. Atualize `status: paused`, `current_commit` e `pending_gates`.
3. Registre em `## Não validado` tudo que ficou sem prova.
4. Grave o evento `status_change`.

*Concluído quando:* handoff existe, gates pendentes estão listados e o não validado está explícito.

## Bloquear

1. `status: blocked` com a causa em `open_questions` ou `pending_gates` — bloqueio sem causa nomeada é abandono.
2. Registre quem ou o que destrava.
3. Gere handoff, como na pausa.

*Concluído quando:* a causa e o destravador estão nomeados.

## Fechar

1. Verifique `pending_gates` vazio. Não vazio → não feche; a workstream está `paused` ou `blocked`.
2. Confirme os gates do nível de risco em `docs/ai-ready/quality-gates.md`, cada um com evidência apontada em `EVIDENCE.md`.
3. Proponha o conhecimento que sobreviveu via `knowledge-promotion`.
4. `status: completed`, atualize `WORKSTREAMS.md`, grave o evento.
5. O diretório **permanece** no repositório. Fechado não é apagado.

*Concluído quando:* gates verdes com evidência, conhecimento proposto e índice atualizado.

## Isolamento

Uma workstream não lê o estado de outra sem referência explícita registrada em `STATE.md`.
Investigação paralela existe justamente para não misturar as duas linhas — misturá-las devolve o
problema que a separação resolve.

## Tratamento de falhas

- **`STATE.md` divergente do repositório real:** o código vence (`authority-model.md`). Corrija o `STATE.md` e registre `F-NNN`.
- **Workstream órfã** (diretório sem linha no índice, ou linha sem diretório): `tools/validate_state.py` acusa; reconcilie antes de qualquer outro trabalho.
- **Duas workstreams para o mesmo trabalho:** feche a mais nova como `cancelled` com motivo e continue na original. Nunca funda IDs.

## Anti-patterns

Workstream sem objetivo verificável · fechar com gate pendente · reutilizar ID · apagar diretório
de workstream fechada · usar uma workstream como caderno de várias linhas de trabalho · deixar
`last_seen` desatualizado.
