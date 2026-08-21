<!-- validate-links: illustrative-paths -->
# Arquivo VLAEG v1 - plano de remocao da Supabase

**Data:** 2026-07-09  
**Solicitante:** Marcus  
**Status:** aprovado para implementacao  
**Escopo:** GennomX AI - remover dependencias de Supabase fora do banco ja cortado  
**Motivacao:** o banco principal ja foi migrado para PostgreSQL da VPS; agora a meta e eliminar Auth/Storage/SDK Supabase do runtime e das interfaces do app.

## 1. Objetivo

Substituir a pilha remanescente da Supabase por componentes proprios:

- Auth: JWT proprio emitido pelo backend FastAPI.
- Storage: Cloudflare R2 por API S3-compatible para raw payload e artefatos.
- Frontend: leitura de cookie JWT propria e middleware local.
- Backend: validacao de JWT sem dependencias de Supabase Auth/JWKS.

## 2. Arquitetura alvo

### 2.1 Auth

- Login por e-mail/senha de um administrador interno.
- Credenciais iniciais via variaveis de ambiente:
  - `AUTH_ADMIN_EMAIL`
  - `AUTH_ADMIN_PASSWORD_HASH`
  - `AUTH_JWT_SECRET`
- Backend assina JWT HS256 com `sub`, `email`, `role`, `iat`, `exp`.
- Frontend grava o token em cookie do proprio dominio e o middleware valida a assinatura localmente.

### 2.2 Storage

- Cloudflare R2 e provisionado fora da VPS, com credenciais de menor privilegio por modulo.
- Buckets da AI:
  - `gennomx-ai-raw`
  - `gennomx-ai-processed`
  - `gennomx-ai-evidence`
- `workers/storage/raw_payload.py` passa a usar S3-compatible API.

## 3. Fora de escopo

- Auth social.
- SSO/OIDC/SAML.
- Multi-tenant com varios usuarios agora.
- Migrar o banco novamente.
- Trocar o MCP ou o dashboard.

## 4. Etapas

| Etapa | Escopo | Estado |
|---|---|---|
| SUPA-0 | Mapear usos remanescentes de Supabase no backend/frontend/docs | Concluida na analise inicial |
| SUPA-1 | Implementar JWT proprio no backend e middleware/frontend | A iniciar |
| SUPA-2 | Substituir raw payload por Cloudflare R2/S3-compatible | A iniciar |
| SUPA-3 | Remover `@supabase/*`, `supabase` Python e envs antigas | A iniciar |
| SUPA-4 | Atualizar docs, changelog, progress e runbook | A iniciar |
| SUPA-5 | Validar login, rotas protegidas, upload raw e deploy | A iniciar |

## 5. Riscos

- Cookie JWT em frontend precisa ser tratado como dado sensivel.
- Cloudflare R2 requer provisionamento externo de buckets, policies e variaveis seguras.
- Qualquer referencia residual a `SUPABASE_*` quebra o deploy se nao for removida.

## 6. Criterios de aceite

- Nenhum caminho de runtime depende de Supabase.
- Login e middleware funcionam com JWT proprio.
- Raw payload e gravado em Cloudflare R2.
- Build/testes passam sem dependencias Supabase no runtime.
- Docs e estado do projeto refletem a nova arquitetura.
