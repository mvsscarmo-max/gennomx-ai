<!-- validate-links: illustrative-paths -->
# Arquivo VLAEG v1 - Platform Admin Auth e storage segregado

**Data:** 2026-07-10  
**Escopo:** GennomX AI como modulo `/ai` da Plataforma GennomX  
**Plano raiz relacionado:** `../project_state/plans/PLAN-008-plataforma-admin-auth-storage.md`  
**Planos relacionados:** `project_state/plano_remocao_supabase_jwt_minio.md`, `project_state/plano_correcao_issues_ingestao_dry_run.md`

## Objetivo

Adaptar o dashboard administrativo da GennomX AI para aceitar autenticacao administrativa comum da Plataforma GennomX, preservando MCP read-only, tokens MCP por cliente host, PostgreSQL/pgvector com roles/RLS e storage Cloudflare R2 segregado para dados biomedicos.

## Estado atual

- Banco principal: PostgreSQL/pgvector na VPS, com roles `gennomx_app`, `gennomx_worker`, `gennomx_migrator`, `gennomx_readonly`.
- Auth/Storage estao em migracao para JWT proprio + Cloudflare R2 por outra trilha.
- Codigo recente ja referencia `AUTH_JWT_*`; o runtime atual ainda usa MinIO e sera migrado para R2 no P-5.
- MCP usa tokens proprios (`MCP_TOKEN_CHATGPT`, `MCP_TOKEN_CLAUDE`, `MCP_TOKEN_PRIVATE_AGENT`) e scopes por ferramenta.
- Ingestao e curadoria exigem rastreabilidade e auditoria.

## Decisao local

A sessao administrativa do dashboard `/ai` pode aceitar token da Plataforma GennomX, mas os tokens MCP permanecem independentes. Autorizacao de ingestao, seguranca e curadoria deve ser por scopes `ai:*`, nao por role admin generica.

## Fases locais

### AI-P0 - Reconciliar com a trilha JWT + Cloudflare R2

- ler e respeitar `project_state/plano_remocao_supabase_jwt_minio.md`;
- nao desfazer o JWT local nem antecipar a migracao de storage para R2;
- confirmar se o issuer local `gennomx-ai` ainda precisa coexistir com `gennomx-platform` durante transicao;
- listar cookies/frontend auth e endpoints `/api/v1/auth/*`.

### AI-P1 - Validacao de token de plataforma

- suportar `iss=gennomx-platform`, `aud=gennomx-admin` para dashboard;
- exigir `apps` contendo `ai`;
- mapear scopes:
  - `ai:read`;
  - `ai:curate`;
  - `ai:ingest:dry_run`;
  - `ai:ingest:run`;
  - `ai:security`;
  - `ai:admin`.
- manter `AUTH_JWT_ISSUER=gennomx-ai` como fallback local se necessario por feature flag;
- testes negativos para audience/issuer/scope.

### AI-P2 - Separar dashboard admin de MCP

- MCP externo continua autenticado por tokens MCP especificos;
- token admin nao vira token MCP;
- MCP nao ganha ferramentas administrativas;
- logs MCP continuam registrando cliente host e ferramenta.

### AI-P3 - Storage biomedico segregado

- buckets da AI permanecem proprios:
  - `gennomx-ai-raw`;
  - `gennomx-ai-processed`;
  - `gennomx-ai-evidence`.
- credencial do worker AI nao deve ler buckets de Carteiras ou Maquina;
- raw payload deve permanecer imutavel por hash;
- preflight de storage deve bloquear ingestao real se Cloudflare R2 falhar, mas permitir dry-run.

### AI-P4 - Autorizacao de ingestao/curadoria

- integrar com o plano dry-run:
  - `ai:ingest:dry_run` para dry-run;
  - `ai:ingest:run` para smoke-run real;
  - `ai:curate` para correcoes humanas;
  - `ai:security` para telas/logs sensiveis;
  - `ai:admin` para configuracao restrita.
- manter four-eyes nas correcoes manuais;
- nao relaxar RLS nem roles de banco.

### AI-P5 - Validacao

- testes de `auth/dependencies.py` com issuer local e issuer plataforma;
- testes negativos de scope;
- testes MCP garantindo independencia de tokens;
- testes R2/storage se alterado;
- backend pytest, frontend lint/typecheck/build conforme ambiente.

## Riscos

- confundir sessao admin com cliente MCP;
- permitir ingestao real sem scope especifico;
- compartilhar credenciais R2 com outros modulos;
- divergencia entre docs legadas Supabase, runtime MinIO transitorio e alvo R2.
