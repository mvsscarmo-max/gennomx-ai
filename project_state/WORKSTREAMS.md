# Workstreams

Índice das linhas de trabalho. Detalhe vive em `workstreams/<WS>/STATE.md` — este arquivo é o
ponteiro, **não o conteúdo**.

**Próximo ID:** WS-004 · IDs nunca são reutilizados, nem os de workstreams canceladas.

## Ativas

| ID | Título | Objetivo | Risco | Fase | Atualizada | Executor |
|---|---|---|---|---|---|---|
| [WS-003](workstreams/WS-003-onda2-ci-pip-audit/STATE.md) | Onda 2: CI verde apos pip-audit | O origin/main tem Security Scan verde com aiohttp e cryptography acima das CVEs do run 32669664058 | 3 | G | 2026-09-18 | cursor-grok-4.6 |

## Propostas

_nenhuma_

## Pausadas

_nenhuma_

## Bloqueadas

_nenhuma_

## Concluídas

| ID | Título | Objetivo | Risco | Fase | Atualizada | Executor |
|---|---|---|---|---|---|---|
| [WS-002](workstreams/WS-002-overlay-ci-f14-segredos/STATE.md) | Overlay 1.1.0, CI e classificacao F1.4 | A GennomX AI tem overlay 1.1.0 com lock sourceCommit, CI ampla com action composta de install/cache sem perder paralelismo, e alertas F1.4 classificados sem ler arquivos de ambiente ignorados. | 3 | G | 2026-08-23 | cursor-grok-4.6 |
| [WS-001](workstreams/WS-001-adocao-do-ai-ready-first-4-0/STATE.md) | Adocao do AI Ready First 4.0 | A GennomX AI opera sob AI Ready First 4.0.0 com AGENTS.md residente enxuto e validadores verdes | 3 | — | 2026-08-21 | cursor-grok-4.6 |

## Canceladas

_nenhuma_

---

**Regras**

- Workstream ativa exige objetivo verificável, plano em execução e ao menos uma tarefa em andamento.
- Diretório sem linha aqui, ou linha sem diretório, é workstream órfã — o validador acusa, e a reconciliação vem antes de qualquer outro trabalho.
- Workstream concluída ou cancelada **permanece** no repositório. Fechada não é apagada.
- Uma workstream por linha de trabalho independente. Investigação paralela abre a sua.
- A linha do índice e o diretório nascem na **mesma passagem**, ou nenhuma das duas.

<!-- Formato da linha, quando houver workstreams:

| ID | Título | Objetivo | Risco | Fase | Atualizada | Executor |
|---|---|---|---|---|---|---|
| [WS-NNN](workstreams/WS-NNN-<slug>/STATE.md) | <titulo> | <objetivo verificavel> | <0-5> | <V/L/A/E/G> | AAAA-MM-DD | <agente> |
-->
