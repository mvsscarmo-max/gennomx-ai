# CONTEXT - GennomX AI

**Atualizado:** 2026-07-20
**Protocolo:** VLAEG 2.0
**Plano ativo:** nenhum
**Ultimo plano concluido:** `plans/PLAN-001-platform-auth-dry7-reconciliacao.md`

## Estado atual

GennomX AI é infraestrutura proprietária de dados biomédicos, API, dashboard e MCP read-only.
Não gera relatórios finais. O estado v1 foi preservado em `archive/v1/`.

- Banco alvo: PostgreSQL/pgvector na VPS, roles segregadas, RLS e porta não pública.
- Auth administrativo: JWT local próprio; Platform Auth RS256 aditivo por flag.
- MCP: tokens e scopes próprios, sem substituição por sessão administrativa.
- Storage runtime: MinIO/S3-compatible em buckets exclusivos da AI.
- Storage futuro: Cloudflare R2, sem provisionamento.
- Supabase: histórico de migração, não runtime.
- Ingestão: DRY-1 a DRY-5 implementados localmente; validação real na VPS pendente.
- DRY-7: primeiro incremento CT.gov por fixtures implementado para endpoints, resultados e adverse events.
- DRY-6 e restante de INGEST-5: bloqueados até validação real do backbone.
- Gates locais: backend, frontend, E2E e auditorias de dependencias aprovados.

## Fronteiras

- Não executar deploy, ingestão real, provisionamento, acesso a produção ou operações com segredos.
- ANVISA, normalização de indicações, resolução de empresas e PMC não estão implementados.
- Sessão administrativa não autentica MCP.
- R2 não integra o runtime nesta fase.

## Próximo passo operacional

Em janela autorizada futura: validar aplicação e PostgreSQL na rede privada da VPS, executar
handshake, preflight MinIO, dry-runs limitados e revisar cobertura antes de qualquer smoke-run real.
