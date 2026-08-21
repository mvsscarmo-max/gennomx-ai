# Laço de correção

O que acontece entre encontrar e fechar. O laço é **governado**: o executor julga o tamanho da
correção **antes de tocar no código**, corrige só o que está seguramente dentro dos limites e
escala o resto com opções — porque um agente que remenda o produto no meio do QA para zerar os
próprios findings está otimizando o painel, não o produto.

Fronteira de fidelidade primeiro: correção **nunca** acontece dentro de uma sessão. A sessão
termina, os findings existem, e então o governador roda.

## O governador

Para cada finding `Falha` ou atrito afiado, julgue antes de editar. **Corrija automaticamente
apenas quando TODAS valerem:**

- **Pequena** — poucos arquivos, sem migração de schema ou dado, sem mudança de contrato de API.
- **Bem compreendida** — causa raiz identificada e enunciada, escrita separadamente do sintoma.
- **Baixo risco** — raio de alcance contido na superfície tocada; jornadas adjacentes improváveis de mudar.
- **Sem trade-off de produto** — o comportamento correto é inequívoco. Qualquer coisa que um product manager ou designer decidiria de outro jeito não é sua para decidir.

Falhou um teste → **Decisões para um Humano**. Quando a correção cresce além dos limites no meio
da edição: reverta por completo, devolva o finding para `Falha` e escale. Correção pela metade é
pior que bug aberto.

## Requisitos de correção automática

Toda correção automática embarca, sem negociação:

1. **Um teste de regressão que falhava antes e passa agora.** Quando nenhum teste automatizado é significativo (texto puro, puramente visual), vale um replay documentado: os passos exatos de refazer, a evidência antes/depois e o motivo declarado de nenhum teste se aplicar — mais um registro da dívida.
2. **Uma correção lógica por commit**, com a mensagem citando o id do bug.
3. **Causa raiz no arquivo do bug** — causa, commit e caminho do teste de regressão.
4. **Reteste** pelo protocolo abaixo antes de a linha virar `Corrigido`.

## Decisões para um Humano

Escalonamentos são findings **com recomendação**, registrados na seção do relatório:

```markdown
### <título do finding> (id do bug / atrito)
- O que está quebrado: <descrição pelo lado do usuário, caminho da evidência>
- Por que não foi corrigido automaticamente: <qual limite do governador falhou>
- Opções:
  1. <opção> — <trade-off>
  2. <opção> — <trade-off>
- Recomendação: <uma das opções, com o motivo>
```

A linha da matriz vira `Bloqueado (decisão humana)` — estado terminal desta rodada. Nunca é
requeueada em silêncio.

## Protocolo de reteste

Depois de qualquer correção:

1. Refaça a jornada impactada **do zero, em persona** — sessão nova, estado novo, entrada real. Não reaproveite a janela aberta.
2. Refaça as **jornadas adjacentes** — as que compartilham componente ou serviço com a mudança. Correção que quebra o vizinho é regressão que a matriz precisa pegar agora, não no próximo ciclo.
3. Passou: bug → `corrigido` (depois `verificado` sob a persona original), linha da matriz → `Corrigido`.
4. Falhou: reabra, reverta se a correção causou, escale se a segunda tentativa exigiria mais que o governador permite.

## Portão de saída

Antes do Status Final: **rode a suíte automatizada completa uma vez.** Matriz verde com suíte
vermelha não está pronta — alguma correção quebrou algo que as sessões não percorreram. O
resultado vai verbatim no relatório; suíte vermelha torna o Status Final "não pronto",
independentemente da matriz.

(A suíte estava verde no Passo 1; este portão pega o que **as correções desta rodada** mudaram.)

## Anti-patterns

Corrigir no meio da caminhada · corrigir sem prova de regressão · refatorar "já que estou aqui" ·
decidir questão de produto para zerar uma linha · retestar só a jornada corrigida · requeuear em
silêncio item bloqueado.
