<!-- validate-links: illustrative-paths -->
<!-- Os caminhos citados em prosa descrevem a estrutura de destino num projeto que adota o
     protocolo, não o layout do repositório de origem. Links markdown continuam verificados. -->

# Guia para agentes de IA

Instruções determinísticas. Onde houver escolha, este documento diz qual tomar — ambiguidade custa
mais que rigidez.

---

## 1. Onde começar a leitura

**Sempre nesta ordem, e pare no passo 5:**

1. `AGENTS.md` — como se trabalha aqui.
2. `project_state/PROJECT.md` — objetivo, comandos de validação, regras críticas.
3. `project_state/WORKSTREAMS.md` — qual linha de trabalho está ativa.
4. `project_state/workstreams/<WS>/STATE.md` — tarefa atual, bloqueios, gates pendentes.
5. `project_state/workstreams/<WS>/HANDOFF.md` — **só se existir e o commit ainda casar**.

**Não leia**, nesta fase: `DECISIONS.md` inteiro · `FINDINGS.md` inteiro · todos os planos · o
ledger inteiro · `docs/` inteiro. Busque por ponteiro quando a tarefa exigir.

Se `AGENTS.md` não existir, o projeto não adotou o protocolo. **Não improvise a estrutura**:
diga isso e ofereça rodar o bootstrap.

## 2. Como descobrir a estrutura

| Pergunta | Comando ou caminho |
|---|---|
| O projeto é conforme? | `python tools/validate.py` |
| Quais skills existem? | `.agents/registry/local-skills.yaml` (índice; o corpo está em `.agents/skills/`) |
| Que skills devo carregar? | `.agents/registry/routing-rules.yaml` + `docs/ai-ready/skill-routing.md` |
| Que rito esta mudança exige? | `docs/ai-ready/risk-levels.md` |
| O que preciso provar para fechar? | `docs/ai-ready/quality-gates.md` |
| Este registro ainda vale? | `docs/ai-ready/state-currency.md` |

## 3. Como determinar a fonte canônica

Em conflito, nesta ordem:

1. **Código, configuração e schema atuais.** O código é o que o sistema **é**.
2. Requisitos aprovados → regras normativas → decisões ativas → evidências recentes → conhecimento consolidado → estado operacional → handoff → ledger → transcrição.

Entre dois documentos: **a camada mais alta vence**; dentro da mesma camada, **o mais recente
vence**. As camadas estão em `CANONICAL-STATE.md` §1.

## 4. Como interpretar e alocar identificadores

- `WS-NNN` linha de trabalho · `T-NNN` tarefa · `PLAN-NNN` plano · `D-NNN` decisão · `F-NNN` finding · `E-NNN` evidência (**local à workstream**) · `AUD-NNN` auditoria · `G-NN` gate · `K-NNN` conhecimento.
- **Nunca reutilize** um identificador, nem de item cancelado.
- **Nunca invente** um número: leia o campo `**Próximo ID:**` do índice correspondente, ou use a automação de alocação.
- Ao citar evidência de outra workstream, **prefixe**: `WS-004:E-051`.
- Identificador vindo de outro repositório leva namespace e **não** é resolvido contra o estado local.

## 5. Como registrar o que você fez

Toda alteração de arquivo produz **três** registros. Nenhum substitui o outro:

| Registro | O que vai | Como |
|---|---|---|
| `EVENTS.jsonl` | que aconteceu | **append** de uma linha JSON com os onze campos |
| `STATE.md` | onde o trabalho está agora | edição do frontmatter e da seção de tarefas |
| `EVIDENCE.md` | a prova | comando + saída verbatim + timestamp + commit |

O ledger é **append-only**. Se você errou uma linha já gravada, **não a edite**: grave um evento
novo que corrige, com o motivo.

## 6. Como evitar criar duplicidade

Antes de criar qualquer arquivo, pergunte: **algum artefato existente já é o dono desta
informação?**

| Você ia criar | Já existe |
|---|---|
| uma lista de tarefas | seção `## Tarefas` do `STATE.md` |
| um resumo de progresso | ledger + digest do `STATE.md` |
| um documento de decisão avulso | `DECISIONS.md` |
| uma cópia de skill "adaptada" | edite a skill na fonte canônica e atualize versão e hash |
| um arquivo de contexto para agente | `AGENTS.md` (residente) ou uma skill (sob demanda) |
| um `CONTEXT.md` / `TASKS.md` / `PROGRESS.md` global | **nada.** Isto é estado paralelo — proibido |

## 7. Como validar o próprio trabalho

```bash
python tools/validate.py
```

**Antes de dizer que terminou:**

- [ ] Todo critério de aceitação tem comando executado e saída registrada.
- [ ] `STATE.md`, ledger e evidência atualizados.
- [ ] O diff contém **apenas** o que a tarefa declarou.
- [ ] Nenhum segredo no diff.
- [ ] O que **não** foi validado está declarado — não omitido.
- [ ] Validador verde, ou o vermelho remanescente está explicado e não é seu.

Se um teste não rodou, escreva que não rodou. **"Deve funcionar" é falsificação de evidência.**

## 8. Como agir diante de inconsistência

1. **Não resolva em silêncio.**
2. Nomeie o conflito: qual arquivo diz o quê, com caminho e linha.
3. Avalie a evidência pela ordem de autoridade (§3).
4. Recomende qual versão prevalece, **com grau de confiança** (Alta / Média / Baixa).
5. Registre como finding se o achado vale além desta tarefa.
6. Se o código contradiz uma **decisão ativa**: **pare**. Registre o finding e proponha decisão substituta. Não alinhe nenhum dos dois lados sozinho.

## 9. O que você nunca edita diretamente

| Nunca | Por quê | O que fazer |
|---|---|---|
| Linha já gravada do ledger | append-only | grave um evento novo |
| Arquivo com banner de congelamento | é registro histórico | crie o registro novo; cite o antigo |
| Decisão de outra pessoa, para "atualizar" | decisão não é editada, é substituída | proponha decisão substituta |
| Evidência de outra tarefa | prova é datada e vinculada | produza a sua |
| Parecer de um revisor, para passar no validador | é falsificação | corrija o código, não o parecer |
| Bloco de aceite humano (G14) | agente nunca assina | peça a assinatura |
| `content_hash` do registro de skills, à mão | ele é derivado | regenere pelo comando |

## 10. O que regenerar depois de cada tipo de mudança

| Você mudou | Regenere / atualize |
|---|---|
| criou ou fechou workstream | linha no `WORKSTREAMS.md` (mesma passagem) |
| criou auditoria | linha no `AUDITS.md`, com o status espelhado |
| editou uma skill | `version` no frontmatter **e** `content_hash` no registro |
| mudou o status de decisão, finding, plano, workstream ou auditoria | evento `currency_change` com motivo |
| fechou uma tarefa | evidência apontada, checkbox, `active_tasks`, `pending_gates` |
| passou o commit vigente | `current_commit` e, se as evidências acompanham, `validated_commit` |
| implementou uma decisão | consolidação por ciclo no changelog |

## 11. Ao encerrar a sessão

Se sobrou trabalho aberto, **gere o handoff** — e ele só vale enquanto o commit registrado for o
commit vigente. Declare, sem otimismo:

- o que ficou **não validado**;
- as **tentativas que falharam** e por quê (é o que impede o próximo agente de repetir o beco);
- as **próximas ações** como ações, não intenções.

## 12. Regra final

Quando este guia e o comportamento do validador discordarem, **o validador vence** — ele é
executável, o guia é texto. Registre a divergência como finding e corrija o guia.
