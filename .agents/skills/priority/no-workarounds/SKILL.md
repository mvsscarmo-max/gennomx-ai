---
name: no-workarounds
description: Corrige o problema na causa raiz em vez de calar o sintoma. Use ao depurar, corrigir bug, resolver teste vermelho, planejar solução ou revisar mudança — sobretudo quando a correção silenciaria um sinal (asserção de tipo, supressão de lint, erro engolido, hack de tempo, monkey patch) em vez de reparar a origem. Não use para edição só de formatação ou só de documentação.
metadata:
  protocol: VLAEG AI Ready First
  layer: priority
  version: 1.0.0
  source: pedronauck/skills@ffc7c18540fd41b3030b29c0b61a494de3d20d49/skills/mine/no-workarounds
  video_evidence: "ohzc4p7-QHQ 06:34 — grupo GUARDRAILS"
  adapted: true
  risk: high
  vlaeg_phases: [A]
  triggers:
    - "escrever, corrigir ou revisar código (nível de risco >= 1)"
    - "teste vermelho, bug, comportamento inesperado"
    - "a correção pensada envolve cast, supressão, catch vazio, sleep ou retry cego"
  negative_triggers:
    - "mudança só de formatação"
    - "mudança só de documentação"
  produces: ["correção na causa raiz", "F-NNN quando a causa é externa", "bloco WORKAROUND contido quando a válvula de escape se aplica"]
  gates: ["G4", "G2"]
---

# Sem gambiarra

Gambiarra é qualquer mudança que faz o problema parar de se manifestar sem tratar por que ele
existe. O sintoma some enquanto a doença se espalha — uma falha adiada que rende juros.
**Corrija a origem, não o sinal.**

## O portão — antes de qualquer correção

```
1. Enuncie o problema e rastreie-o até a causa raiz.
2. A correção repara essa causa, ou só impede o sintoma de aparecer?
3. Estou calando um sinal, ou consertando uma origem?

Calando um sinal        → redesenhe a correção contra a causa raiz.
Causa raiz externa ou
genuinamente incorrigível → use a válvula de escape.
```

A correção está pronta quando **teria sido desnecessária se o código estivesse certo desde o
início** — e não precisa de cast, supressão, atraso nem catch vazio para passar.

## Os sete sinais

Cada linha é o compilador, o linter, o runtime ou o revisor dizendo algo verdadeiro. Conserte o
que ele aponta.

| Categoria | O sinal que silencia | Conserte a origem… |
|---|---|---|
| **TIPO** — `as`, `any`, `!`, `as unknown as` | O sistema de tipos achou o código errado | Tornando os tipos verdadeiros: corrija a definição, ou valide dado genuinamente desconhecido na fronteira (schema, type guard) |
| **LINT** — `eslint-disable`, `@ts-ignore`, `# noqa` inline | A análise estática achou um problema real | Consertando o que a regra apontou; se a regra é mesmo inadequada ao repo, desative-a na configuração, não na linha |
| **ENGOLIR** — catch vazio, `.catch(() => null)`, catch-e-default | Algo falhou e o código finge que não | Tratando cada erro: registre com contexto e relance, ou mapeie para um resultado tipado |
| **TEMPO** — `setTimeout`, `sleep`, retry cego | O código roda na ordem errada | Coordenando pelo evento real de prontidão; em teste, espere por condição, não pelo relógio |
| **PATCH** — mutação de protótipo, global ou interno de biblioteca | A API não faz o que o código precisa | Compondo por fora: wrapper, adapter ou o ponto de extensão oficial da biblioteca |
| **ESPALHAR** — `?.` e `??` em profundidade, cadeias de fallback | O dado é não confiável na origem | Validando uma vez na fronteira e confiando na forma daí em diante |
| **CLONE** — copia-e-ajusta de código parecido | Uma abstração não serve mas é forçada | Extraindo o padrão comum, ou escrevendo código de propósito específico |

**Quando qualquer categoria disparar, leia `references/workaround-catalog.md` integralmente antes
de escolher a correção** — 30 padrões nomeados (W-01…W-30), incluindo gambiarras de ambiente,
build, teste e arquitetura, além das sete acima.

## A válvula de escape

Nem toda causa raiz é sua para corrigir. A gambiarra é permitida **apenas** quando **todas** valem:

```
1. A causa raiz está em código externo que a equipe não controla.
2. A correção adequada depende de mudança upstream com prazo incerto.
3. O custo de não entregar excede a dívida contraída.
4. A gambiarra é isolada — não vaza para outro código.
```

Quando as quatro valem, contenha:

```
1. Marque: // GAMBIARRA: [motivo] — ver [link do registro]
2. Abra um registro rastreável para a remoção.
3. Adicione um teste que fixa o comportamento atual.
4. Adicione um teste-canário que FALHA quando a correção upstream chegar.
5. Defina data de revisão (máximo 90 dias).
```

Se qualquer condição falhar, corrija a causa raiz. Sem exceção.

Neste protocolo, usar a válvula de escape é um **finding obrigatório** (`F-NNN`) com nível de
autoridade `evidence`, citando qual das quatro condições justifica cada uma.

## Fundamentos

O princípio converge de Jidoka na Toyota, do quadrante de dívida de Fowler, do "bom gosto" de
Torvalds e da teoria das Janelas Quebradas — e toda desculpa para pulá-lo tem resposta conhecida.
Leia `references/rationalizations.md` quando a pressão de prazo estiver empurrando para a
gambiarra.

## Integração com o protocolo

- Vale a partir do **nível de risco 1**. Pressa não é exceção registrada.
- A correção só passa no gate **G4** com evidência: teste vermelho antes, verde depois.
- Se a causa raiz revelar uma armadilha reutilizável, proponha promoção via `knowledge-promotion` para `docs/gotchas/`.
- `deslop` roda depois: ele remove ruído estético; este guardrail remove dívida estrutural. Não são substituíveis.

## Critérios de conclusão

- [ ] A causa raiz está enunciada por escrito, separada do sintoma.
- [ ] A correção repara essa causa e dispensa cast, supressão, atraso e catch vazio.
- [ ] Existe teste que falhava antes e passa agora (ou justificativa registrada de por que nenhum teste é significativo).
- [ ] Toda gambiarra remanescente tem as quatro condições satisfeitas, os cinco itens de contenção e um `F-NNN`.

## Anti-patterns

"Depois eu arrumo" sem registro · desativar a regra de lint no arquivo inteiro em vez da
configuração · aumentar timeout até o teste passar · `try/except` amplo para "estabilizar" ·
marcar teste como skip para desbloquear a entrega · trocar a asserção por uma mais fraca ·
justificar gambiarra por prazo sem passar pela válvula de escape.
