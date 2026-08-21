<!-- validate-links: illustrative-paths -->

# Modelo de autoridade

Memória não é verdade. Um registro prova que algo foi **dito, tentado, observado, executado ou
registrado** — não que continua correto. Este documento diz quanto peso cada informação tem.

## 1. Ordem de verdade

```text
1.  Código, configuração e schema atuais
2.  Requisitos aprovados
3.  Regras normativas
4.  Decisões ativas
5.  Testes e evidências recentes
6.  Conhecimento consolidado
7.  Estado operacional
8.  Handoff
9.  Ledger
10. Transcrição bruta
```

Em conflito, o número menor vence. Exceção exige justificativa escrita no `STATE.md`.

> Um teste recente (5) que reprova o código (1) **não** torna o código correto; torna o código
> defeituoso. A ordem não diz "o código está certo" — diz "o código é o que **é**". É uma ordem de
> factualidade, não de qualidade.

## 2. Níveis de autoridade de um registro

Todo registro carrega um nível. **Sem nível declarado, o padrão é `hypothesis`.**

| Nível | Significa | Quem pode criar | Vira regra? |
|---|---|---|---|
| `normative` | regra vinculante do projeto | humano | já é |
| `approved-decision` | escolha estrutural aprovada | humano | já é |
| `verified-knowledge` | aprendizado revisado e aprovado | humano aprova, agente propõe | sim, por promoção |
| `operational-state` | o que está acontecendo agora | agente | não |
| `evidence` | comando executado e sua saída | agente | não, mas fundamenta |
| `hypothesis` | suposição não verificada | agente | nunca sem verificação |
| `historical` | verdadeiro no passado, não revalidado | qualquer | não |
| `superseded` | substituído por registro mais novo | qualquer | não |

O padrão `hypothesis` é deliberadamente pessimista: um registro que não declara sua autoridade é
tratado como o mais fraco possível. O ônus de declarar é de quem escreve, não de quem lê.

## 3. O que o ledger prova

Um evento prova **apenas** que aquilo aconteceu naquele momento, naquele commit. Não prova que:

- a solução ainda funciona;
- a decisão continua válida;
- o caminho descartado continua inviável;
- o teste ainda passa.

Por isso todo evento carrega `commit`. Um resultado observado em commit anterior é `historical` até
ser reexecutado.

## 4. Supersessão

Registro nunca é apagado. Quando deixa de valer:

```text
Status: superseded by <ID>
```

E o novo referencia o antigo. **Reciprocidade é obrigatória**: se o novo diz "substitui X", o
cabeçalho de X diz "substituída por". Marcador de um lado só é erro detectável, e é o caso em que o
leitor descobre a substituição por acaso — ou não descobre.

Vale para decisões, findings, conhecimento promovido e handoffs. Apagar histórico auditável é
**proibido**.

Um handoff passa a `historical` quando seu commit difere do commit vigente no `STATE.md`.
Ancestralidade apenas mostra que ele pertence à mesma linha de desenvolvimento; **não prova que o
resumo continua atual**.

## 5. Divergência documentação × código

O código vence. Procedimento:

1. Registre a divergência como finding com nível `evidence` — arquivo, linha, o que o doc diz, o que o código faz.
2. Corrija **o documento** — não o código, salvo se a tarefa for exatamente essa.
3. Se o código contradiz uma **decisão ativa**, **pare**: registre o finding e proponha decisão substituta. Não alinhe o código ao papel nem o papel ao código sem aprovação humana.

O passo 3 existe porque os dois atalhos são igualmente destrutivos: mudar o código para casar com o
papel descarta uma escolha real feita por alguém; mudar o papel para casar com o código apaga uma
decisão sem que ninguém tenha decidido revogá-la.

## 6. Handoff, resumo e evidência

- **Handoff** é resumo operacional. Não substitui ledger, decisões nem documentação normativa.
- **Resumo nunca é evidência.** Um handoff que diz "testes passaram" sem apontar a linha da evidência é uma alegação, não uma prova.
- **Evidência** é comando + saída + timestamp + commit. Sem os quatro, é hipótese.
