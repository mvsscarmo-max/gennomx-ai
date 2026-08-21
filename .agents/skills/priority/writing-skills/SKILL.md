---
name: writing-skills
description: Autora, refatora e depura agent skills. Use ao criar uma skill do zero, podar ou reestruturar um SKILL.md inchado, apertar os gatilhos de uma descrição, ou diagnosticar referências que o agente ignora. Não use para arquivos de instrução residentes como AGENTS.md ou CLAUDE.md (use writing-agents-md), nem para documentação humana.
metadata:
  protocol: VLAEG AI Ready First
  layer: priority
  version: 1.0.0
  source: pedronauck/skills@ffc7c18540fd41b3030b29c0b61a494de3d20d49/skills/mine/writing-skills
  video_evidence: "ohzc4p7-QHQ 04:26 — grupo GUIAS"
  adapted: true
  risk: medium
  vlaeg_phases: [A]
  triggers:
    - "criar uma skill nova"
    - "refatorar SKILL.md inchado ou com gatilho fraco"
    - "diagnosticar skill cujas referências o agente ignora"
  negative_triggers:
    - "editar AGENTS.md ou CLAUDE.md (use writing-agents-md)"
    - "escrever README ou documentação para humanos"
  produces: ["SKILL.md", "auditoria escrita item a item", "entrada em local-skills.yaml"]
  gates: ["G6", "G7", "G10"]
---

# Escrever skills

Uma skill existe para arrancar determinismo de um sistema estocástico. **Previsibilidade** — o
agente seguir o mesmo *processo* toda vez, não produzir a mesma saída — é a virtude raiz; toda
alavanca abaixo serve a ela.

## Ramos

| Quando você está… | Faça |
|---|---|
| Criando uma skill do zero | Leia `references/authoring-procedure.md` **integralmente** primeiro — mecânica da spec, layout de diretório, validação de metadados. Depois aplique a doutrina abaixo a cada linha escrita. |
| Melhorando uma skill existente (inchaço, deriva, gatilho fraco) | Aplique a doutrina abaixo, seção por seção, até toda regra pertinente ter sido aplicada. |
| Diagnosticando skill cujas referências o agente ignora | Leia `references/loading-diagnosis.md` **integralmente** antes de propor qualquer correção. |

Todo ramo termina igual: uma auditoria escrita, item a item, contra `references/checklist.md`.
Marque cada item como Passa ou Falha, corrija toda Falha e reaudite. Skill que lê bem e falha na
auditoria não está pronta.

## Invocação

Duas escolhas, com custos diferentes:

- **Invocada por modelo** — mantém `description`, então o agente dispara sozinho e outras skills alcançam a skill. Paga **carga de contexto**: a descrição fica na janela a cada turno.
- **Invocada por usuário** — tira a descrição do alcance do agente. Carga de contexto zero, mas gasta **carga cognitiva**: *você* vira o índice que precisa lembrar que ela existe. Mecânica: `disable-model-invocation: true`.

Escolha invocação por modelo só quando o agente (ou outra skill) precisa alcançá-la sozinho.

Neste protocolo, toda skill local é invocada por modelo e tem gatilho declarado em
`.agents/registry/routing-rules.yaml` — o roteador é o índice, não a memória de quem digita.

## Escrevendo a descrição

A descrição faz dois trabalhos: dizer o que a skill é e listar os **ramos** que devem dispará-la.
Cada palavra aumenta a carga de contexto, então ela merece poda mais dura que o corpo:

- **Coloque a palavra-âncora na frente** — é ali que ela faz o trabalho de invocação.
- **Um gatilho por ramo.** Sinônimos que renomeiam um único ramo são duplicação. Colapse-os.
- **Corte identidade que já está no corpo.** Descrição é gatilho, mais a cláusula de alcance quando outra skill precisa chamá-la.
- Inclua gatilhos negativos ("Não use para…"): eles evitam a seleção por semelhança de nome, que este protocolo proíbe.

## Hierarquia de informação

Uma skill é feita de dois tipos de conteúdo — **passos** e **referência** — que se misturam
livremente. A decisão central é onde cada um fica na escada:

1. **Passo no SKILL.md** — ação ordenada, o degrau primário. Cada passo termina num **critério de conclusão** *verificável* (dá para saber pronto de não-pronto?) e, quando importa, *exaustivo* ("toda tabela alterada contabilizada", não "produza uma lista"). Critério vago convida à conclusão prematura.
2. **Referência no SKILL.md** — definição, regra ou fato consultado sob demanda. Um conjunto plano de regras pares é uma forma legítima, não um defeito.
3. **Referência externa** — empurrada para arquivo separado, alcançada por **ponteiro de contexto**, carregada só quando o ponteiro dispara.

Empurre pouco demais e o topo incha; empurre demais e você esconde o que o agente precisa. Essa
tensão é a decisão inteira.

**Carregamento progressivo** é o movimento escada abaixo. O melhor teste é o **ramo**: deixe inline
o que todo ramo precisa e empurre para trás de um ponteiro o que só alguns alcançam. É a *redação*
do ponteiro, não o alvo, que decide se e quando o agente carrega o arquivo — ponteiro que deve
disparar diz "leia integralmente".

**Co-locação** decide o que fica ao lado: definição, regras e ressalvas de um conceito sob um mesmo
título, para que ler uma parte traga as vizinhas.

## Quando dividir

Cada corte gasta uma das duas cargas, então só divida quando o corte se paga:

- **Por invocação** — separe quando há uma palavra-âncora distinta que deve disparar sozinha, ou quando outra skill precisa alcançá-la. Você paga carga de contexto pela nova descrição.
- **Por sequência** — separe uma sequência de passos quando os passos à frente tentam o agente a apressar o que está na frente. Tirá-los de vista aumenta o trabalho investigativo no passo atual.

## Poda

Mantenha cada significado numa **fonte única**: mudar o comportamento deve ser uma edição em um
lugar só.

Cheque **relevância** linha a linha: isso ainda diz respeito ao que a skill faz?

Depois cace **no-ops** frase a frase, não linha a linha: aplique o teste em cada frase isolada —
"isso muda o comportamento em relação ao default?" — e, quando falhar, apague a frase inteira em vez
de aparar palavras. Seja agressivo: a maior parte da prosa que falha deve sair, não ser reescrita.

## Palavras-âncora

Uma **palavra-âncora** é um conceito compacto que já vive no pré-treino e com o qual o agente
pensa enquanto roda a skill (*lição*, *névoa de guerra*, *bala traçante*). Repetida ao longo do
texto, ela acumula uma definição distribuída e ancora uma região inteira de comportamento com
pouquíssimos tokens.

Ela serve à previsibilidade duas vezes: no corpo ancora **execução**; na descrição ancora
**invocação** — quando a mesma palavra vive nos seus prompts, docs e código, o agente liga essa
linguagem à skill e a dispara com mais confiabilidade.

Exemplos de colapso: "rápido, determinístico, de baixo overhead" → *enxuto*; "um loop em que você
acredita" → *vermelho* (o loop fica vermelho no bug, ou não fica).

## Modos de falha

- **Conclusão prematura** — encerrar um passo antes de estar de fato pronto. Defesa, nesta ordem: afie o critério de conclusão; só se ele for irredutivelmente vago *e* você observar a pressa, esconda os passos seguintes dividindo.
- **Duplicação** — o mesmo significado em mais de um lugar. Custa manutenção e tokens, e infla a proeminência do significado além do posto real.
- **Sedimento** — camadas obsoletas que se acumulam porque acrescentar parece seguro e remover parece arriscado. Destino padrão de toda skill sem disciplina de poda.
- **Sprawl** — skill longa demais mesmo com toda linha viva e única. A cura é a escada.
- **No-op** — linha que o modelo já obedece por default; você paga carga para não dizer nada.
- **Negação** — dirigir por proibição sai pela culatra: *não pense num elefante* nomeia o elefante. Enuncie o alvo positivo; guarde a proibição só como guardrail duro, sempre com o que fazer no lugar.

## Contrato mínimo das skills deste protocolo

Além da spec, toda skill local declara em `metadata`: `protocol`, `layer`, `version`, `source`
(quando adaptada), `risk`, `vlaeg_phases`, `triggers`, `negative_triggers`, `produces` e `gates`.
Validado por `python tools/validate_skills.py` — frontmatter incompatível reprova o repositório.

O corpo cobre, conforme aplicável: objetivo, quando usar, quando não usar, gatilhos, pré-condições,
entradas, procedimento, artefatos, gates obrigatórios, evidências, tratamento de falhas,
dependências, skills relacionadas, critérios de conclusão, anti-patterns.

## Arquivos empacotados

- `references/authoring-procedure.md` — mecânica da spec para o ramo criar: metadados, layout, convenções de script, validação.
- `references/checklist.md` — auditoria de saída dos ramos criar e melhorar: doutrina (Parte A) e conformidade de spec (Parte B), item a item.
- `references/loading-diagnosis.md` — ramo diagnosticar: sintomas de referência ignorada, escada de força do ponteiro, correções em ordem.
- `scripts/validate_metadata.py` — auxiliar **somente leitura**; valida `name`/`description`/`metadata` contra a spec e contra o contrato deste protocolo. Invoque como `python .agents/skills/priority/writing-skills/scripts/validate_metadata.py --path <dir-da-skill>`.
