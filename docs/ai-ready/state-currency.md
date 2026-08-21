<!-- validate-links: illustrative-paths -->

# Vigência do estado — quando um registro ainda vale

Responde, sem ambiguidade, **«este registro ainda vale?»** para decisão, finding, plano,
workstream, verificação independente e auditoria.

Esta norma **não** redefine identificadores (ver [../IDS-AND-REGISTRIES.md](ids-and-registries.md)).
Define **quando o status de um registro deixa de ser vigente**.

## 1. Fonte única de verdade — camadas

Nenhum arquivo novo de estado. A fonte já existe; é **declarada em camadas**, com autoridade
decrescente (ver [../CANONICAL-STATE.md](canonical-state.md) §1).

Em conflito: o **código** vence o documento; entre documentos, a **camada mais alta** vence; dentro
da mesma camada, o registro **mais recente** vence.

A seção de **fatos canônicos** do `PROJECT.md` lista valores vigentes, o registro que os fixou e os
**valores aposentados**. Repetir um valor aposentado num arquivo vivo passa a ser **contradição
detectável por varredura** — não inferência semântica.

## 2. Vocabulário e critérios por tipo

Vocabulário **fechado**. Status fora da lista é inválido. Perda de vigência só ocorre pelos
critérios abaixo — **nunca** por «parecer desatualizado».

### 2.1 Decisão

**Status:** `ativa` · `parcialmente-revogada` · `substituída` · `expirada-por-escopo` · `histórica`

**Ainda vale?** Só se `ativa` (ou a cláusula nomeada ainda válida em `parcialmente-revogada`).

| | Critério de perda de vigência |
|---|---|
| **(a)** | Outra decisão a declara substituída ou revogada — total, ou por cláusula nomeada. **Reciprocidade obrigatória**: se a nova diz «substitui X», o cabeçalho de X diz «substituída por» |
| **(b)** | Um finding com autoridade `evidence` prova que o fato que a fundamentava não existe mais |
| **(c)** | Seu corpo limita o escopo a uma tarefa ou passagem nomeada, e ela terminou → `expirada-por-escopo` |
| **(d)** | Se o **código diverge** dela, ela **não expira** — entra em fila de atualização, e o divergente vira finding |

O critério (d) é o que impede que uma decisão seja revogada por acidente: código divergente é
sintoma, não revogação.

### 2.2 Finding

**Status:** `aberto` · `resolvido` · `superado-por F-NNN` · `histórico`

**Ainda vale como pendência?** Só se `aberto`.

Só sai de `aberto` com **comando e saída** registrados provando que o comportamento descrito **não
reproduz mais**. Leitura não fecha finding.

### 2.3 Plano

**Ainda vale como plano em curso?** Enquanto alguma workstream o declara ativo, ou alguma tarefa
aberta o cita como origem. Sem isso, o status terminal é `concluído`, `pausado`, `arquivado` ou
`bloqueado` conforme a workstream. **O cabeçalho do plano herda o status da workstream que o
detém — nunca o contrário.**

### 2.4 Workstream

**Ainda vale como linha ativa?** Só com status `active` **e**, cumulativamente:

1. plano em execução;
2. ao menos uma tarefa em andamento;
3. commit vigente alcançável a partir do `HEAD` da worktree declarada.

Snapshot desatualizado é **erro** em `active`; nos demais status, **aviso**.

### 2.5 Verificação independente

**G13** é recomputável — não há «rodada vigente presa a um SHA»; se o tip andar, o detector roda de
novo. A **RC** produz **uma** auditoria por workstream de risco ≥ 3; não existe rodada 2 de
julgamento. **G14** é o bloco assinado por humano.

Artefatos selados sob gates aposentados, em workstream fechada, são registro histórico — **não**
base de retomada nem prova sob o regime vigente.

### 2.6 Documento de referência

Vigente enquanto nenhuma decisão `ativa` o contradiz. Contradição detectada entra em fila de
atualização — **não** reprova o gate por si só.

### 2.7 Auditoria

**Status:** `vigente` · `parcialmente-endereçada` · `endereçada` · `superada-por AUD-NNN` ·
`histórica`

**Ainda vale como orientação?** Só `vigente` e, no trecho ainda aberto,
`parcialmente-endereçada`. `endereçada` e `superada-por` permanecem legíveis como origem; **não
abrem trabalho novo**.

O status vive no **frontmatter** do documento e é **espelhado** na linha do índice. **Divergência
entre os dois é erro.**

## 3. Congelamento e prevenção de duplicidade

Todo arquivo congelado recebe, na **primeira linha**:

```html
<!-- vlaeg:frozen at=AAAA-MM-DD by=D-NNN reason="..." -->
```

- Arquivo em caminho congelado **sem** banner → erro.
- O mesmo plano em dois caminhos rastreados, sem que o segundo esteja congelado → erro.
- O orçamento de contexto **exclui** os caminhos congelados do briefing.
- Varredura dos valores aposentados dos fatos canônicos em arquivos vivos → erro de contradição.

## 4. Registro de transição

Toda transição de status de decisão, finding, plano, workstream ou auditoria exige evento no ledger
com:

- `type`: **`currency_change`**
- os campos obrigatórios do ledger
- **motivo** preenchido (por que perdeu ou recuperou vigência)

Transição detectada no diff **sem** evento correspondente → erro. Data futura em qualquer registro
→ erro.

## 5. Estado atual × histórico

Conteúdo congelado **não orienta** planejamento, priorização nem decisão, salvo consulta explícita
como referência histórica — e essa consulta é **declarada** no `STATE.md` da workstream.

O banner e o orçamento de contexto tornam a regra **verificável**, não apenas escrita. Sem eles,
«não use o histórico» é conselho; com eles, é gate.

## 6. Como perguntar «ainda vale?»

| Tipo | Pergunta operacional | Resposta «sim» exige |
|---|---|---|
| Decisão | O status é `ativa` (ou a cláusula parcial cobre o caso)? | cabeçalho coerente; sem substituta reciprocamente marcada; escopo não esgotado |
| Finding | O status é `aberto`? | sem evidência executada que prove o contrário |
| Plano | Alguma workstream o tem como ativo, ou tarefa aberta o cita? | status herdado da workstream detentora |
| Workstream | `active` + plano + tarefa em andamento + commit alcançável? | os três, cumulativos |
| Auditoria | `vigente`, ou trecho aberto em `parcialmente-endereçada`? | frontmatter = índice |
| G13 / RC / G14 | G13 verde no tip? RC única registrada? G14 assinado por humano? | os três |

Se a resposta for «não», o registro permanece **legível como histórico** — não como orientação
operacional.
