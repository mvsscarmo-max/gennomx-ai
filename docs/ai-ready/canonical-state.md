<!-- validate-links: illustrative-paths -->
<!-- Os caminhos citados em prosa descrevem a estrutura de destino num projeto que adota o
     protocolo, não o layout do repositório de origem. Links markdown continuam verificados. -->

# Estado canônico

Responde a uma pergunta só, e sem ambiguidade: **quando dois arquivos discordam, qual vence?**

Um projeto que não sabe responder isso não tem uma fonte de verdade — tem várias, e a que prevalece
é a que o leitor abriu primeiro.

## 1. As camadas da fonte única de verdade

Autoridade decrescente. Em conflito entre documentos, a camada de cima vence; dentro da mesma
camada, o registro mais recente vence. **Contra o código, nenhum documento vence.**

```text
0  CÓDIGO       o código, a configuração e o schema atuais    o que o sistema É
                                                   |
1  DURÁVEL      project_state/PROJECT.md           o que o projeto é
                                                   |
2  ÍNDICE VIVO  WORKSTREAMS.md · AUDITS.md         que linhas e auditorias existem
                                                   |
3  OPERACIONAL  workstreams/<WS>/STATE.md          o que está em curso
                                                   |
4  NORMATIVO    DECISIONS.md · FINDINGS.md         o que foi decidido e descoberto
                                                   |
5  PROBATÓRIO   EVIDENCE.md · EVENTS.jsonl         o que foi executado

   DERIVADO     plans/ · docs/ · audits/           como será feito
   HISTÓRICO    docs/legacy/ · docs/historico/     o que já foi (congelado)
```

**Derivado não é inferior — é dependente.** Um plano descreve trabalho que só existe de verdade
quando vira tarefa dentro de uma workstream.

**Histórico não orienta** planejamento, priorização nem decisão, salvo consulta explícita declarada
no `STATE.md` da workstream.

## 2. Taxonomia por artefato

Cada artefato do protocolo é exatamente **um** destes tipos. Confundi-los é a origem da maior parte
dos conflitos de estado.

| Tipo | Definição | Pode ser reconstruído? | Quem escreve |
|---|---|---|---|
| **Fonte de verdade** | a afirmação original; não deriva de nada | não | quem tem autoridade para o registro |
| **Representação derivada** | reexpressa uma fonte para outro público ou formato | sim, da fonte | quem gera a derivação |
| **Cache** | cópia por desempenho, com invalidação declarada | sim, sempre | automação |
| **Índice** | ponteiros e status; nunca o corpo | sim, varrendo o que indexa | automação ou quem cria a entrada |
| **Registro histórico** | verdadeiro no passado; congelado | não | ninguém (é imutável) |
| **Metadado** | descreve outro artefato (autoria, hash, versão) | sim, do artefato | automação |
| **Configuração** | parâmetro de comportamento | não | humano |
| **Artefato gerado** | saída de um processo determinístico | sim, reexecutando | automação |

### Classificação de referência

| Artefato | Tipo | Deriva de | Regenerável por |
|---|---|---|---|
| `AGENTS.md` | fonte de verdade (residente) | — | — |
| `docs/` normativo | fonte de verdade (normativa) | decisões aprovadas | — |
| `project_state/PROJECT.md` | fonte de verdade (durável) | — | — |
| `PROJECT.md` § Fatos canônicos | fonte de verdade + índice | decisões e findings que os fixaram | — |
| `WORKSTREAMS.md` | **índice** | diretórios de workstream | varredura de `workstreams/*/STATE.md` |
| `AUDITS.md` | **índice** | frontmatter das auditorias | varredura de `audits/*.md` |
| `STATE.md` frontmatter | fonte de verdade (operacional) | — | — |
| `STATE.md` § Digest | representação derivada | ledger | resumo do ledger |
| `DECISIONS.md` | fonte de verdade (normativa) | — | — |
| `FINDINGS.md` | fonte de verdade (normativa) | evidência | — |
| `EVIDENCE.md` | fonte de verdade (probatória) | execução real | reexecutando o comando |
| `EVENTS.jsonl` | fonte de verdade (probatória), append-only | — | — |
| `HANDOFF.md` | representação derivada | `STATE.md` + evidência + ledger | regenerável a partir deles |
| `CHANGELOG.md` | representação derivada | decisões implementadas | consolidação por ciclo |
| `plans/PLAN-NNN` | derivado | decisões e findings | — |
| `knowledge/` | consolidado | findings promovidos | — |
| `.agents/registry/local-skills.yaml` | **índice** (com metadado de hash) | `.agents/skills/` | varredura + hash |
| `.agents/registry/external-skills.yaml` | catálogo (índice) | fonte externa | reimportação após intake |
| `.agents/templates/` | configuração | — | — |
| `.agents/policy/` | configuração | — | — |
| aliases de ferramenta | **artefato gerado**, não versionado | `.agents/skills/` | comando de bootstrap |
| estado quente de coordenação | **cache**, não versionado | runtime | descartável |
| `docs/legacy/`, `docs/historico/` | registro histórico | — | nunca |

## 3. Regras de resolução de conflito

**C1 — Código vence documento.** Registre a divergência como finding com autoridade `evidence`
(arquivo, linha, o que o doc diz, o que o código faz) e corrija **o documento**. Exceção: se o
código contradiz uma **decisão ativa**, pare — registre o finding e proponha decisão substituta.
Não alinhe o código ao papel nem o papel ao código sem aprovação humana.

**C2 — Camada mais alta vence.** Um plano que contraria o `PROJECT.md` está errado, não o contrário.

**C3 — Dentro da camada, o mais recente vence** — mas só dentro da mesma camada. Recência **não**
promove um registro de camada inferior.

**C4 — Índice e corpo devem coincidir.** Divergência entre o status no índice e o status no
frontmatter do documento é **erro**, não preferência. O índice é regenerável; o corpo não.

**C5 — Entre índice e diretório, reconcilie antes de qualquer outro trabalho.** Diretório sem linha
no índice, ou linha sem diretório, é registro órfão.

**C6 — Nunca resolva um conflito em silêncio.** Explicite o conflito, avalie a evidência e
recomende qual versão prevalece, **com grau de confiança**.

## 4. O que nunca é duplicado

| Nunca duplicar | Por quê | O que fazer |
|---|---|---|
| Regra normativa em dois arquivos | dessincroniza na primeira edição | um arquivo é a fonte; o outro aponta |
| Corpo de skill fora da fonte canônica | cópia divergente é indetectável a olho | o registro indexa por caminho e hash |
| Tarefa em lista global **e** em workstream | dois donos, nenhum responsável | a workstream é a única dona |
| Decisão em `DECISIONS.md` **e** em `CHANGELOG.md` como registro novo | duplica a dúvida "onde escrevo isto" | `DECISIONS.md` registra; o changelog **consolida** o já implementado |
| Corpo de auditoria dentro do índice | índice inchado deixa de ser lido | o índice aponta; o corpo fica no documento |
| Achado de severidade baixa promovido a registro global | ledger inchado deixa de ser lido | permanece no documento de origem, com identificador local |
| Plano em dois caminhos rastreados | qual está vigente? | o segundo é congelado com banner |

## 5. O que pode ser regenerado — e o que não pode

**Regenerável** (perder é inconveniente, não catastrófico): índices de workstreams e auditorias ·
hashes do registro de skills · aliases de ferramenta · digest de sessão no `STATE.md` · changelog
consolidado · handoff · qualquer artefato marcado "gerado".

**Não regenerável** (perder é perda real): o ledger · a evidência · as decisões · os findings · o
conteúdo normativo · o histórico congelado.

A distinção governa a política de retenção: o que não é regenerável **nunca** é apagado
automaticamente.

## 6. Fatos canônicos

O `PROJECT.md` **deveria** manter uma seção de fatos canônicos: valores vigentes, o registro que os
fixou e — o que a torna útil — os **valores aposentados**.

| Fato | Vigente | Fixado por | Aposentado |
|---|---|---|---|
| `<nome do fato>` | `<valor atual>` | `<D-NNN ou F-NNN>` | `<valor anterior>` |

Repetir um valor aposentado num arquivo vivo passa a ser **contradição detectável por varredura**,
não inferência semântica. É a diferença entre "acho que este IP está velho" e "este IP está na
coluna Aposentado e apareceu em `docs/rules/`".

## 7. Ciclo de vida de um registro

```text
criação → registro no índice → modificação → (supersessão | expiração por escopo)
                                           → congelamento → consulta declarada
```

| Etapa | Regra |
|---|---|
| **Criação** | nasce com identificador, autoridade e status; identificador nunca reutilizado |
| **Registro** | entra no índice na **mesma passagem** em que o corpo é criado — nunca depois |
| **Modificação** | altera o corpo, registra a transição de status no ledger com o motivo |
| **Supersessão** | recebe `substituído por <ID>`; o novo referencia o antigo; **reciprocidade obrigatória** |
| **Expiração por escopo** | o corpo limitava a validade a uma passagem nomeada, e ela terminou |
| **Congelamento** | recebe banner na primeira linha, sai do orçamento de contexto, deixa de orientar |
| **Reconstrução** | só para artefato regenerável (§5), por comando determinístico |
| **Exclusão** | apagar histórico auditável é **proibido**; purga é ação de nível 5, com registro do que foi purgado |

## 8. Perguntas frequentes de desempate

| Situação | Resposta |
|---|---|
| O `STATE.md` diz que a tarefa foi concluída, mas não há evidência | A tarefa **não** foi concluída. Evidência é constitutiva, não decorativa |
| O handoff diz "testes passaram", sem apontar a linha da evidência | É alegação, não prova. Trate como não validado |
| O ledger registra que um caminho foi descartado há três meses | Prova que foi descartado **naquele commit**. Hoje é `historical` |
| Uma decisão ativa contradiz o código | Pare. Finding + proposta de decisão substituta |
| Duas decisões se contradizem e nenhuma se declara substituída | Erro de reciprocidade. Corrija o marcador dos dois lados antes de agir |
| Um documento em `docs/` contradiz uma decisão ativa | O documento entra em fila de atualização; isso sozinho **não** reprova o gate |
| Um plano se declara "em execução" mas nenhuma workstream o detém | O plano **não** está em execução. O status do plano **herda** o da workstream |
| Um arquivo congelado descreve o estado como ativo | Congelado não orienta. O que vale é o estado vigente |
