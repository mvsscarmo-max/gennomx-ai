<!-- validate-links: illustrative-paths -->
<!-- Os caminhos citados em prosa descrevem a estrutura de destino num projeto que adota o
     protocolo, não o layout do repositório de origem. Links markdown continuam verificados. -->

# Identificadores e registros

Todo registro tem um identificador estável, e cada família vive numa camada específica da fonte
única de verdade. Quem entende o mapa não precisa procurar: sabe onde o registro nasce, quem o
valida e o que quebra se ele for movido.

**Regra transversal, sem exceção: identificadores NUNCA são reutilizados** — nem os de linhas de
trabalho canceladas, nem os de tarefas que nunca começaram, nem os de descobertas resolvidas, nem
os de gates aposentados.

## 1. Formato

```text
<PREFIXO>-<NNN>
```

`NNN` é decimal, com zero à esquerda, mínimo três dígitos, monotonicamente crescente dentro do
escopo do prefixo. O identificador é **opaco**: não codifica data, autor, prioridade nem estado.
Codificar significado no identificador cria a tentação de "corrigi-lo" quando o significado muda —
e identificador que muda deixa de identificar.

## 2. Famílias

### `WS-NNN` — workstream · camada 2

Uma linha de trabalho independente. Investigação paralela abre a sua.

| | |
|---|---|
| **Onde nasce** | `project_state/WORKSTREAMS.md`, campo `**Próximo ID:**` |
| **Onde vive** | `project_state/workstreams/WS-NNN-<slug>/` |
| **Quem aloca** | automação de criação — diretório e linha de índice na **mesma passagem** |
| **Escopo de unicidade** | projeto |
| **Estados** | `proposed` · `active` · `paused` · `blocked` · `completed` · `cancelled` |

`active` exige plano em execução **e** tarefa em andamento. Diretório sem linha no índice, ou linha
sem diretório, é workstream órfã: a reconciliação vem antes de qualquer outro trabalho.

### `T-NNN` — tarefa · camada 3

| | |
|---|---|
| **Onde vive** | seção `## Tarefas` do `STATE.md`, e como campo `task` no ledger |
| **Quem aloca** | automação, varrendo estados, ledgers **e planos** |
| **Escopo de unicidade** | projeto (não a workstream) |
| **Estados** | `aberta` · `em andamento` · `bloqueada` · `parcial` · `concluída` · `cancelada` |

Toda tarefa declara **origem** (`PLAN-NNN` ou `ad-hoc`) e, ao fechar, **evidência**. Tarefa
concluída sem evidência executada **não existe**.

> **Armadilha conhecida.** Se o alocador não ler os planos, os identificadores reservados num plano
> ainda não iniciado ficam invisíveis e podem ser realocados. O alocador **deve** varrer também
> `project_state/plans/`, incluindo intervalos escritos como `T-194 … T-208`.

### `PLAN-NNN` — plano · camada derivada

| | |
|---|---|
| **Onde vive** | `project_state/plans/PLAN-NNN-<slug>.md` |
| **Estados** | `proposto` · `aprovado` · `em execução` · `concluído` · `cancelado` |

Todo critério de validação precisa de **comando exato** — critério sem comando é intenção. Um plano
só está `em execução` enquanto uma workstream o declara ativo; **o status do plano herda o da
workstream, nunca o contrário**.

### `D-NNN` — decisão · camada 4

| | |
|---|---|
| **Onde vive** | `project_state/DECISIONS.md`, ordem cronológica |
| **Campos** | Data · Autor · Status · Autoridade · Contexto · Decisão · Alternativas descartadas · Impacto · Substitui / substituída por |
| **Consolidação** | por ciclo, no `CHANGELOG.md` (consolidação, nunca registro novo) |

Uma decisão **pode** ser revogada por cláusula: uma decisão nova revoga os parágrafos §5 e §6 de
outra sem invalidar o resto. Quando isso acontece, **os dois lados precisam do marcador** — é o que
a verificação de reciprocidade cobra.

### `F-NNN` — finding · camada 4

| | |
|---|---|
| **Onde vive** | `project_state/FINDINGS.md` |
| **Entrada** | gateada por triagem (ver `docs/findings-triage.md`) |
| **Estados** | `aberto` · `resolvido` · `superado-por F-NNN` · `histórico` |

Dois eixos de entrada: **defeitos** só viram finding formal quando Críticos ou Altos; **achados
estruturais** entram em qualquer severidade, pelo valor de reuso — são eles que impedem
reinvestigação. Médios e baixos permanecem no documento de origem, sob identificador local.
Promoção tardia existe; **rebaixamento e remoção, nunca**.

### `E-NNN` — evidência · camada 5

| | |
|---|---|
| **Onde vive** | `EVIDENCE.md` da workstream, como `## E-NNN — <título>` |
| **Escopo de unicidade** | **local à workstream** |
| **Conteúdo** | comando + saída + timestamp + commit |

O `E-001` de uma workstream não tem relação com o `E-001` de outra. Ao citar evidência de fora,
**prefixe**: `WS-004:E-051`.

### `AUD-NNN` — auditoria · camada 2

| | |
|---|---|
| **Onde nasce** | `project_state/AUDITS.md`, campo `**Próximo ID:**` |
| **Onde vive** | `audits/AUD-NNN-<slug>.md`; o índice espelha o status |
| **Estados** | `vigente` · `parcialmente-endereçada` · `endereçada` · `superada-por AUD-NNN` · `histórica` |

O identificador é a identidade; **o caminho é campo do índice** — auditorias antigas podem manter
caminhos históricos. Prefixo de três letras deliberadamente: `AUD` não colide com identificadores
locais de documento que usem `A-NN`.

### `G-NN` — gate · camada 3

| | |
|---|---|
| **Onde vive** | `pending_gates` no frontmatter do `STATE.md` |
| **Norma** | `docs/quality-gates.md` |

Gates aposentados **mantêm o número reservado para sempre**. Artefatos selados sob um gate
aposentado permanecem como registro histórico, nunca como prova de conclusão.

### `K-NNN` — conhecimento · consolidado

| | |
|---|---|
| **Onde vive** | `project_state/knowledge/{candidates,experiments,historical}/` |
| **Estados** | `candidate` · `active` · `superseded` |

Supersessão **move** o arquivo e marca o status, **mantendo o identificador**. Candidato não
aprovado em 90 dias expira para histórico com o motivo — a não promoção também é conhecimento.

### Identificadores locais de documento — `P-NN`, `V-NN`, `C-NN`, `R-NN`, `A-NN`

Identificam itens **dentro de um documento de origem**, sem entrar no ledger global. É o mecanismo
que a triagem exige: todo parecer ou auditoria que lista achados declara, por item, **identificador
local, severidade e tipo**.

Um identificador local só sobe para finding formal por promoção explícita, e o finding novo **cita
o identificador local de origem**. Quando dois caminhos independentes descrevem o mesmo defeito,
isso é **confirmação cruzada** — e o registro precisa dizer isso, em vez de duplicar o achado.

### Identificadores de proveniência externa

**Nunca** resolvidos contra o estado local. Sempre com namespace explícito:

| Forma | Significado |
|---|---|
| `<projeto>:e66cd9a` | commit de um repositório irmão |
| `<projeto>:E-010` | evidência registrada dentro de outro projeto |
| `<documento> C-09` | item de um documento upstream, homônimo de identificadores locais |
| `coordination:AGENT-001` | agente registrado na camada de coordenação |

**Homônimo não é o mesmo registro.** Esta é a regra que impede que um relatório importado de outro
repositório seja lido como se descrevesse o estado local.

## 3. Como os identificadores se correlacionam

```text
  descoberta            F-NNN  --------------------+
      |                                            |
      v                                            v
  decisão               D-NNN  -----> PLAN-NNN --> T-NNN --> E-NNN
      |                    |             |           |         ^
      |                    |             |           v         |
      +--> CHANGELOG.md    |             |         G-NN -----> RC / AUD-NNN (R-NN)
                           |             |           |
                           v             v
                    AGENTS.md /     WS-NNN (STATE.md)
                    docs/rules/
```

Em palavras: um **finding** motiva uma **decisão**; a decisão autoriza um **plano**; o plano vira
**tarefas** dentro de uma **workstream**; cada tarefa fecha com **evidência**; o risco da workstream
determina quais **gates** se aplicam; em risco alto a Revisão de Ciclo produz uma **auditoria** com
identificadores locais. Decisões que mudam norma alteram o núcleo residente ou as regras; decisões
implementadas são consolidadas no changelog.

### Tabela de correlação entre documentos

| Documento | Consome | Produz | Nunca contém |
|---|---|---|---|
| `PROJECT.md` | D-NNN, F-NNN (fatos canônicos) | — | tarefa, status volátil |
| `WORKSTREAMS.md` | WS-NNN | próximo WS-NNN | detalhe de tarefa |
| `AUDITS.md` | AUD-NNN | próximo AUD-NNN | corpo da auditoria |
| `STATE.md` | PLAN-NNN, D-NNN, F-NNN | T-NNN, gates pendentes | prova de execução |
| `DECISIONS.md` | F-NNN, PLAN-NNN | D-NNN | evidência bruta |
| `FINDINGS.md` | identificador local de origem | F-NNN | cópia do documento de origem |
| `EVIDENCE.md` | T-NNN | E-NNN | resumo sem comando |
| `EVENTS.jsonl` | tudo | histórico append-only | reescrita |
| `PLAN-NNN` | D-NNN, F-NNN | reserva de T-NNN | estado de execução |
| auditoria | — | identificador local | F-NNN direto |
| `CHANGELOG.md` | D-NNN implementadas | consolidação por ciclo | decisão nova |

### Onde cada pergunta se responde

| Pergunta | Vá para |
|---|---|
| Em que estamos trabalhando agora? | `WORKSTREAMS.md` → `STATE.md` da workstream ativa |
| Que auditorias ainda orientam? | `AUDITS.md` → documento só se o status exigir |
| Por que isto é assim? | `DECISIONS.md` |
| Isto já foi investigado? | `FINDINGS.md` — findings estruturais existem exatamente para isso |
| Isto foi mesmo executado? | `EVIDENCE.md` da workstream, e o ledger |
| O que falta para fechar? | `pending_gates` no frontmatter do `STATE.md` |
| Como continuar o trabalho de outro agente? | `HANDOFF.md`, **se o commit ainda casar** |
| Qual era o estado antes? | caminhos congelados — consulta, nunca insumo |

## 4. Registros e o que cada um é

| Registro | Tipo | O que garante | O que **não** garante |
|---|---|---|---|
| `WORKSTREAMS.md` | índice | que a linha existe e em que estado | que o trabalho está em dia |
| `AUDITS.md` | índice | que a auditoria existe e seu status | que os achados foram tratados |
| `local-skills.yaml` | índice + metadado | que a skill existe no caminho, com aquele hash | que a skill é boa |
| `external-skills.yaml` | catálogo | que a skill foi catalogada | que foi auditada ou aprovada |
| `EVENTS.jsonl` | ledger append-only | que aquilo aconteceu naquele commit | que continua verdade |
| `EVIDENCE.md` | prova | que o comando rodou e produziu aquela saída | que o código não regrediu depois |
| `DECISIONS.md` | normativo | que a escolha foi feita com autoridade | que ainda é a melhor escolha |
| `FINDINGS.md` | normativo | que a descoberta foi registrada | que ainda reproduz |
| `CHANGELOG.md` | derivado | consolidação do que foi implementado | registro primário de decisão |

## 5. Erros comuns

1. **Reaproveitar identificador de item cancelado.** Proibido. O histórico deixa de ser rastreável.
2. **Numerar evidência globalmente.** É local à workstream; ao citar de fora, prefixe.
3. **Citar uma rodada sem namespace.** Rótulos homônimos em espaços diferentes se confundem. Sempre qualifique.
4. **Promover achado médio a finding formal "para não esquecer".** A triagem existe porque ledger inchado deixa de ser lido. O documento de origem já guarda o item.
5. **Declarar tarefa concluída citando evidência de outro commit.** Isso é falsificação de evidência, não erro de forma.
6. **Resolver conflito entre documentos em silêncio.** Explicite, avalie a evidência, recomende a versão que prevalece com grau de confiança.
7. **Tratar registro histórico como vigente.** Arquivos congelados guardam cópias de planos que se declaram ativos e não são.
8. **Criar o diretório da workstream sem a linha no índice** (ou o inverso). As duas coisas na mesma passagem, ou nenhuma.

## 6. Verificações que um validador conforme deve fazer

| Verificação | Severidade |
|---|---|
| identificador reutilizado em qualquer família | ERROR |
| workstream órfã (diretório sem índice, ou índice sem diretório) | ERROR |
| status divergente entre índice e frontmatter | ERROR |
| tarefa sem origem declarada | ERROR |
| tarefa concluída sem evidência apontada | ERROR |
| evidência apontada que não existe, ou sem comando/commit | ERROR |
| plano sem status, sem critério, ou com critério sem comando | ERROR |
| decisão sem status ou sem autoridade | ERROR |
| supersessão declarada de um lado só | ERROR |
| workstream ativa sem plano ou sem tarefa em andamento | ERROR |
| handoff sem commit, ou com commit diferente do vigente | ERROR / WARNING |
| identificador citado que não existe em lugar nenhum | WARNING |
| workstream pausada há muito tempo sem handoff atualizado | WARNING |
