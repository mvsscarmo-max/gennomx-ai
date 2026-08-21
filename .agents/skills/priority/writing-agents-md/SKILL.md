---
name: writing-agents-md
description: Autora e enxuga arquivos de instrução residentes (AGENTS.md, CLAUDE.md, GEMINI.md) onde cada linha paga aluguel. Use ao escrever um arquivo de instrução do zero, auditar ou cortar um arquivo inchado, ou decidir se uma nova regra merece ficar residente e em qual escopo. Não use para skills sob demanda (use writing-skills), README, nem documentação humana.
metadata:
  protocol: VLAEG AI Ready First
  layer: priority
  version: 1.0.0
  source: pedronauck/skills@ffc7c18540fd41b3030b29c0b61a494de3d20d49/skills/mine/writing-agents-md
  video_evidence: "ohzc4p7-QHQ 02:05 — grupo GUIAS"
  adapted: true
  risk: medium
  vlaeg_phases: [A]
  triggers:
    - "criar ou editar AGENTS.md, CLAUDE.md, GEMINI.md ou equivalente"
    - "arquivo de instrução passou de uma tela"
    - "promover uma correção de chat a regra permanente"
  negative_triggers:
    - "escrever ou editar uma skill (use writing-skills)"
    - "escrever README ou documentação para humanos"
    - "documentar arquitetura (use docs/architecture/)"
  produces: ["AGENTS.md revisado", "tabela de veredito por linha", "D-NNN quando altera governança"]
  gates: ["G6", "G7", "G10"]
---

# Escrever AGENTS.md

Mantenha o arquivo de instrução enxuto o bastante para que cada regra nele **vincule**.

## Física: contexto residente

`AGENTS.md` não é documentação. É um fragmento do system prompt: o harness o injeta em toda
sessão, antes de a tarefa ser conhecida, e ele nunca sai. Uma skill carrega sob demanda; este
arquivo é **residente**. Três consequências governam tudo abaixo:

- **Cada linha tributa cada tarefa.** Regra relevante em 5% das sessões gasta atenção nos outros 95%.
- **Regras se diluem entre si.** Seguir instrução é um orçamento: quanto mais regras residentes, menos cada uma vincula. Arquivo inchado não impõe mais — impõe menos, e a regra crítica se afoga.
- **O leitor é um modelo de fronteira.** Ele já sabe Git, teste, os idiomas da linguagem e boa prática geral, e sabe ler o código. Ele precisa de **decisões**, não de conhecimento.

O arquivo que sobrevive a isso é um **delta**: a diferença entre o comportamento padrão do agente
e o que este projeto exige. O que não é delta é aluguel pago à toa.

## O teste do aluguel

Rode em toda linha escrita, mantida ou proposta. A linha fica só se as três valerem. Linha que
falha é **removida ou realocada**, nunca suavizada.

1. **Delta** — muda o que o agente faria de outro jeito. Repetir default, boa prática geral ou prosa motivacional falha aqui.
2. **Frequência** — vale para a maioria das sessões naquele escopo. Regra que só algumas tarefas precisam desce a escada.
3. **Economia** — mantê-la residente custa menos que derivá-la sob demanda. Comando de teste não óbvio passa (economiza uma busca por sessão); o que o toolchain anuncia sozinho — erro de tipo, saída de lint, CI vermelho — falha.

## Escada de escopo

Coloque cada regra no escopo mais estreito que ainda cobre as tarefas que precisam dela:

| Escopo | Residente para | Pertence ali |
|---|---|---|
| Global (`~/.claude/CLAUDE.md`) | todo projeto | regra de fluxo entre projetos — a barra mais alta |
| Raiz do repositório | toda tarefa do repo | comandos, tripwires do repo, desvios de convenção |
| Subdiretório (`<dir>/AGENTS.md`) | trabalho naquele subdiretório | regra de área, carregada só ao tocar a área |
| Skill | por gatilho | procedimentos e fluxos multi-etapa |
| Documento linkado | sob demanda | referência que algumas tarefas precisam |

Duas mecânicas decidem posicionamento mais que qualquer outra coisa: arquivos aninhados carregam
preguiçosamente — a árvore de diretórios **é** o carregamento progressivo nativo desses arquivos.
E um import expandido no carregamento (`@caminho`) é residente e paga aluguel integral, enquanto
um caminho citado em prosa é lido só sob demanda.

## O que merece residência

- Comandos que não dá para adivinhar: build, teste, execução, com flags e variáveis exigidas.
- Desvios de convenção: onde este repo faz X e o ecossistema faz Y.
- Tripwires: restrições cuja violação é cara — arquivo gerado que nunca se edita à mão, branch protegida, comando irreversível.
- Vocabulário de domínio com significado não óbvio no código.
- Ponteiros para material sob demanda, cada um redigido para *quando* carregar.

## Forma

- Uma regra, uma linha, imperativa e concreta: "Rode `make check` antes do commit", não "garanta qualidade".
- Declare cada regra **uma vez**. Regra repetida não reforça — compete com a cópia, e as cópias divergem.
- Enuncie o alvo positivo; guarde a proibição para tripwire, sempre com o que fazer no lugar.
- Cláusula de motivo (uma oração, não um parágrafo) só onde a regra parece arbitrária e os agentes insistem em "corrigi-la".
- Reserve ênfase (IMPORTANTE, NUNCA, maiúsculas) para a uma ou duas regras cuja violação é catastrófica. Ênfase em tudo é ênfase em nada.
- Regra clara dispensa exemplo. Se parece precisar de um, afie a regra até não precisar — exemplo paga aluguel dobrado e prende a regra a uma forma superficial.
- Agrupe por preocupação, em títulos planos, tripwires primeiro.
- Quando o arquivo da raiz passar de uma tela (~60 linhas), rode o ramo **Cortar** antes de acrescentar qualquer coisa.

## Ramos

**Escrever — arquivo novo**

1. Colete candidatos a delta do próprio repositório: manifestos, Makefile e CI para comandos reais; layout para desvios de convenção; histórico e docs existentes para tripwires.
2. Redija cada candidato pela Forma e posicione-o na escada de escopo.
3. Rode o teste do aluguel linha a linha; remova ou realoque as falhas.

*Concluído quando:* toda linha passa nos três testes no escopo escolhido.

**Cortar — arquivo existente**

1. Dê veredito a **toda** linha: manter / reescrever / realocar (com escopo destino) / despejar (com o teste que falhou). Regras contraditórias vão para o humano resolver — nunca escolha um lado em silêncio.
2. Apresente a tabela de veredito, depois aplique: reescreva os sobreviventes pela Forma, crie os arquivos de subdiretório e os ponteiros das realocações.

*Concluído quando:* toda linha original tem veredito e o arquivo sobrevivente passa na barra de Escrever.

**Portão — uma regra nova, em geral promovendo uma correção de chat**

1. Enuncie a candidata como uma linha imperativa positiva.
2. Rode o teste do aluguel e escolha o degrau da escada.
3. Procure no arquivo a regra que ela duplica ou contradiz e **atualize aquela regra no lugar** — acrescentar é como se forma sedimento.

*Concluído quando:* a regra vive em exatamente um escopo, exatamente uma vez.

## Integração com o protocolo

- Alterar `AGENTS.md` é decisão de governança: registre `D-NNN` em `project_state/DECISIONS.md`.
- O núcleo residente deste protocolo tem teto declarado em `.agents/policy/context-budget.yaml`; `tools/validate_ai_ready.py` reprova se estourar.
- Regra que nasce de aprendizado passa antes por `knowledge-promotion` — o portão aqui é o último passo, não o primeiro.
- `CLAUDE.md` e `GEMINI.md` são ponteiros puros. Escrever regra neles é o defeito que este protocolo chama de duplicação normativa.

## Modos de falha

- **Tecido cicatricial** — regra acrescentada depois de um incidente, residente para sempre. A busca por duplicata do ramo Portão é a resposta imunológica; reteste as regras vizinhas enquanto estiver ali.
- **Documentação espelho** — o arquivo repete o que o código já mostra (tour de arquitetura, inventário de arquivos). Falha o teste de delta por inteiro.
- **Proliferação de exemplo** — blocos bom/ruim se multiplicando sob cada regra. Corte os blocos, afie as regras.
- **Inflação de ênfase** — a corrida das maiúsculas. Termina com nada vinculando.
- **Reinstrução do harness** — reexplicar uso de ferramenta ou formato de resposta que o próprio system prompt do harness já governa. Aluguel puro; despeje ao ver.

## Anti-patterns

Arquivo que cresce a cada semana (contém estado, que pertence a `STATE.md`) · regra duplicada
entre `AGENTS.md` e skill · ponteiro sem condição de disparo ("veja X para mais") · seção de
"princípios" sem consequência operacional.
