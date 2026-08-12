# DECISIONS - GennomX AI

## D-001 - Runtime sem Supabase

**Data:** 2026-07-20
**Status:** ativa

PostgreSQL/pgvector na VPS é o banco alvo. Auth usa JWT local próprio e Platform Auth por flag.
Storage runtime usa MinIO/S3-compatible. Cloudflare R2 é futuro. Supabase permanece apenas em
registros e artefatos históricos de migração.

## D-002 - Platform Auth aditivo e por escopo

**Data:** 2026-07-20
**Status:** ativa

Com a flag desligada, somente JWT local e chave interna são aceitos pela API. Com a flag ligada,
RS256 da plataforma também é aceito após validação integral do contrato. `ai:admin` satisfaz os
scopes do módulo; papéis locais preservam o comportamento anterior.

## D-003 - MCP é uma fronteira de identidade separada

**Data:** 2026-07-20
**Status:** ativa

MCP mantém `X-MCP-Token`, clientes e scopes por ferramenta. Bearer/cookie administrativo não é
credencial MCP e não concede ferramentas administrativas.

## D-004 - DRY-7 limitado a dados literais da fixture CT.gov

**Data:** 2026-07-20
**Status:** ativa

O primeiro incremento projeta outcomes planejados, outcome measures e adverse events disponíveis.
Não infere eficácia ou safety. Valores negativos/inconclusivos e raw estruturado são preservados,
com evidência e idempotência. Ausência de resultados produz gaps.

## D-005 - INGEST-5 permanece sequencial

**Data:** 2026-07-20
**Status:** ativa

Somente o recorte local de DRY-7 avança por fixtures. ANVISA, normalização de indicações, resolução
de empresas e PMC continuam bloqueados até validação real do backbone PostgreSQL/MinIO/Celery.

## D-006 - Estado operacional em VLAEG 2.0

**Data:** 2026-07-20
**Status:** ativa

O estado vivo usa `CONTEXT`, `DECISIONS`, `TASKS`, `FINDINGS`, `PROGRESS` e `plans/`. O estado v1
foi movido sem exclusão para `archive/v1/`.
