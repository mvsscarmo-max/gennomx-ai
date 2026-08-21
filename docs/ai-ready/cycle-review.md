<!-- validate-links: illustrative-paths -->

# Revisão de Ciclo — norma de execução

Como a verificação independente opera: G13 (mecânica), fase RC (julgamento) e G14 (autoridade).

## 1. Princípio

**Liberal na notação, estrito no julgamento.** Seta ASCII, travessão simples e lista no lugar de
subtítulo não custam rodada. Tabela de paridade ausente, contrato não avaliado e autor igual a
revisor reprovam. Um veredito de aprovação sem a tabela preenchida, quando o prompt a exigia, é
**rodada inválida**. Engenharia elegante que não entrega o campo do plano não é aprovação.

Três camadas, cada uma no preço do que verifica:

| Camada | Mecanismo | Quando | Custo |
|---|---|---|---|
| Mecânica | **G13** — verificação diferencial | risco ≥ 2 | segundos, recomputável |
| Julgamento | **RC** — Revisão de Ciclo | risco ≥ 3, uma vez por workstream | 1 invocação de revisor |
| Autoridade | **G14** — aceite humano assinado | risco ≥ 3 | leitura do responsável |

## 2. G13 — Verificação diferencial

Detectores determinísticos sobre `base_commit..HEAD` (lista em
[quality-gates.md](quality-gates.md) §2). **Nada é selado nem fixado a um SHA**: se o tip andar, o
detector roda de novo.

> **Por que recomputável, e não selado.** Um gate cujo resultado é um selo preso a um commit
> obriga a reabrir o gate a cada commit novo — inclusive o commit que registra o próprio selo.
> Isso gera uma cascata de re-verificação irredutível: o ato de provar move o alvo da prova. Um
> detector que simplesmente roda de novo não tem esse problema.

## 3. Fase RC — uma rodada de julgamento

Dispara em risco ≥ 3, **uma vez por workstream**, antes do commit de fechamento, e **pode barrar o
fechamento**.

- **Prompt único, duas seções:** (a) leitura adversarial do diff da janela; (b) conformidade com o protocolo, com as saídas de G13 e do validador **embutidas e assinadas** — o revisor não reexecuta o validador.
- **Saída:** uma auditoria `AUD-NNN`, com identificadores locais `R-01…R-NN`, cada um com severidade e tipo.
- **Triagem:** achados `critico` e `prova-obrigatoria` corrigem-se **nesta** workstream, e a correção é verificada por **G13** — nunca por outra invocação de revisor. As demais classes viram finding + plano + tarefa da workstream seguinte.

**Invariante duro:** uma rodada de julgamento por workstream. **Não existe rodada 2.** Tentativa de
*invocação* que falhou por infraestrutura ainda tem orçamento; rodada de *julgamento* tem teto 1.

### Classes de achado

| Classe | Ação |
|---|---|
| `critico` | corrigir sempre; G13 verifica; **nunca** aceite por decisão |
| `prova-obrigatoria` | corrigir; G13 verifica; **nunca** aceite por decisão |
| `contrato` | corrigir nesta workstream, ou decisão registrada com prazo |
| `cobertura-adicional` · `risco` · `nit` | ressalva → finding ou tarefa da workstream seguinte |

Comportamento novo sem teste é `prova-obrigatoria`. Teste ignorado ou com asserção removida é
`critico`.

## 4. Independência do revisor

**A regra:** o revisor **deve** ser distinto do autor — modelo diferente e, no mesmo ambiente,
processo separado. **Nunca um subagente do próprio autor**, que herda o contexto e o viés de quem
escreveu o código.

O projeto **deveria** declarar uma escada nomeada de revisores, na ordem de preferência, e o
critério de descida. E **deve** escrever a consequência aritmética da escada em vez de descobri-la
em produção:

> Com uma escada de N degraus e o autor ocupando um deles, sobram **N−1** revisores independentes.
> Se N = 2, há **exatamente um** revisor por workstream e **nenhum terceiro fallback**.

Esgotado o orçamento de tentativas por falha de infraestrutura, o fechamento destrava por **G14 com
decisão registrada e prazo**, e a RC fica pendente para a workstream seguinte. **Só a ausência de
revisor se destrava assim — nunca um achado crítico já produzido.**

### Relógios do runner

Quem automatiza a invocação **deve**: capturar `stderr` (não só `stdout`); definir um limite de
inatividade (referência: 600 s sem um byte) e um teto duro de execução (referência: 1800 s). Um
processo pendurado sem saída conta como uma tentativa de infraestrutura, não como veredito.

## 5. Pré-voo

Idêntico ao de [quality-gates.md](quality-gates.md) §3. Marcador falho → aborte e reporte qual.

## 6. G14 — Aceite de fechamento

Bloco assinado em `EVIDENCE.md`: o responsável humano declara ter lido o resumo do diff, o
relatório de G13 e o diagnóstico da RC, e **aceita** ou **nomeia ressalvas** como findings com
prazo.

**Agente nunca assina.** Um validador conforme deve reprovar um bloco de G14 cujo signatário seja um
agente — é a única forma de a não-autocertificação ser verificável em vez de prometida.

Quem pode assinar é **declarado pelo projeto** em `g14_signers:`, não fixado no validador: gravar o
nome de uma pessoa no código transformaria uma escolha local em regra do protocolo.

> **Limite declarado.** Texto em Markdown é **declaração, não autenticação**. O validador verifica
> que o bloco existe, que nomeia um signatário declarado e que não foi assinado por agente. Ele
> **não** prova que a pessoa nomeada de fato leu e aceitou. Um projeto que precise dessa prova deve
> amarrar G14 a um sinal externo verificável — commit assinado, aprovação de plataforma — e essa é
> uma extensão do projeto, não do protocolo, que opera sem rede e com Git opcional.

## 7. O que continua invalidando

Nada aqui afrouxa [quality-gates.md](quality-gates.md) §4. Declarar aprovado teste não executado,
colar saída anterior ao último commit, tratar a saída bruta de um processo como parecer, ou editar
o parecer do revisor para passar no validador continua sendo falsificação.
