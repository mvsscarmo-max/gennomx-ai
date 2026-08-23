# DECISIONS - GennomX AI

## D-001 - Runtime sem Supabase

**Data:** 2026-07-20
**Status:** ativa | **Autoridade:** approved-decision

PostgreSQL/pgvector na VPS é o banco alvo. Auth usa JWT local próprio e Platform Auth por flag.
Storage runtime usa MinIO/S3-compatible. Cloudflare R2 é futuro. Supabase permanece apenas em
registros e artefatos históricos de migração.

## D-002 - Platform Auth aditivo e por escopo

**Data:** 2026-07-20
**Status:** ativa | **Autoridade:** approved-decision

Com a flag desligada, somente JWT local e chave interna são aceitos pela API. Com a flag ligada,
RS256 da plataforma também é aceito após validação integral do contrato. `ai:admin` satisfaz os
scopes do módulo; papéis locais preservam o comportamento anterior.

## D-003 - MCP é uma fronteira de identidade separada

**Data:** 2026-07-20
**Status:** ativa | **Autoridade:** approved-decision

MCP mantém `X-MCP-Token`, clientes e scopes por ferramenta. Bearer/cookie administrativo não é
credencial MCP e não concede ferramentas administrativas.

## D-004 - DRY-7 limitado a dados literais da fixture CT.gov

**Data:** 2026-07-20
**Status:** ativa | **Autoridade:** approved-decision

O primeiro incremento projeta outcomes planejados, outcome measures e adverse events disponíveis.
Não infere eficácia ou safety. Valores negativos/inconclusivos e raw estruturado são preservados,
com evidência e idempotência. Ausência de resultados produz gaps.

## D-005 - INGEST-5 permanece sequencial

**Data:** 2026-07-20
**Status:** ativa | **Autoridade:** approved-decision

Somente o recorte local de DRY-7 avança por fixtures. ANVISA, normalização de indicações, resolução
de empresas e PMC continuam bloqueados até validação real do backbone PostgreSQL/MinIO/Celery.

## D-006 - Estado operacional em VLAEG 2.0

**Data:** 2026-07-20
**Status:** ativa | **Autoridade:** approved-decision

O estado vivo usa `CONTEXT`, `DECISIONS`, `TASKS`, `FINDINGS`, `PROGRESS` e `plans/`. O estado v1
foi movido sem exclusão para `archive/v1/`.

## D-007 — Adotar o Protocolo VLAEG AI Ready First 4.0.0

**Data:** 2026-08-21 | **Autor:** Marcus (T-207 / PLAN-024), executado por Cursor | **Status:** ativa | **Autoridade:** approved-decision
**Workstream:** WS-001 / PLAN-002 | **Nível de risco:** 3 | **Decisor humano:** true

**Contexto:** T-207 da raiz autorizou distribuir o AI Ready First 4.0.0 a esta aplicação em worktree própria.

**Decisão:** adotar o AI Ready First 4.0.0. O contrato de produto longo saiu de `AGENTS.md` para `docs/rules/contrato-operacional.md`. Estado VLAEG 2.0 global congelado em `docs/legacy/project_state-vlaeg2/`.

**Alternativas descartadas:** manter o AGENTS.md de 439 linhas como residente; copiar regra de gate para o bundle federado.

**Impacto:** `AGENTS.md`, `docs/ai-ready/`, `tools/`, `federation/protocol/`, estado local.

**Substitui/substituída por:** substitui D-006 quanto ao estado vivo; não revoga D-001…D-005.

## D-008 — Escape INFRA da RC desta WS (teto 25 arquivos)

**Data:** 2026-08-23 | **Autor:** Marcus (transcricao G14 desta sessao) | **Status:** ativa | **Autoridade:** approved-decision
**Workstream:** WS-002 / PLAN-003 | **Nivel de risco:** 3 | **Decisor humano:** true
**Prazo:** 2026-09-06

**Contexto:** o motor independente opencode/openai/gpt-5.6-sol existe nesta maquina. O pre-voo da RC recusou a janela por teto de 25 arquivos. Nao houve rodada de julgamento. Push origin continua bloqueado (main ja adiantada).

**Decisao:** destravar so a ausencia da RC para fechar WS-002. Nao destravar achado critico (nenhum foi produzido).

**Impacto:** G14 desta WS cita **Escape INFRA:** D-008.
