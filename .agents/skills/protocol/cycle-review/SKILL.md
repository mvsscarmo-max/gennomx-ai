---
name: cycle-review
description: Conduz a Revisão de Ciclo — G13 diferencial, uma rodada de julgamento por workstream (RC) e aceite humano G14 — com prompt gerado, revisor independente e artefato de auditoria AUD-NNN. Use em risco maior ou igual a 3 antes do fechamento, ou quando o responsável humano pedir revisão de ciclo. Não use durante edição ativa, com diff vazio, nem como substituto de G13 sozinho em risco 2.
metadata:
  protocol: VLAEG IA-ready
  layer: protocol
  version: 1.0.0
  source: local
  adapted: true
  risk: medium
  vlaeg_phases: [G, cross-cutting]
  triggers:
    - "nível de risco >= 3 antes do fechamento da workstream"
    - "pedido explícito de Revisão de Ciclo"
  negative_triggers:
    - "edição ainda em andamento"
    - "diff vazio"
    - "só G13 em risco 2 (rode o verificador diferencial sozinho)"
    - "auditar QA de produto (use qa-execution)"
  produces: ["AUD-NNN-<slug>.md", "bloco G13/G14 em EVIDENCE.md", "F-NNN por achado"]
  gates: ["G13", "G14"]
---

# Revisão de Ciclo

Três camadas, cada uma no preço do que verifica:

| Camada | Mecanismo | Quando |
|---|---|---|
| Mecânica | **G13** — verificador diferencial | risco ≥ 2 |
| Julgamento | **RC** — uma invocação de revisor | risco ≥ 3, uma vez por workstream |
| Autoridade | **G14** — aceite humano assinado | risco ≥ 3 |

Norma: `docs/ai-ready/cycle-review.md` — leia integralmente na primeira RC da tarefa.
Template do prompt: `references/rc-prompt.md` — **não redija à mão**.

## Procedimento

**Passo 0 — Pré-voo.** Gate verde **agora** (validador do protocolo e G13, quando aplicável).
Diff não vazio, sem marcador de trabalho em andamento, sem artefato local. Marcador falho →
**aborte e reporte qual falhou**. Não invoque revisor.

*Concluído quando:* os seis itens do pré-voo passam.

**Passo 1 — G13.** Rode o verificador diferencial da janela `base_commit..HEAD` e registre a saída
em `EVIDENCE.md` com o gate marcado. Corrija todo detector vermelho **antes** da RC.

G13 é **recomputável**: se o tip andar, rode de novo. A lista de detectores cresce por finding,
nunca por antecipação.

*Concluído quando:* G13 verde no tip, com bloco no `EVIDENCE.md`.

**Passo 2 — Prompt da RC.** Gerado, nunca manuscrito. O gerador embute as saídas de G13 e do
validador, **já assinadas**, monta o prompt a partir de `references/rc-prompt.md` e nomeia a
auditoria de destino. Pré-voo falho **não abre rodada**.

Embutir as saídas assinadas é o que impede o revisor de reexecutar o validador — reexecução gasta
tempo do revisor com o que já está provado e abre espaço para divergência entre duas execuções.

*Concluído quando:* o prompt existe, com as duas seções e as saídas embutidas.

**Passo 3 — Executar.** Primeiro revisor disponível e **independente do autor** na escada declarada
pelo projeto. O revisor escreve **apenas** o arquivo de auditoria. Saída diferente de zero ou
artefato ausente → classifique como falha de infraestrutura; **não trate a saída bruta como
parecer**. Processo pendurado além do limite de inatividade conta uma tentativa de infraestrutura.

**Invariante:** uma rodada de **julgamento** por workstream. Não existe rodada 2. Tentativa de
**invocação** que falhou por infraestrutura ainda tem orçamento.

*Concluído quando:* a auditoria existe, ou a falha de infraestrutura foi registrada.

**Passo 4 — Triagem.** Cada achado recebe identificador local `R-NN`, severidade e tipo.

| Classe | Ação |
|---|---|
| `critico` · `prova-obrigatoria` | corrigir nesta workstream; **G13** verifica; nunca aceite por decisão |
| `contrato` | corrigir nesta workstream, ou decisão registrada com prazo |
| demais | ressalva → finding + plano/tarefa da workstream seguinte |

Pergunte o que incorporar antes de editar. Commit só por instrução explícita.

*Concluído quando:* todo `R-NN` tem destino, e os críticos foram verificados por G13.

**Passo 5 — G14.** O responsável humano assina o bloco em `EVIDENCE.md`: leu resumo do diff, G13 e
a RC; aceita ou nomeia findings com prazo. **Agente nunca assina.**

Sem revisor disponível após esgotar o orçamento de infraestrutura: G14 + decisão registrada + prazo
destrava **só a ausência de revisor** — nunca um achado crítico já produzido.

*Concluído quando:* o bloco G14 assinado por humano está no `EVIDENCE.md`.

## Independência

Autor e revisor: modelos distintos. Mesmo ambiente, apenas em processo separado — **nunca
subagente**, que herda o contexto e o viés de quem escreveu o código. Sem execução irrestrita e sem
os mecanismos de isolamento excluídos por norma.

## Tratamento de falhas

- **Nenhum revisor independente:** registre RC pendente, abra decisão com prazo, humano assina G14. **Não use o autor como revisor.**
- **Falha de infraestrutura:** esgote o orçamento no degrau; troque uma vez para o degrau seguinte, se houver; depois escape por G14.
- **Achado crítico na RC:** corrija e rode G13 — nunca peça segunda rodada de revisor.
- **G13 vermelho no pré-voo:** corrija antes de gastar a invocação.

## Anti-patterns

Redigir prompt à mão · segunda rodada de julgamento · tratar saída bruta como auditoria ·
reexecutar o validador dentro do revisor · agente assinar G14 · destravar achado crítico por
decisão · editar o parecer do revisor para passar no validador · reabrir gates aposentados.
