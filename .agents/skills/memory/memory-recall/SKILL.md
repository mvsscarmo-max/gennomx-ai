---
name: memory-recall
description: Monta o briefing inicial dentro do orçamento e entrega o delta desde a última participação deste agente, mais busca dirigida no histórico. Use ao iniciar sessão numa workstream existente, ao precisar saber se um caminho já foi tentado, e antes de investigar um problema que pode já estar mapeado. Não use para carregar histórico completo, nem para tratar registro antigo como verdade atual.
metadata:
  protocol: VLAEG AI Ready First
  layer: memory
  version: 1.0.0
  source: "conceitos de briefing, delta e ledger pesquisável de akitaonrails.com/2026/07/20, sem sandbox"
  adapted: true
  risk: low
  vlaeg_phases: [cross-cutting]
  triggers:
    - "iniciar sessão em workstream existente"
    - "verificar se um caminho já foi tentado"
    - "antes de investigar problema possivelmente mapeado"
  negative_triggers:
    - "carregar histórico completo"
    - "tratar registro do ledger como regra vigente"
  produces: ["briefing dentro do orçamento", "delta", "referências de busca"]
  gates: ["G8"]
---

# Recuperar memória

Contexto bruto demais é caro, ruidoso e recria exatamente o problema que a memória do projeto
deveria resolver. O agente recebe **briefing limitado + delta + ponteiros**, e busca o resto quando
a tarefa exigir.

## Briefing

Monte a partir destas fontes, nesta ordem, parando ao atingir o orçamento de
`.agents/policy/context-budget.yaml` (padrão 6.000 caracteres):

| Ordem | Conteúdo | Fonte | Cortável |
|---|---|---|---|
| 1 | Objetivo do projeto e regras críticas | `PROJECT.md` | não |
| 2 | Workstream ativa e objetivo | `WORKSTREAMS.md`, `STATE.md` | não |
| 3 | Tarefa atual e bloqueios | `STATE.md` | não |
| 4 | Gates pendentes | `STATE.md` | não |
| 5 | Referência ao último handoff | `HANDOFF.md` | sim |
| 6 | Decisões **relacionadas à tarefa** | `DECISIONS.md` | sim |
| 7 | Riscos abertos | `STATE.md` | sim |
| 8 | Ponteiros de busca | esta skill | sim |

Nunca entra no briefing: transcrição, ledger inteiro, todos os planos, todas as decisões, todas as
skills, workstream encerrada, decisão substituída, conhecimento alheio à tarefa.

*Concluído quando:* o briefing cabe no orçamento e contém os quatro itens não cortáveis.

## Delta

O delta é o que aconteceu **desde a última participação deste agente nesta workstream** — não desde
o começo.

1. Leia `last_seen` do agente atual em `STATE.md` § `agents`. Ausente → é a primeira participação: entregue os 10 eventos mais recentes, não o histórico.
2. Filtre `EVENTS.jsonl` por `ts > last_seen`.
3. Se o resultado passar do teto de delta (padrão 4.000 caracteres), entregue os mais recentes, a **contagem do que ficou de fora** e um ponteiro de busca. Truncar em silêncio é pior que truncar declarando.
4. Atualize `last_seen`.

*Concluído quando:* o delta foi entregue dentro do teto, com a contagem do omitido, e `last_seen` está atualizado.

## Busca

Quando a tarefa precisa de mais do que briefing e delta trazem:

```bash
rg -n "termo" project_state/workstreams/*/EVENTS.jsonl
rg -n "termo" project_state/FINDINGS.md project_state/DECISIONS.md
rg -n "termo" project_state/knowledge/ docs/gotchas/
```

Perguntas que a busca responde bem: *já tentamos isto?* · *por que desistimos daquilo?* ·
*esta limitação já está mapeada?* · *que decisão cobre esta área?*

**Escopo padrão: este projeto.** Busca entre projetos é `false` em
`.agents/policy/context-budget.yaml` e só liga com decisão registrada, justificativa, lista
explícita de projetos e data de revisão.

*Concluído quando:* a pergunta foi respondida ou se confirmou que o histórico não a cobre — e a segunda resposta também é um resultado válido, que evita reinvestigação.

## O que a memória prova

Um resultado de busca prova que algo foi **dito, tentado, observado, executado ou registrado**
naquele commit. Não prova que continua correto.

Antes de agir sobre um achado antigo:

1. Compare o `commit` do evento com o `HEAD`.
2. Diferente → o achado é `historical`. Revalide antes de decidir.
3. Trate o código atual como autoridade máxima (`authority-model.md`).

Um caminho descartado há três meses pode ter voltado a ser viável. Um teste que passava pode ter
quebrado. O ledger registra a tentativa, não a verdade.

## Tratamento de falhas

- **`EVENTS.jsonl` com linha inválida:** pule a linha, registre `F-NNN` com o número dela e siga. Uma linha corrompida não invalida o ledger.
- **Sem `last_seen` e ledger enorme:** entregue os 10 eventos mais recentes e o ponteiro de busca. Nunca despeje tudo por não saber por onde começar.
- **Briefing estoura o orçamento mesmo cortando tudo que é cortável:** o `STATE.md` está inchado — ele guarda histórico que pertence ao ledger. Registre e proponha a limpeza.

## Anti-patterns

Colar o ledger no prompt · tratar handoff antigo como estado atual · buscar entre projetos por
padrão · truncar sem declarar · promover achado de busca a regra sem passar por `knowledge-promotion`.
