# Protocolo de sessão

## O laço

Para cada passo da jornada, sempre nesta ordem:

**Entrar** — chegue à superfície pelo caminho que a persona usaria. Não pule para a URL interna
nem restaure estado por atalho de desenvolvedor. Se a persona chegaria por e-mail, comece pelo
e-mail.

**Agir** — execute o verbo do passo com os dados da persona. Dado realista, não `teste123`.

**Verificar** — confirme o observável esperado. `Passa` exige as quatro condições:

1. o observável esperado foi **visto**;
2. confirmado por um **caminho de leitura independente** (recarregar a lista, abrir outra tela, consultar via outra superfície pública);
3. **sobreviveu a um recarregamento** — UI otimista some no refresh;
4. **evidência capturada**.

Três das quatro não é `Passa`. É `Atrito` ou `Falha`, conforme o que faltou.

**Capturar** — registre a evidência em `qa/reports/<data>-<escopo>.md`, com caminho de arquivo
quando houver captura de tela ou log.

## Padrão de evidência

| Situação | Evidência mínima |
|---|---|
| Checkpoint da jornada | descrição do observável + timestamp |
| Divergência do esperado | descrição + captura ou log + passos de reprodução |
| Bloqueio | pré-requisito exato ausente |
| Tentado-e-limpo (borda) | o que foi tentado e o que aconteceu |

Evidência ausente transforma o veredito em hipótese. Hipótese não fecha linha de matriz.

## Fidelidade de persona

Guardrails que definem "interface pública":

- **Permitido:** navegador, app, CLI que o usuário instala, API pública documentada, e-mail, arquivo exportado.
- **Não permitido para decidir veredito:** console do navegador, acesso direto ao banco, endpoint interno, leitura do código-fonte para saber o que deveria acontecer, flag de desenvolvedor.

Ler o código para **entender** um bug encontrado é legítimo depois de o veredito ter sido dado
pela superfície. Ler o código para **decidir** o veredito não é.

## Travamento é finding

Quando o fluxo trava, a resposta é registrar — nunca cutucar até destravar. O usuário real não
tem esse recurso, e "funcionou depois que eu insisti" descreve o produto com precisão. Sequência:
encerre a sessão, registre o travamento com evidência, tente uma vez a partir de sessão limpa,
depois marque bloqueado.

## Estados de veredito

| Estado | Significa |
|---|---|
| `Pendente` | ainda não percorrido |
| `Passa` | as quatro condições de prova satisfeitas |
| `Atrito` | funciona, mas a persona hesita, se confunde ou reclama |
| `Falha` | não faz o que a jornada exige |
| `Bloqueado (precisa verificação humana)` | trecho que só um humano completa |
| `Bloqueado (decisão humana)` | escalado pelo governador do laço de correção |
| `Pulado` | cortado por caixa de tempo, com motivo declarado |

`Bloqueado` em qualquer variante é **terminal para a rodada**: espera por uma pessoa, visivelmente.
