# Auditorias

Índice das auditorias e diagnósticos. Detalhe vive no documento apontado — este arquivo é o
ponteiro, **não o conteúdo**. IDs nunca são reutilizados.

**Próximo ID:** AUD-002

Vocabulário de status (`docs/ai-ready/state-currency.md`): `vigente` · `parcialmente-endereçada` ·
`endereçada` · `superada-por AUD-NNN` · `histórica`.

## Registradas

| ID | Data | Tipo | Escopo | Status | Caminho | Levou a |
|---|---|---|---|---|---|---|
| AUD-001 | 2026-08-21 | revisao-de-ciclo | WS-001 / T-012 | vigente | [AUD-001-adocao-do-ai-ready-first-4-0.md](../audits/AUD-001-adocao-do-ai-ready-first-4-0.md) | R-01…R-04 |

## Regras

- Auditoria nova nasce em `audits/AUD-NNN-<slug>.md` e ganha linha aqui na **mesma passagem**.
- O ID é a identidade; o **caminho é campo do índice** — auditoria antiga pode manter caminho histórico.
- O status no frontmatter do documento e nesta tabela **devem coincidir**; divergência é erro.
- Conteúdo de auditoria não entra no briefing residente — só este índice.

<!-- Formato da linha:

| ID | Data | Tipo | Escopo | Status | Caminho | Levou a |
|---|---|---|---|---|---|---|
| AUD-001 | AAAA-MM-DD | <parecer externo \| auditoria interna \| diagnóstico \| revisao-de-ciclo> | <escopo> | vigente | [<arquivo>](../audits/<arquivo>) | <PLAN-NNN / WS-NNN / F-NNN> |
-->
