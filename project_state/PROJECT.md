# PROJECT.md — GennomX AI

O que é durável neste projeto. O que está acontecendo agora vive em `WORKSTREAMS.md` e nos
`STATE.md` de cada workstream. **Este arquivo não contém tarefa nem status volátil.**

## Objetivo

Entregar dados estruturados, evidências, contexto e ferramentas MCP de consulta em life
sciences. A geração final de relatórios fica nos modelos host externos.

Critério de sucesso: ingestão rastreável, MCP read-only no MVP, gates backend/frontend verdes,
sem dependência de resposta generativa interna como produto.

## Usuários

- **Operador interno** — dashboard, correção e auditoria.
- **Modelos host** — consultam via MCP com token e scope próprios.

## Escopo

**Incluído:** PostgreSQL/pgvector, pipelines de ingestão, MCP, dashboard, API interna, Platform
Auth por flag, MinIO/S3-compatible.

**Fora de escopo:** chatbot como produto; relatório final interno; acesso SQL do host; R2 no
runtime atual; ANVISA/PMC até validação do backbone.

## Stack

Backend Python (pytest, Ruff, mypy). Frontend Next.js. PostgreSQL/pgvector. Celery no backbone.
Auth JWT local + Platform Auth RS256 por flag.

## Arquitetura

Infraestrutura de dados com MCP semântico. Contrato de produto em
`docs/rules/contrato-operacional.md`. Visão adicional em `docs/` e `architecture/`.

## Regras críticas

1. MCP não é proxy de SQL. Token, cliente e scope por ferramenta.
2. Bearer/cookie administrativo não autentica MCP.
3. Nenhuma saída de LLM grava direto no banco; persistência exige schema, evidência e score.
4. Dado bruto, processado e curado permanecem separados; conflito não se sobrescreve.
5. Não copiar marca, base ou claims da Gosset AI.
6. Sem deploy, ingestão real ou provisionamento sem autorização humana.

## Comandos

```bash
python tools/validate.py
cd backend && python -m pytest tests/unit -q
cd frontend && npm run lint && npm run typecheck && npm run build
```

**Pré-requisitos:** Python do backend e Node do frontend instalados. Validação na VPS é gate
humano separado.

## Classificação de dados

Aplicação com dado biomédico e competitivo. Segredos só em ambiente. Política de captura:
`.agents/policy/capture-policy.yaml`.

## Fonte da verdade

- Banco operacional: PostgreSQL/pgvector na VPS (alvo); Supabase é histórico
- Storage runtime: MinIO/S3-compatible; R2 é futuro, não runtime
- Bundle federado: `federation/protocol/` com lock ao lado
- Contrato de produto: `docs/rules/contrato-operacional.md`
- Estado operacional: `project_state/WORKSTREAMS.md` e `workstreams/<WS>/STATE.md`
- `CONTEXT.md` / `TASKS.md` / `PROGRESS.md` estão congelados em `docs/legacy/project_state-vlaeg2/`

## Fatos canônicos

| Fato | Vigente | Fixado por | Aposentado |
|---|---|---|---|
| Protocolo de agente | AI Ready First 4.0.0 | D-007 | VLAEG 2.0 |
| Bundle federado | 1.0.0 digest `sha256:5703c899…` | T-207 / lock local | — |
| Banco alvo | PostgreSQL/pgvector | D-001 | Supabase como runtime |
| MCP | identidade separada | D-003 | sessão admin como credencial MCP |

## Ponteiros

| Preciso de | Vá para |
|---|---|
| Como trabalhar aqui | `AGENTS.md` |
| Contrato de produto | `docs/rules/contrato-operacional.md` |
| Estado atual | `project_state/WORKSTREAMS.md` |
| Regra normativa do protocolo | `docs/ai-ready/protocol.md` |
| Decisões e descobertas | `project_state/DECISIONS.md`, `project_state/FINDINGS.md` |
| Estado VLAEG 2.0 congelado | `docs/legacy/project_state-vlaeg2/` |
