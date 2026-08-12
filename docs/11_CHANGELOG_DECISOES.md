## 2026-07-20 - Platform Auth, DRY-7, Supabase reconciliada e VLAEG 2.0

**Area:** Segurança / Ingestão / Dados / Documentação

**Decisão:** concluir AI-P1/P2/P4 no backend com Platform Auth RS256 aditivo por flag e scopes
`ai:*`, sem alterar o autenticador MCP; implementar apenas o primeiro incremento DRY-7 do
ClinicalTrials.gov por fixtures; manter o restante de INGEST-5 bloqueado; consolidar PostgreSQL VPS,
JWT próprio e MinIO como runtime, R2 como futuro e Supabase como histórico; migrar o estado do
projeto para VLAEG 2.0 preservando v1 em arquivo.

**Implementação:** `CurrentUser` normaliza origem/subject/tenant/scopes; rotas de leitura,
curadoria, dry-run, ingestão real, segurança e administração usam scopes específicos. O parser
CT.gov cobre outcomes planejados, outcome measures e adverse events; projeções idempotentes
referenciam evidência e preservam literais negativos/inconclusivos. `get_trial_results` retorna
resultados, adverse events, evidências e gaps. SUPA-4 foi reconciliada com o código real.

**Limites:** nenhum deploy, ingestão real, provisionamento R2, acesso a produção ou segredo.
ANVISA, normalização de indicações, resolução de empresas, PMC e DRY-6 continuam bloqueados até
validação real do backbone na VPS.

**Status:** implementada localmente; validação ambiental da VPS permanece pendente.

> Ponteiros `project_state/*.md` em entradas anteriores a esta data são históricos. O estado v1
> correspondente está em `project_state/archive/v1/`; o estado vivo usa VLAEG 2.0.

**Validação local final:** pytest `282 passed, 1 skipped`; 7 E2E; Ruff, mypy, Bandit, ESLint,
TypeScript, build Next.js, verificacao de base path e auditorias Python/npm aprovados. O lock Python
foi reconciliado sem dependencias Supabase/PyPDF2 e com MCP `>=1.28.1`.

---

## 2026-07-10 - Plano local: Platform Auth/Storage para GennomX AI

**Area:** Seguranca / Plataforma / MCP / Storage

**Decisao:** GennomX AI podera aceitar auth administrativo comum da Plataforma GennomX no dashboard, mas tokens MCP, roles PostgreSQL/RLS e buckets MinIO da AI permanecem segregados. Autorizacao administrativa deve ser por scopes `ai:*`, nao por role global implicita.

**Plano local:** `project_state/plano_platform_admin_auth_storage.md`.

**Status:** registrado; implementacao pendente.

---## 2026-07-10 - Plano aprovado: correcao dos issues de ingestao com dry-run

**Area:** Ingestao / Data warehouse / Operacao / Governanca

**Decisao:** corrigir os issues da ativacao operacional da ingestao antes de habilitar recorrencia ampla, incluindo `dry_run` real nas tasks dos seis conectores implementados, ativacao auditavel de `data_sources`, disparo admin controlado com `max_records`, preflight de storage/env, camada de cobertura/qualidade do warehouse e agendamento posterior das tasks de pos-processamento.

**Motivo:** o codigo ja possui seis conectores, tasks Celery e `beat_schedule`, mas o banco esta em estado bootstrap e a primeira ingestao real precisa de freios operacionais. O dry-run reduz risco antes de escrita em entidades, raw storage, evidencias e cursores incrementais. A cobertura do warehouse evita que a IA Host ou o dashboard superestimem maturidade de dados ainda vazios/parciais.

**Fronteira com outra trilha:** Marcus informou que a substituicao de Supabase por JWT proprio + MinIO/S3-compatible ja esta sendo tocada por outro agente. Esta decisao nao autoriza remover Supabase, implementar JWT proprio ou implementar MinIO nesta trilha; a correcao deve integrar-se por contrato com o provider de storage/auth que estiver ativo.

**Plano canonico:** `project_state/plano_correcao_issues_ingestao_dry_run.md`.

**Status:** aprovado e registrado; implementacao ainda nao iniciada.

---
## 2026-07-09 - Cutover VPS autorizado para ingestão + plano operacional + compose de deploy da aplicação

**Area:** Banco de dados / Infraestrutura / Ingestão / Operação

**Decisão:** Marcus autorizou o cutover do banco principal para o PostgreSQL da VPS (`gennomx-ai-postgres-ready`) para fins de ingestão e operacionalização do data warehouse proprietário. A ingestão recorrente deve acontecer contra a VPS, não mais contra a Supabase. Supabase Auth/JWKS e Supabase Storage permanecem ativos nesta fase.

**Implementação:** nesta sessão foi produzido o plano operacional de ingestão recorrente (`project_state/plano_ingestao_fase_operacional.md`) baseado no estado real do código, e o compose de deploy da aplicação na VPS (`infra/docker-compose.vps-app.yml`) que sobe Redis + worker + beat (+ API sob profile `api`) conectados à rede Docker interna `gennomx-ai-postgres-ready-private` do Postgres, sem publicar portas no host. O diagnóstico confirmou que os 6 conectores P1 já estão implementados, registrados no `handshake.py`, com tasks Celery e `beat_schedule` existentes; o backlog é majoritariamente operacional (deploy/env/rede/Redis/Storage Supabase), não de implementação de conectores. Lacunas P1 mapeadas para a Onda 2: parser granular de `endpoints`/`trial_results`/`adverse_events` a partir de CT.gov `resultsSection`; ANVISA; normalizador de indicações; entity resolution de empresas; PMC full-text.

**Validação:** teste unitário estendido em `backend/tests/unit/test_postgres_vps_artifacts.py` aprovado (trava contratos do novo compose: sem `ports`, rede externa do Postgres, rede interna app, `--concurrency=1` no worker, `beat` command, API sob profile `api`). Probe efêmero `gennomx-ai-net-probe` confirmou resolução DNS do host `gennomx-ai-postgres-ready-postgres-1` na rede interna antes de ser removido.

**Segurança:** nenhuma porta publica 5432 ou 8000 publicamente; roles `gennomx_app`/`gennomx_worker`/`gennomx_migrator`/`gennomx_readonly` sem superuser/BYPASSRLS; Supabase Auth/JWKS/Storage não removidos. Achado operacional: `docker compose config` interpolou `.env` local e expôs segredos no stdout durante validação de sintaxe — valores não registrados em arquivo; recomenda-se preferir `docker compose config --no-interpolate` ou validação por teste unitário, e avaliar rotação das chaves expostas antes de produção.

**Estado:** plano + artefatos de deploy prontos; execução efetiva do runbook (copiar código para a VPS, `.env` staging, handshake, smoke-run incremental, up beat, monitorar 24-72h) pendente em ambiente com rede de saída e SSH à VPS. Cutover produtivo com `ENVIRONMENT=production` (exige `rediss://` e validações de `config.py`) fica após a primeira rodada em staging validada.

---

## 2026-07-09 - Inventário real Supabase via MCP e decisão de dispensar pg_dump/restore em staging (segunda sessão)

**Area:** Banco de dados / Infraestrutura / Operação

**Implementação:** nesta sessão o namespace Supabase tornou-se disponível. Projeto `qfanrziwepkqkgtvfrdt` foi restaurado de `INACTIVE` para `ACTIVE_HEALTHY` e o inventário real foi coletado via `supabase_execute_sql` (read-only):

- PostgreSQL `17.6`; banco 12 MB.
- `alembic_version = 0005` (alvo VPS em `0006`).
- Extensões: `pg_trgm=1.6`, `pgcrypto=1.3`, `uuid-ossp=1.1`, `vector=0.8.0` (alvo 0.8.1), `pg_stat_statements=1.11`, `supabase_vault=0.3.1`, `plpgsql=1.0`.
- 28 tabelas em `public`; 27 com RLS; 60 policies. Todas as 28 owners são `gennomx_migrator`.
- Roles gennomx_* com `rolsuper=false`/`rolbypassrls=false` confirmadas.
- Schemas/roles Supabase-specific identificados a NÃO migrar: schemas `auth`, `graphql`, `graphql_public`, `realtime`, `storage`, `vault`, `extensions`; roles `anon`, `authenticated`, `service_role` (BYPASSRLS), `supabase_admin` (superuser/BYPASSRLS), `supabase_auth_admin`, `supabase_storage_admin`.
- Contagens críticas: `data_sources=8` (todas `connector_status=inactive`, `is_enabled=false`, `last_successful_run=NULL`, `last_failed_run=NULL`); `retention_policies=5`; demais 26 tabelas = 0 registros.

**Decisão operacional:** `pg_dump --data-only`/`pg_restore` fica **dispensável** em staging porque o banco Supabase contém apenas seeds de `data_sources`/`retention_policies` já reproduzidos no alvo pelas próprias migrações Alembic (`0001` + `0004`, ambas com `ON CONFLICT DO NOTHING`). Persistir em `pg_dump` acrescentaria risco operacional (URL direta Supabase com DNS falho localmente, manipulação de credenciais) sem benefício. O alvo VPS em `0006` já contém funcionalmente o mesmo estado de dados; a comparação é conceitual e dispensa `tools/compare_postgres_migration.py`.

**Limitações:** UUIDs de `data_sources` diferem entre origem e alvo (aleatórios por execução da migração); irrelevante porque o app referencia por `slug`. Validação da aplicação (backend/pytest) contra VPS DB não foi executada nesta sessão — VPS Postgres em rede Docker interna (`gennomx-ai-postgres-ready-private`) não é alcançável desta máquina; exigirá backend em staging on-VPS ou VPN/tunnel.

**Segurança:** nenhuma remoção de Supabase Auth/JWKS/Storage, nenhum uso de `postgres`/service_role/superuser como conexão de aplicação, nenhuma exposição pública de 5432, nenhum relaxamento de RLS. `VPS_getProjectContents` não foi inspecionada para evitar expor credenciais nesta sessão. Inventário não persistido em artefato `supabase-inventory.json`.

**Estado:** staging de dados conceitualmente concluído pela paridade de seeds; cutover produtivo permanece não executado, dependente de validação on-VPS e aprovação explícita do Marcus.

---

## 2026-07-09 - MCP Supabase corrigido via OAuth

**Area:** Operacao / Ferramentas / Banco de dados

**Implementacao:** corrigida a configuracao local do MCP Supabase para continuidade da migracao banco-only. No Codex, `codex mcp login supabase` concluiu via OAuth e a entrada `supabase` deixou de depender de `SUPABASE_ACCESS_TOKEN`, passando a `auth_status=o_auth`. No OpenCode, a entrada ativa foi trocada de `mcp-server-supabase` local sem token para o MCP remoto oficial e `opencode mcp auth supabase` concluiu.

**Validacao:** `codex mcp list --json` mostra `supabase` com OAuth e sem `bearer_token_env_var`; `opencode mcp auth list` mostra `supabase authenticated`; `opencode mcp list` mostra `supabase connected`.

**Limite remanescente:** a sessao atual do agente nao injeta ferramentas MCP novas dinamicamente. O inventario real Supabase deve ser retomado em nova sessao Codex/OpenCode ja carregada com o namespace Supabase. A URL direta Supabase local continua indisponivel; nao executar dump/restore nem cutover produtivo sem inventario/validacao segura.

---

## 2026-07-09 - Alembic head aplicado no PostgreSQL VPS staging

**Area:** Banco de dados / Infraestrutura / Segurança / Operação

**Implementação:** aplicado Alembic `head` no PostgreSQL VPS staging `gennomx-ai-postgres-ready` sem publicar `5432`. Como a API Hostinger limita `content`/`environment` a 8192 caracteres e não há imagem/remote do backend, o SQL offline Alembic foi compactado, dividido em dois chunks e executado por projeto Docker temporário conectado à rede interna `gennomx-ai-postgres-ready-private`.

**Validação:** alvo em `alembic_version=0006`; extensões `pg_trgm=1.6`, `pgcrypto=1.3`, `uuid-ossp=1.1`, `vector=0.8.1`; roles `gennomx_app`, `gennomx_migrator`, `gennomx_readonly`, `gennomx_worker` com `rolsuper=false` e `rolbypassrls=false`; 27 tabelas com RLS; 60 policies; 29 tabelas públicas; `data_sources=8`. Grants pós-migração foram reaplicados, incluindo inserts de auditoria para `gennomx_app`.

**Bloqueio remanescente:** inventário real Supabase, dump/restore staging e comparação origem/alvo não foram executados nesta rodada. O MCP Supabase foi corrigido/autenticado posteriormente via OAuth, mas exige nova sessão para carregar ferramentas; a URL direta Supabase local falhou DNS e o pooler configurado rejeitou role/tenant.

**Segurança:** nenhuma remoção de Supabase Auth/JWKS/Storage, nenhuma mudança no frontend, nenhuma exposição pública de PostgreSQL, nenhum uso de `postgres`/superuser como conexão de aplicação e nenhum relaxamento de RLS. A inspeção Hostinger revelou que `getProjectContents` retorna variáveis de ambiente sensíveis; respostas dessa API devem ser tratadas como sensíveis e rotação deve ser avaliada antes de produção.

**Status:** schema staging em head; migração de dados bloqueada por acesso Supabase.

---

## 2026-07-09 - Limpeza VPS e bloqueio operacional do Alembic staging

**Area:** Banco de dados / Infraestrutura / Segurança / Operação

**Implementação:** após aprovação explícita, removidos os projetos intermediários de bootstrap e o projeto legado `postgresql-spko` da VPS. A listagem final da VPS mantém apenas `gennomx-ai-postgres-ready` e `traefik`; o banco staging final continua `healthy`, com bootstrap concluído e sem porta PostgreSQL publicada.

**Bloqueio:** Alembic `head` ainda não foi aplicado ao alvo. Foi gerado SQL offline localmente, mas a tentativa de aplicar via job temporário Hostinger esbarrou no limite de 8192 caracteres do campo `environment`. Sem remoto Git configurado e sem imagem publicada do backend/migrations, falta um caminho reprodutível para executar `alembic upgrade head` dentro da rede Docker interna.

**Supabase:** o MCP Supabase global ainda não aparece na sessão atual; a mudança de configuração requer reinício do OpenCode. Inventário real, dump/restore e comparação seguem pendentes.

**Status:** limpeza/provisionamento concluídos; migrations e migração de dados pendentes.

---

## 2026-07-09 - Provisionamento staging PostgreSQL/pgvector na Hostinger VPS

**Area:** Banco de dados / Infraestrutura / Seguranca / Operacao

**Implementacao:** via MCP Hostinger VPS, criada a primeira stack staging funcional de PostgreSQL/pgvector para a migração banco-only. A stack final válida é `gennomx-ai-postgres-ready`, rodando em rede Docker interna, sem porta publicada, com TLS interno e bootstrap concluído de extensões/roles.

**Seguranca:** criado firewall Hostinger `gennomx-ai-vps-public-ingress` (`325948`) e associado à VPS `1817951`, permitindo entrada somente em SSH/22, HTTP/80, HTTPS/443 e ICMP. Isso mitiga um achado crítico: projeto pré-existente `postgresql-spko` publicava PostgreSQL no host (`0.0.0.0:32768`/IPv6).

**Incidente:** tentativas intermediárias de bootstrap registraram senhas de tentativa em logs por erro de quoting SQL. Essas senhas foram descartadas/rotacionadas e não correspondem à stack final. Os projetos intermediários devem ser parados/removidos após confirmação; logs antigos devem ser tratados como sensíveis.

**Nao executado:** inventário real Supabase, dump/restore, Alembic no alvo e cutover produtivo. O MCP Supabase não apareceu como ferramenta/recurso disponível nesta sessão.

**Status:** Staging de banco provisionado; migração de dados e validação de aplicação pendentes.

---

## 2026-07-09 - Hardening dos artefatos PostgreSQL VPS para staging

**Area:** Banco de dados / Infraestrutura / Seguranca / Operacao

**Implementacao:** reforcada a preparacao banco-only sem executar deploy, restore ou cutover. O bootstrap de roles na VPS passa a ser seguro para reexecucao e rotacao de senhas, usa o banco conectado (`current_database()`) em vez de fixar `gennomx`, e concede acesso de leitura a sequences para `gennomx_readonly`, necessario para backup/inspecao sem privilegio administrativo. O servico de backup do compose passou a exigir TLS (`PGSSLMODE=require`) com CA montada fora do Git.

**Motivo:** reduzir riscos antes do primeiro ensaio em staging: evitar scripts acoplados a um nome fixo de banco, permitir rotacao operacional de senhas, manter backup em role readonly e travar contratos de rede/TLS por teste automatizado.

**Arquivos/artefatos:** `infra/postgres/bootstrap_roles_vps.sql`, `infra/docker-compose.postgres-vps.yml`, `backend/tests/unit/test_postgres_vps_artifacts.py`, `docs/05_SEGURANCA_E_GOVERNANCA.md`, `docs/09_DEPLOY_E_OPERACAO.md`, `project_state/task_plan.md`, `project_state/progress.md`.

**Validacao:** `py_compile` dos scripts/config/teste; `docker compose -f infra\docker-compose.postgres-vps.yml config` com senhas dummy; `pytest backend\tests\unit\test_secure_config.py backend\tests\unit\test_postgres_vps_artifacts.py -v --tb=short` -> 14 passed; `ruff check` nos arquivos relevantes -> passed.

**Nao executado:** inventario real Supabase, provisionamento na Hostinger, bootstrap em banco real, Alembic no alvo, dump/restore, comparacao pos-restore e cutover produtivo.

**Status:** Implementada como hardening local; staging real ainda bloqueado por credenciais/certificados/janela.

---

## 2026-07-09 - Preparacao da migracao banco-only para PostgreSQL VPS

**Area:** Banco de dados / Infraestrutura / Seguranca / Operacao

**Implementacao:** preparada a primeira camada executavel da migracao banco-only Supabase PostgreSQL -> PostgreSQL/pgvector na VPS Hostinger, mantendo Supabase Auth/JWKS e Supabase Storage temporariamente.

**Arquivos/artefatos:** `backend/app/config.py` ganhou `DATABASE_PROVIDER=supabase_postgres|vps_postgres` e validação fail-closed contra URLs Supabase quando o provider for `vps_postgres`; `.env.example` passou a documentar banco VPS como alvo e Supabase DB como rollback temporario; `infra/docker-compose.postgres-vps.yml` define PostgreSQL 16 + pgvector sem porta publica 5432, rede interna, healthcheck, TLS por certificados fora do Git e volume de backup; `infra/postgres/bootstrap_roles_vps.sql` cria extensoes e roles `gennomx_app`, `gennomx_worker`, `gennomx_migrator`, `gennomx_readonly` com `NOSUPERUSER NOBYPASSRLS`; `infra/postgres/backup.sh` e `restore_check.sh` preparam backup/restore; `tools/postgres_inventory.py` e `tools/compare_postgres_migration.py` preparam inventario e validacao de restore.

**Decisao de seguranca:** nao relaxar TLS nem RLS para facilitar o corte. Restore em staging/producao deve usar janela controlada, reaplicar grants depois de Alembic/restore e validar roles sem superuser/BYPASSRLS. Porta 5432 nao deve ser exposta publicamente.

**Nao executado:** nenhum provisionamento real na Hostinger, dump do Supabase, restore, Alembic no alvo, teste contra banco VPS ou cutover produtivo. Esses passos exigem credenciais/URLs reais, certificados TLS do Postgres, backup final e aprovacao operacional explicita.

**Status:** Preparado em codigo/documentacao; cutover aguardando janela e aprovacao.

---
# 11 — Changelog de Decisões

## 2026-07-09 - Decisao: migrar PostgreSQL Supabase para PostgreSQL na VPS

**Area:** Banco de dados / Infraestrutura / Seguranca / Operacao

**Decisao:** substituir o PostgreSQL hospedado da Supabase por PostgreSQL/pgvector hospedado diretamente na VPS da GennomX como banco principal da GennomX AI. A migracao sera faseada: primeiro banco, mantendo Supabase Auth/JWKS e Supabase Storage temporariamente; depois, se desejado, migrar Auth e Storage em planos separados.

**Motivo:** Marcus decidiu centralizar a infraestrutura de banco de dados na VPS. A mudanca reduz dependencia do PostgreSQL gerenciado da Supabase, mas exige assumir backup, restore, seguranca, TLS, roles, RLS, monitoramento e disponibilidade do banco.

**Racional tecnico:** hoje Supabase cumpre tres papeis diferentes: PostgreSQL, Auth/JWKS e Storage de raw payload. Migrar os tres simultaneamente aumentaria muito o risco operacional. O corte seguro e migrar somente o banco primeiro, preservando login e raw storage ate substitutos estarem implementados e testados.

**Impacto:** `DATABASE_URL`, `WORKER_DATABASE_URL` e `DATABASE_URL_SYNC` passarao a apontar para PostgreSQL/pgvector na VPS; roles `gennomx_app`, `gennomx_worker`, `gennomx_migrator` e `gennomx_readonly` continuam obrigatorias com `NOSUPERUSER NOBYPASSRLS`; porta 5432 nao deve ser exposta publicamente; backups e restore passam a ser responsabilidade operacional da GennomX. Supabase Auth/Storage permanecem temporarios na primeira fase.

**Plano canonico:** `project_state/plano_migracao_supabase_postgres_vps.md`.

**Status:** Planejado; cutover real exige aprovacao operacional explicita, backup final, restore validado e janela de manutencao.

---

## 2026-07-09 - Plano aprovado: data warehouse e ingestao recorrente

**Area:** Dados / Ingestao / Data warehouse / MCP / Operacao

**Decisao:** iniciar a construcao operacional do banco/data warehouse da GennomX AI por ondas, partindo do estado real ja implementado e nao de uma arquitetura greenfield. As primeiras quatro etapas aprovadas sao: (1) diagnostico e inventario real do banco/conectores/jobs/MCP/ambiente; (2) ativacao controlada dos conectores existentes com handshake, dry-run/execucao limitada e validacao de idempotencia; (3) camada inicial de qualidade/cobertura do warehouse; (4) primeiro incremento seguro de granularidade clinica para endpoints, resultados e safety.

**Motivo:** o projeto ja possui schema Supabase/PostgreSQL, conectores `clinicaltrials_gov`, `pubmed`, `openfda`, `dailymed`, `open_targets` e `ema`, Celery/Redis, raw storage, `SourceDocument`, `EvidenceSnippet`, MCP read-only e dashboard. A proxima etapa de valor nao e redesenhar a base, mas operacionalizar ingestao real recorrente, medir cobertura, explicitar lacunas e expandir o banco com qualidade auditavel.

**Cadencia alvo:** backbone diario para ClinicalTrials.gov, PubMed, openFDA, DailyMed e freshness; backbone semanal para Open Targets, EMA, retencao e qualidade/cobertura. Fontes event-driven ou mais ruidosas (ANVISA, PMC full-text, congressos, press releases, investor decks) ficam fora da primeira rodada e entram em ondas posteriores conforme contrato VLAEG, compliance e prioridade.

**Qualidade esperada:** evoluir cada dado por niveis: raw preservado -> parseado -> normalizado -> canonico com evidencia -> enriquecido/conectado -> curado/confiavel. Ferramentas MCP devem retornar evidencias, lacunas, freshness e limites, sem prometer cobertura inexistente.

**Documentos afetados:** `project_state/plano_data_warehouse_ingestao.md`, `project_state/prompt_implementacao_dw_etapas_1_4.md`, `project_state/task_plan.md`, `project_state/progress.md`, `docs/11_CHANGELOG_DECISOES.md`.

**Status:** Plano aprovado; implementacao das etapas 1-4 delegada ao proximo agente.

---

## 2026-07-08 — F4 em andamento: GennomX AI sob `gennomx.com`

**Área:** Frontend / API / Auth / Operação

**Decisão:** alinhar o GennomX AI ao contrato vigente de `gennomx.com`, com frontend em
`admin.gennomx.com/ai`, API em `admin.gennomx.com/api/ai` e MCP em `mcp.gennomx.com`, mantendo o
compose legado como histórico.

**Implementação:**
- `frontend/next.config.ts`: `basePath` via `NEXT_PUBLIC_BASE_PATH` e export do valor para o client.
- `frontend/src/lib/base-path.ts`: helper `withBasePath(...)` para redirects e navegação client-side.
- `frontend/src/lib/api-base.ts`: join seguro de `NEXT_PUBLIC_API_URL` com paths relativos.
- `frontend/src/lib/api.ts` / `frontend/src/lib/api-server.ts`: chamadas agora usam paths relativos
  (`api/v1/...`, `health`) via `apiUrl(...)`.
- `frontend/src/middleware.ts`: redirects de login e de root respeitam o `basePath`.
- `frontend/src/app/login/page.tsx` e `frontend/src/components/layout/header.tsx`: navegação com
  `withBasePath(...)`.
- `frontend/scripts/check-base-path.mjs`: guard estático para evitar novos caminhos absolutos.
- `backend/app/config.py` / `backend/app/main.py`: `ROOT_PATH=/api/ai` e `API_ALLOWED_HOSTS` passam
  a refletir a topologia ativa.
- `.env.example`: documenta `NEXT_PUBLIC_BASE_PATH=/ai`, `ROOT_PATH=/api/ai`, `API_ALLOWED_HOSTS`
  e os hosts `admin.gennomx.com` / `mcp.gennomx.com`.

**Motivo:** eliminar o acoplamento ao host antigo (`api.gennomx.ai`) e manter frontend, backend e
redirects coerentes quando a app estiver atrás do hub admin.

**Validação pendente:** `npm run lint`, `npm run typecheck`, `npm run build`, `npm run check:base-path`
e a suíte backend correspondente.

**Status:** em andamento.

## 2026-07-02 — Revisão técnica sênior: dashboard, governança e débito técnico de CI

**Área:** Dashboard / API / Segurança / Governança / Qualidade / CI

**Decisão:** executar o plano de correção registrado em `project_state/task_plan.md`
(revisão técnica sênior de 2026-07-02), cobrindo os achados de severidade média/baixa (A1–A7)
identificados após o programa de correção técnica anterior (2026-06-20) já ter fechado os
achados críticos, mais o débito técnico de CI descoberto ao tentar deixar os gates verdes.

**Implementação:**
- **A1 (funcional):** `GET /api/v1/overview` implementado (`OverviewService`, agregação em
  query única); o dashboard exibia KPIs zerados porque a rota nunca existira apesar de o
  frontend já a chamar.
- **A2 (funcional):** filtro `phase` de ativos passa a ser aplicado no SQL. Achado colateral:
  vocabulário de fase divergente entre frontend (`PHASE_1`) e backend (`PHASE1`) também
  quebrava o filtro de fase de **trials** e a tradução `phaseLabel` em produção — corrigidos
  os três.
- **A3 (governança):** `CorrectionService.review` recusa aprovação quando `reviewer ==
  requested_by` (quatro olhos). Exigiu, para funcionar de fato, registrar um handler global
  `@app.exception_handler(GennomXError)` — sem ele, `AuthorizationError`/`NotFoundError`
  viravam 500 genérico em qualquer rota, não só nesta.
- **A4 (segurança):** SSRF por DNS-rebinding mitigado no scraper controlado (feature ainda
  inativa) — conexão passa a usar o IP já validado, com `Host`/SNI fixados no hostname original.
- **A6 (limpeza):** `CurrentUser.can_write`/papel `worker` removidos (nunca usados por nenhuma
  rota ou usuário real).
- **A7 (recursos):** `LLMClient`/`LLMService` ganharam `close()` + suporte a context manager.
- **Débito técnico de CI (fora de A1–A7, necessário para o gate ficar verde):** achado bandit
  médio (XXE em `pubmed/connector.py`, corrigido com `defusedxml`) e 20 erros mypy
  pré-existentes em 7 arquivos, todos corrigidos na raiz do problema (sem `# type: ignore`) —
  ver `docs/05_SEGURANCA_E_GOVERNANCA.md` (Correção fase 3) para o achado XXE.

**Motivo:** os achados eram de coerência funcional (dashboard mentindo sobre dados),
governança (ausência de segregação de funções) e um blocker silencioso de CI (mypy/bandit
nunca tinham rodado contra o código real, pois o repositório nunca teve commit/push).

**Alternativas consideradas:**
- Remover o parâmetro `phase` em vez de implementá-lo (A2): descartado; o dropdown de fase já
  existe na UI e é intenção de produto clara, só faltava a ligação com o backend.
- Deixar o achado bandit/mypy pré-existente fora de escopo: descartado a pedido do usuário
  após o relatório inicial apontar que bloquearia o CI mesmo sem relação com A1–A7.

**Impacto:** dashboard exibe métricas reais; filtro de fase funcional em ativos e trials;
correções factuais exigem revisor distinto do solicitante; erros de domínio retornam status
HTTP correto em toda a API (não só em correções); scraper resiste a rebinding; `ruff check`,
`ruff format --check`, `mypy app workers` e `bandit -r app workers -ll` passam localmente sem
supressões. Suíte completa (238 testes) e Playwright e2e (7/7) verdes.

**Documentos afetados:** `docs/05_SEGURANCA_E_GOVERNANCA.md` (Correção fase 3),
`docs/07_DASHBOARD_UX.md` (Estado implementado — 2026-07-02),
`project_state/task_plan.md`, `project_state/findings.md`, `docs/11_CHANGELOG_DECISOES.md`.

**Riscos remanescentes:** primeiro commit/push (A5) segue adiado por decisão do usuário — o
CI real no GitHub ainda não foi executado; validação manual em navegador não foi feita nesta
sessão (sem ambiente rodando).

**Status:** Implementada; commit/push (A5) e validação manual em ambiente real pendentes.

---

## 2026-07-02 — Prontidão de deploy MVP: retry, hosts e stack produtiva

**Área:** Deploy / Operação / Segurança / Jobs

**Decisão:** fechar as pendências bloqueantes e não bloqueantes identificadas na análise pré-deploy,
mantendo fora do escopo ANVISA e PMC full-text por decisão explícita do usuário.

**Implementação:**
- `retry_job` passa a reenfileirar também `openfda`, `dailymed`, `open_targets` e `ema`, cobrindo
  todos os conectores P1 implementados; testes unitários adicionados.
- `API_ALLOWED_HOSTS` passa a configurar o `TrustedHostMiddleware` em produção; wildcard global e
  localhost são recusados pelo validator de produção.
- `infra/docker-compose.prod.yml` e `infra/Caddyfile` adicionam base produtiva para Hostinger VPS:
  API FastAPI, worker Celery, beat Celery, Redis TLS e Caddy HTTPS.
- `.env.example` documenta `API_DOMAIN`, `TLS_ADMIN_EMAIL`, `API_ALLOWED_HOSTS` e URLs Redis
  `rediss://` para produção.
- `Makefile` ganha `prod-up`, `prod-down`, `prod-logs` e `release-check`.
- `.gitignore` deixa de ignorar qualquer diretório `lib/` globalmente; isso preserva
  `frontend/src/lib/` no primeiro commit enquanto `.env`, caches, build e `secrets/` seguem fora.
- `docs/09_DEPLOY_E_OPERACAO.md` ganha checklist de pré-deploy: migração até `0006`, gates locais,
  handshake com rede, validação `/ready` e configuração do frontend.

**Motivo:** tornar o MVP operacionalmente subível sem depender de domínios hardcoded, sem relaxar
Redis TLS em produção e com fallback manual de jobs para todos os conectores já implementados.

**Validação pendente:** executar gates locais completos e `make handshake` em ambiente com Python,
Docker e rede liberados; aplicar Alembic `0006` no Supabase real com credenciais produtivas.

---

## 2026-07-02 — Conectores P1 regulatórios/target: openFDA, DailyMed, Open Targets, EMA

**Área:** Conectores / Ingestão / MCP (`get_regulatory_status`)

**Decisão:** implementar os quatro conectores P1 pendentes da planilha
`project_state/fontes_priorizacao.xlsx`, seguindo o padrão VLAEG do conector `pubmed`
(Link → Arquitetura → testes), como parte da preparação do deploy do MVP.

**Implementação:**
- `workers/persistence/regulatory.py` (novo, compartilhado): persiste `regulatory_approvals`
  para openFDA/DailyMed/EMA — resolve `DrugAsset` por nome/alias, upsert de `SourceDocument`,
  `PersistenceDecisionEngine` para insert/replace/noop/conflict, `EvidenceSnippet` por registro.
- `workers/persistence/targets.py` (novo): persiste `targets` para Open Targets, com merge não
  destrutivo de `aliases`/`associated_indication_ids` em atualizações.
- Quatro pacotes de conector novos: `workers/connectors/{openfda,dailymed,opentargets,ema}/`.
- Quatro tasks Celery (`run_openfda_ingest`, `run_dailymed_ingest`, `run_opentargets_ingest`,
  `run_ema_ingest`) e `beat_schedule` correspondente (diário para openFDA/DailyMed, semanal para
  Open Targets/EMA).
- `tools/handshake.py` atualizado com os quatro novos `healthcheck()`.
- Nenhuma migração de schema foi necessária: `regulatory_approvals`, `targets` e as linhas de
  `data_sources` para as quatro fontes já existiam desde `0001_initial_schema.py`.
- Nova dependência `openpyxl` (parsing do export oficial EMA em `.xlsx`) adicionada a
  `pyproject.toml`, `_lock_requirements.in` e `requirements.lock`.
- Testes unitários: `test_regulatory_persistence_flow.py` e `test_targets_persistence_flow.py`
  (fluxo compartilhado insert/update/noop/conflict/reject) + `test_{openfda,dailymed,opentargets,
  ema}_connector.py` (parser/normalizer/healthcheck) — 39 testes novos, suíte completa em 223
  passed/2 skipped (skips ambientais pré-existentes de DuckDB no Python 3.14 local).
- Durante os testes, corrigido um bug real em `regulatory.py`: a consulta de aprovação existente
  não recuperava `source_updated_at`, fazendo o motor de decisão cair sempre em `CONFLICT`
  ("peer_sources_disagree") em vez de `REPLACE` ao reingerir a mesma fonte com dado mais recente.

**Limitações documentadas:** nenhuma das quatro fontes expõe filtro de delta confiável (execuções
incrementais são limitadas por `*_MAX_RECORDS_PER_RUN` e dependem de upserts idempotentes);
resolução de `DrugAsset` é por nome/alias exato, sem fuzzy matching; Open Targets é guiado por
lista semente de doenças, não por todo o grafo da plataforma. Detalhe completo em
`docs/03_FONTES_E_INGESTAO.md` §6.8C.

**Motivo:** fechar a cobertura de dados P1 (decisão do usuário) antes da Onda B de prontidão de
deploy, e destravar `get_regulatory_status`/`search_drugs`/`compare_assets` com dados regulatórios
e de targets reais em vez de tabelas vazias.

---

## 2026-06-23 — Revisão técnica sênior: correções críticas/altas/médias/baixas

**Área:** Segurança / MCP / Workers / Frontend / Qualidade

**Decisão:** executar o plano de correção da revisão técnica sênior do monorepo
(`atue-como-um-revisor-abundant-hinton`), cobrindo todas as prioridades identificadas.

**Implementação:**
- **Crítico:** chaves reais removidas de `.env.example` (substituídas por placeholders); rotação
  dispensada por decisão do time (chaves recém-inseridas, repositório sem commit).
- **Alto:** rate limit por IP pré-autenticação no MCP + remoção de escrita em `mcp_query_logs`
  para falhas `401` (DoS); `validate_secure_production_settings` passa a exigir JWKS/`SUPABASE_URL`
  em produção.
- **Médio:** sanitização de erros nas MCP tools (sem vazar texto de exceção); lockfile de
  dependências versionado (`requirements.lock`) usado no `Dockerfile`/CI; `retry_job` passa a
  retornar `501` explícito para fontes sem task mapeada (em vez de `200 success:false`);
  `worker-status` retorna estado `unknown` em falha de `inspect`; `workers/tasks/ingest.py`
  (1.467 linhas) refatorado em `workers/persistence/{common,evidence,assets,trials,publications}.py`,
  preservando comportamento e cobertura de teste.
- **Baixo:** limpeza de buckets vazios/stale no rate limiter MCP em memória; variável morta
  `SECRET_KEY` removida de `tests/conftest.py`/CI (era `API_SECRET_KEY`); `/ready` oculta detalhe
  por componente em produção; `frontend/src/middleware.ts` passa a redirecionar usuários não-admin
  fora de `/governance` e `/security`.
- **Testes de regressão:** 401 MCP sem escrita em DB, erro de tool sanitizado, usuário `readonly`
  recebendo 403 em rota `require_admin`, downgrade de migration crítica (RLS) — já existente,
  confirmado e mantido.

**Motivo:** elevar a postura de segurança/confiabilidade antes do primeiro commit/push e fechar
lacunas de manutenção identificadas na revisão, sem alterar escopo funcional do produto.

**Documentos afetados:** `docs/04_MCP_TOOLS.md` (§8.9), `docs/05_SEGURANCA_E_GOVERNANCA.md`
(Correção fase 2), `docs/11_CHANGELOG_DECISOES.md`.

**Status:** Implementada.

---

## 2026-06-23 — Reabertura da Fase 11 como motor LLM OPENCODE

**Área:** Arquitetura / IA interna / Segurança / Operação

**Decisão:** reabrir o passo 11 sem benchmark comparativo. O motor inicial de LLM do MVP será
uma chave API do OPENCODE, inicialmente apontando para DeepSeek V4 Pro, com integração planejada em
`project_state/plano_fase_11_llm_opencode.md`.

**Motivo:** o usuário decidiu abandonar a etapa de benchmark e avançar com uma escolha operacional
direta de provedor/modelo, preservando a exigência de configuração por ambiente, validação por
schema, evidência, confidence score, auditoria e bloqueio de escrita direta por LLM.

**Impacto:** a execução deverá atualizar a stack documentada, que ainda menciona LiteLLM como
gateway ativo, e implementar um adaptador OPENCODE isolado. O identificador real do modelo e a URL
base devem ser confirmados por handshake antes da lógica final.

**Documentos afetados nesta etapa:**  
- `project_state/plano_fase_11_llm_opencode.md`
- `project_state/task_plan.md`
- `docs/11_CHANGELOG_DECISOES.md`

**Status:** Planejada.

---

## 2026-06-23 — Implementação da Fase 11: motor LLM OPENCODE

**Área:** Arquitetura / IA interna / Segurança / Operação

**Decisão:** implementar o motor LLM conforme `project_state/plano_fase_11_llm_opencode.md`,
substituindo LiteLLM (quarantined) por um adaptador HTTP direto via `httpx` contra a API
OpenAI-compatible do OPENCODE, com validação Pydantic obrigatória e auditoria `llm_call_logs`.

**Implementação:**
- `backend/app/services/llm/`: módulo com `LLMClient` (httpx), `LLMService` (config + safety),
  `LLMRequest`/`LLMResponse` (schemas Pydantic genéricos), `LLMCallMetadata` e erros tipados;
- `backend/app/config.py`: novas variáveis (`LLM_PROVIDER`, `LLM_ENABLE_NETWORK_CALLS`,
  `OPENCODE_API_KEY`, `OPENCODE_BASE_URL`, etc.); validação fail-closed em produção;
- `backend/app/models/db/llm_call_log.py`: modelo ORM `LLMCallLog` (hashes, schema_valid,
  latency, tokens, status, error sanitizado — sem armazenar prompts completos);
- `backend/migrations/versions/0006_llm_call_logs.py`: migração para criar tabela `llm_call_logs`;
- `tools/handshake_llm.py`: handshake VLAEG fase L para OPENCODE, com `--dry-run` e `--mock`;
- `backend/tests/unit/test_llm_module.py`: 20+ testes unitários mockados cobrindo config,
  client, service, schema validation, prompt injection e sanitização;
- `.env.example` atualizado; variáveis LiteLLM deprecadas e movidas para legado;
- `Makefile`: novo target `handshake-llm`;
- Docs `01`, `05`, `06`, `09`, `12` atualizados para refletir OPENCODE como adaptador.

**Motivo:** completar o passo 11 do fechamento operacional e da remediação externa, mantendo
a premissa de que o LLM interno é auxiliar e não decide correções, merges ou escrita direta.

**Trade-offs:** LiteLLM permanece no `pyproject.toml` como extra opcional `llm` (quarantined)
até que uma release com as correções de CVE esteja disponível. O adaptador OPENCODE é simples
e acoplado ao formato OpenAI-compatible; provedores com API diferente exigiriam novo adaptador.

**Status:** Implementada.

---

## 2026-06-23 — Conector PubMed (E-utilities)

**Área:** Dados / Ingestão / Conectores

**Decisão:** implementar o conector PubMed conforme `project_state/plano_conector_pubmed.md`,
criando slug `pubmed` (separado do slug legado `pubmed_pmc`, preservado inativo). Escopo restrito
a PubMed (abstracts/metadados via E-utilities); PubMed Central full-text/OA subset adiado para
ordem 3 (PMC).

**Implementação:** Connector (ESearch/EFetch, paginação WebEnv, rate limit, retry tenacity),
Parser (XML ElementTree: PMID, DOI, PMCID, title, abstract estruturado, journal, authors, MeSH,
NCT via DataBank), Normalizer (`publication_type` controlado, `evidence_maturity=peer_reviewed_primary`),
Task Celery (`run_pubmed_ingest` + `_persist_publications`), SourceDocument + EvidenceSnippet +
NCT linking, migração `0005`, handshake, beat schedule diário.

**Motivo:** a planilha `fontes_priorizacao.xlsx` lista PubMed como P1/ordem 2 (MVP Core, baixa
complexidade, sem autenticação obrigatória). A tabela `publications` e o MCP `search_publications`
já existiam mas sem fonte real de dados.

**Trade-offs:** parser usa `xml.etree.ElementTree` (stdlib) para não adicionar dependência nova;
`open_access` permanece `false` por padrão (sem verificação de licença PMC individual); sem LLM
para extração/validação (passo 11 adiado).

**Risco mitigado:** resolve a duplicação de slug `pubmed_pmc` sinalizada na entrada anterior,
criando slug individualizado `pubmed` para PubMed.

**Status:** Implementada.

---

## 2026-06-23 — Integração operacional do Supabase como banco principal

**Área:** Dados / Banco / Segurança / Operação

**Decisão:** formalizar o Supabase/PostgreSQL hospedado como alvo operacional do backend, workers
e migrações, mantendo roles segregadas (`gennomx_app`, `gennomx_worker`, `gennomx_migrator`,
`gennomx_readonly`) e TLS obrigatório.

**Implementação:** adicionado helper de normalização de URLs PostgreSQL/Supabase para asyncpg e
psycopg2, aplicado no runtime, workers e Alembic; `.env.example` agora documenta pooler/direct
connection; `infra/supabase/bootstrap_roles.sql` cria roles, extensões e grants mínimos.

**Risco mitigado:** evita uso de `postgres`/`service_role` pelo backend, reduz erro operacional com
`sslmode=require` em asyncpg e mantém a separação entre app, ingestão e migrações.

**Status:** Implementada.

## 2026-06-23 — Validação JWT Supabase via JWKS

**Área:** Segurança / Auth / API

**Decisão:** trocar a validação FastAPI de JWT Supabase de `HS256` + segredo legado para JWKS
(`ES256`/`RS256`), mantendo fallback HS256 apenas quando `SUPABASE_JWKS_URL`/`SUPABASE_URL` não
estiver disponível.

**Motivo:** o projeto Supabase usa signing key ECC/P-256 e o PostgREST já foi configurado com
`pgrst.jwt_jwks_uri`; a API interna deve validar tokens do mesmo modo para aceitar tokens novos e
permitir desativar o segredo legado.

**Impacto:** `get_current_user()` usa `PyJWKClient` com cache, valida `aud`/`iss` e preserva a
extração de `app_metadata.gennomx_role`; `.env.example` passa a documentar `SUPABASE_JWKS_URL`.

**Status:** Implementada.

## 2026-06-21 — Conclusão operacional dos passos 1–10 e 12–14

**Área:** Dados / Ingestão / Governança / Segurança / Operação / Dashboard

**Decisão:** transformar políticas aprovadas em contratos executáveis: migração `0004`, registry de
granularidade, serviço genérico de assertions, staging DuckDB integrado, workflow de correção,
freshness agendada, retenção com legal hold/manifesto/checksum, scraping fail-closed e painel.

**Trade-offs:** mais escrita e complexidade em troca de rastreabilidade; expurgo deliberadamente
mais lento e seguro. Merge parcial limita-se a objetos/listas. Scrapers começam desativados.

**LLM:** passo 11 continua adiado; nenhuma regra depende de modelo generativo.

**Status:** Implementada; gates em `project_state/progress.md`.

## 2026-06-21 — Remediação do parecer técnico externo

**Área:** Ingestão / Segurança / Testes / Frontend / Operação

**Decisão:** corrigir o caminho de INSERT de `SourceDocument`, tornar rejeição sistêmica total uma
falha explícita, testar o fluxo completo de persistência, tratar limite normal como parcial,
separar roles PostgreSQL e validá-los no runtime, remover privilégio admin da chave interna,
encaminhar JWT do usuário no SSR sem cache, remover auth morta, unificar event-loop e concluir
deduplicação/confiança determinísticas.

**Motivo:** o parecer identificou uma falha crítica real e lacunas de defesa em profundidade que
não estavam integralmente cobertas pelos 14 passos de governança temporal.

**Impacto:** ingestões novas voltam a persistir; falhas de programação não podem produzir job verde
silencioso; RLS deixa de depender apenas da disciplina de deploy; SSR preserva identidade e
auditoria do usuário.

**Validação:** 104 testes unitários/de integração aprovados e 1 skip ambiental, incluindo o fluxo
HTTP completo do MCP e persistência CT.gov em INSERT/UPDATE/NOOP/falha; Ruff, ESLint, TypeScript,
build Next e SQL Alembic offline aprovados. Resultados detalhados em `project_state/progress.md`.

**LLM:** seleção de modelos (passo 11) continua adiada e não foi alterada.

**Status:** Implementada.

## 2026-06-20 — Governança temporal e política de persistência (passos 1–10, 12–14)

**Área:** Dados / Ingestão / Banco / Segurança / Operação

**Decisão:** adotar ADR-001 e separar raw imutável, assertions bitemporais, projeção canônica e
histórico/auditoria. Foram introduzidos `field_assertions`, `data_conflicts`,
`manual_corrections`, metadados temporais, supersession, motor determinístico de decisão,
proteção contra regressão do CT.gov, separação do estágio corrente/máximo histórico/status,
relações trial↔ativo temporais, evidência por campo, staging/quality gates com DuckDB, retenção,
arquivamento e compliance de scraping controlado.

**Motivo:** impedir que versões atrasadas, duplicadas, conflitantes ou obsoletas contaminem o
estado corrente sem destruir rastreabilidade.

**Impacto:** migração `0003`; tabelas canônicas passam a ser projeções correntes; atualização
factual destrutiva deixa de ser permitida; decisões possuem ação, razão e versão de regras.

**Trade-offs:** mais escrita e complexidade de governança em troca de replay, auditabilidade e
consultas correntes menores. Arrays legados permanecem temporariamente como caches compatíveis.

**Compliance:** revogadas orientações genéricas de contorno de robots/captcha/bloqueios. Scraping
passa a exigir avaliação por domínio, allowlist, limites, kill switch e respeito aos controles.

**LLM:** o passo 11 (seleção/benchmark de modelos) foi explicitamente adiado por decisão do
usuário. Nenhum modelo ou plano de provedor foi acoplado nesta entrega.

**Arquivos principais:** `architecture/ADR_001_temporalidade_precedencia.md`, migração `0003`,
`app/services/persistence_decision.py`, modelos de governança, worker CT.gov, staging, testes,
`AGENTS.md`, docs 02/03/05/06/09 e `project_state/*`.

**Riscos remanescentes:** migração completa de arrays de indications/sponsors/locations para
relações temporais será incremental por conector; política de current stage será refinada por
agregação de todas as relações após integração das fontes seguintes.

**Status:** Implementada; validações locais registradas em `project_state/progress.md`.

## 2026-06-20 — Correção fase 4: integridade, RLS e runtime mínimo

Referências escalares passam a UUID/FK e trial↔ativo deixa de depender apenas de array. RLS é
habilitada com acesso por papéis de backend; papéis locais deixam de possuir login/senha no
repositório. Readiness inclui Redis e containers são versionados, autenticados e executados com
superfície reduzida. A migração falha diante de dados inválidos em vez de removê-los.

## 2026-06-20 — Correção fase 3: ingestão rastreável e limitada

CT.gov passa a ser processado página a página, com cursor no último sucesso e sobreposição. O
limite de registros torna a execução incompleta para impedir perda silenciosa. Raw payload é
obrigatório, comprimido e endereçado por hash no Supabase Storage; falha de upload interrompe o
job. Persistência usa savepoint por estudo e evidências passam a ser fragmentos literais da fonte.

## 2026-06-20 — Correção fase 2: fronteira MCP interoperável e distribuída

**Área:** MCP / Segurança / Auditoria / Operação

**Decisão:** oferecer FastMCP por stdio como transporte padrão, preservar `/api/mcp/call` como adaptador legado, aplicar escopos por cliente, rate limit Redis, limite de payload e índice limitado de entidades acessadas.

**Motivo:** o endpoint JSON proprietário não era diretamente interoperável e os controles em memória não cobriam múltiplos workers.

**Impacto:** hosts locais podem iniciar MCP padrão; clientes HTTP permanecem compatíveis; produção falha fechada se Redis não garantir o limite.

**Riscos:** exposição remota futura exige transporte HTTP MCP suportado, TLS e autenticação no gateway.

**Status:** Implementada; teste integrado do transporte permanece no gate final.

Este arquivo deve registrar decisões relevantes para preservar o racional do projeto ao longo do tempo.

Use este arquivo sempre que houver mudança em:

- escopo do produto;
- arquitetura;
- stack;
- modelo de dados;
- fontes e conectores;
- servidor MCP;
- regras de segurança;
- testes e gates de qualidade;
- deploy e operação;
- roadmap;
- premissas estratégicas.

---

## Formato recomendado

```md
## AAAA-MM-DD — Título da decisão

**Área:** Produto | Arquitetura | Dados | MCP | Segurança | Testes | Operação | UX | Comercial

**Decisão:**  
Descrever a decisão de forma objetiva.

**Motivo:**  
Explicar o racional.

**Alternativas consideradas:**  
Listar opções descartadas, quando aplicável.

**Impacto:**  
Explicar efeitos esperados no código, dados, segurança, operação ou roadmap.

**Documentos afetados:**  
- `AGENTS.md`
- `docs/...`

**Status:** Proposta | Aprovada | Implementada | Substituída | Revogada
```

---

## 2026-06-04 — Separação conceitual entre aplicação e geração de relatórios

**Área:** Produto / Arquitetura / MCP

**Decisão:**  
A GennomX AI será tratada como infraestrutura proprietária de dados biomédicos e competitivos com acesso via MCP. A geração final de relatórios será executada por modelos host externos, como ChatGPT, Claude e agentes privados.

**Motivo:**  
Preservar o núcleo de valor no banco proprietário, nas evidências, na rastreabilidade e nas ferramentas MCP, evitando que a aplicação seja reduzida a um chatbot ou gerador textual.

**Impacto:**  
O design da aplicação deve priorizar banco, ingestão, normalização, governança, dashboard, API e MCP. Relatórios devem ser tratados como consumo externo por modelos host, eventualmente apoiados por bundles estruturados.

**Documentos afetados:**  
- `AGENTS.md`
- `README.md`
- `docs/00_CONTEXTO_ESTRATEGICO.md`
- `docs/04_MCP_TOOLS.md`

**Status:** Implementada na documentação.

---

## 2026-06-09 — Reorganização modular da documentação

**Área:** Documentação / Operação de agentes

**Decisão:**  
Os documentos originais foram reorganizados em uma estrutura modular com `AGENTS.md` na raiz e documentação especializada em `/docs`.

**Motivo:**  
Facilitar a leitura por desenvolvedores e agentes de IA, reduzir redundância, preservar o racional e separar instruções operacionais de documentação estratégica/técnica detalhada.

**Impacto:**  
A partir desta organização, agentes devem usar `AGENTS.md` como fonte operacional principal e consultar os arquivos específicos em `/docs` antes de alterações relevantes.

**Documentos afetados:**  
- `AGENTS.md`
- `README.md`
- `CLAUDE.md`
- `GEMINI.md`
- `docs/*`

**Status:** Implementada na documentação.


---

## 2026-06-09 — Aprovação da stack tecnológica refinada do MVP

**Área:** Arquitetura / Stack / Operação / Segurança / Testes

**Decisão:**  
A stack oficial do MVP foi refinada para: Next.js no dashboard; FastAPI para API interna, administração e MCP; Celery + Redis para jobs assíncronos; DuckDB nos workers para processamento batch; Supabase/PostgreSQL como núcleo de dados, auth, storage, full-text search e pgvector; LiteLLM como gateway de modelos de IA com roteamento por criticidade, custo e validação por schema.

**Motivo:**  
Reduzir custo fixo inicial, facilitar manutenção por equipe enxuta, preservar Supabase como centro operacional do MVP, evitar que a API/MCP sofram com ingestões pesadas e permitir uso controlado de modelos de IA por tarefa.

**Alternativas consideradas:**  
- RabbitMQ já no MVP: adiado; Redis é mais simples para a primeira fase.
- OpenSearch/Pinecone/Vector DB dedicado no MVP: adiado; PostgreSQL full-text search e pgvector são suficientes inicialmente.
- Fixar modelo específico de LLM: descartado; os modelos devem ser configuráveis e trocáveis.
- Processamento pesado nas rotas FastAPI: descartado por risco de lentidão, OOM e indisponibilidade do dashboard/MCP.

**Impacto:**  
A documentação agora exige separação entre frontend, API/MCP e workers; uso de jobs assíncronos para ingestão e parsing; DuckDB como motor batch local; LiteLLM com governança; e novos testes específicos para Next.js, FastAPI, Celery, DuckDB e LiteLLM.

**Documentos afetados:**  
- `AGENTS.md`
- `README.md`
- `docs/01_ARQUITETURA.md`
- `docs/03_FONTES_E_INGESTAO.md`
- `docs/04_MCP_TOOLS.md`
- `docs/05_SEGURANCA_E_GOVERNANCA.md`
- `docs/06_TESTES_E_QUALIDADE.md`
- `docs/07_DASHBOARD_UX.md`
- `docs/08_ROADMAP.md`
- `docs/09_DEPLOY_E_OPERACAO.md`
- `docs/12_STACK_TECNOLOGICA_REFINADA.md`

**Status:** Aprovada e implementada na documentação.

---

## 2026-06-12 — Primeira correção de integração MCP, jobs e rastreabilidade ClinicalTrials.gov

**Área:** MCP / Dados / Ingestão / Segurança / Testes / Operação

**Decisão:**  
Priorizar correções de integração do MVP antes de expandir novos conectores: o endpoint MCP agora recebe sessão real de banco, valida `arguments`, persiste logs em `mcp_query_logs` inclusive para chamadas inválidas/bloqueadas, a API de jobs consulta `ingestion_jobs`, retry de ClinicalTrials.gov passa a reenfileirar tarefa Celery, o `JobTracker` resolve `data_source_id` e grava JSON válido em campos de erro/metadados, e o pipeline ClinicalTrials.gov cria `SourceDocument` e `EvidenceSnippet` básico por trial ingerido.

**Motivo:**  
O diagnóstico mostrou que a arquitetura já estava bem estruturada, mas havia lacunas no fluxo real de auditoria e rastreabilidade. Sem sessão de banco no MCP, as ferramentas retornavam indisponibilidade; sem logs persistidos, chamadas de modelos host não eram auditáveis; sem `SourceDocument`/`EvidenceSnippet`, os trials ingeridos não atendiam ao requisito central de evidência.

**Alternativas consideradas:**  
- Expandir conectores antes de corrigir rastreabilidade: descartado, pois aumentaria volume de dados sem evidência.
- Implementar raw storage completo nesta etapa: adiado para manter a mudança pequena; por enquanto há documento-fonte e trecho de evidência básico.
- Expor retry genérico para todas as fontes: descartado até que cada conector tenha task Celery real.

**Impacto:**  
- MCP fica operacionalmente conectado ao banco e auditável.
- `clinicaltrials_gov` passa a ter rastreabilidade mínima fonte→trial→evidência.
- Jobs deixam de ser endpoint vazio e passam a refletir dados reais.
- Novos jobs de ingestão passam a carregar `data_source_id` quando a fonte estiver registrada.
- `pyproject.toml` passa a usar build backend editável válido para `pip install -e`.
- Frontend atualizado para `next@15.5.18` e `eslint-config-next@15.5.18`.
- `frontend/package-lock.json` criado e CI frontend volta a usar `npm ci`.
- Backend passa em Ruff e em 45 testes automatizados.
- Frontend passa em lint, typecheck e build.
- Persistem 2 vulnerabilidades moderadas no `npm audit`, ligadas ao `postcss` transitivo dentro do Next; correção major não aplicada nesta etapa.
- Novos testes unitários cobrem dispatcher MCP e serviço de jobs.

**Documentos afetados:**  
- `docs/03_FONTES_E_INGESTAO.md`
- `docs/04_MCP_TOOLS.md`
- `docs/05_SEGURANCA_E_GOVERNANCA.md`
- `docs/06_TESTES_E_QUALIDADE.md`
- `docs/11_CHANGELOG_DECISOES.md`

**Status:** Implementada parcialmente no código; pendências registradas nos documentos específicos.

---

## 2026-06-12 — Linking inicial ClinicalTrials.gov para DrugAsset

**Área:** Dados / Ingestão / Workers / Testes

**Decisão:**  
Implementar a criação/atualização inicial de `DrugAsset` a partir de intervenções terapêuticas do ClinicalTrials.gov e preencher `clinical_trials.drug_asset_ids` já durante a ingestão. O task Celery `link_trials_to_assets` também passa a executar backfill de trials antigos sem vínculo com ativos.

**Motivo:**  
O próximo gargalo do MVP era transformar trials ingeridos em grafo consultável por ativo. Sem esse vínculo, ferramentas MCP e páginas de ativos ficariam dependentes de busca textual em `interventions`, reduzindo precisão, rastreabilidade e valor analítico.

**Alternativas consideradas:**  
- Adiar linking para deduplicação fuzzy completa: descartado, pois bloquearia valor inicial do MVP.
- Criar ativos sem evidência: descartado por violar o princípio central de rastreabilidade.
- Fazer matching amplo por substring: adiado para evitar falsos positivos em nomes compostos e braços comparadores.

**Impacto:**  
- ClinicalTrials.gov cria/reusa `SourceDocument`, cria evidência do trial e também evidência do ativo.
- Intervenções `DRUG`, `BIOLOGICAL` e `GENETIC` geram candidatos a `DrugAsset`.
- Ativos existentes são atualizados com aliases, indicações, sponsors, estágio clínico mais avançado e metadados de NCT IDs.
- Trials passam a persistir `drug_asset_ids`.
- Backfill de trials sem vínculo fica disponível em `workers.tasks.process.link_trials_to_assets`.
- Foram adicionados testes unitários e a suíte backend passou em 50 testes.

**Documentos afetados:**  
- `docs/02_MODELO_DE_DADOS.md`
- `docs/03_FONTES_E_INGESTAO.md`
- `docs/06_TESTES_E_QUALIDADE.md`
- `docs/MEMORY_FASE_2.md`
- `docs/MEMORY_FASE_6.md`
- `docs/11_CHANGELOG_DECISOES.md`

**Status:** Implementada no código e validada por testes unitários.

---

## 2026-06-20 — Adoção do Protocolo VLAEG Otimizado

**Área:** Documentação / Operação de agentes / Dados / Operação

**Decisão:**  
Adotar formalmente o Protocolo VLAEG Otimizado (`protocolo_vlaeg_otimizado.md`) como framework operacional padrão da GennomX AI, sem regredir a documentação existente. Foram criados `docs/13_PROTOCOLO_VLAEG.md` (mapeamento de fases V‑L‑A‑E‑G e de documentação VLAEG↔GennomX) e o diretório `project_state/` (`task_plan.md`, `progress.md`, `findings.md`), que sucede `TASKFLOW.md` e consolida os `MEMORY_FASE_*` (preservados como histórico). Formalizados contratos de dados por conector (`docs/03` §0) e por ferramenta MCP (`docs/04` §0), declarações de automação e runbook de autocorreção (`docs/09` §0/§0C). No código, a fase Link ganhou `BaseConnector.healthcheck()` + implementação no ClinicalTrials.gov + `tools/handshake.py`; a fase Gatilho ganhou `beat_schedule` no Celery para ingestão diária do ClinicalTrials.gov.

**Motivo:**  
Tornar explícita a rastreabilidade de processo (Visão→Link→Arquitetura→Estilo→Gatilho), fechar lacunas concretas que a ótica VLAEG expôs (sem validação sistemática de conectividade e sem agendamento real de ingestão) e padronizar a evolução de novos conectores, ferramentas MCP e automações.

**Alternativas consideradas:**  
- Renumerar os docs para o esquema VLAEG 00–08: descartado para evitar regressão e perda de granularidade; adotado mapa de equivalência.
- Manter TASKFLOW/MEMORY como fonte de estado: descartado em favor de `project_state/` como fonte única, preservando os arquivos antigos como histórico.
- Apenas overlay documental sem tocar código: descartado; o usuário aprovou overlay + correções de engenharia.

**Impacto:**  
- Ordem de leitura obrigatória (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`) passa a incluir `docs/13` e `project_state/`.
- Novos conectores devem declarar contrato de dados e passar pelo handshake (matriz Link em `docs/03`) antes da lógica.
- Ingestão do ClinicalTrials.gov passa a ter gatilho agendado via Celery beat.
- Novos testes cobrem `healthcheck()`.

**Documentos afetados:**  
- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`
- `docs/13_PROTOCOLO_VLAEG.md` (novo)
- `docs/03_FONTES_E_INGESTAO.md`, `docs/04_MCP_TOOLS.md`, `docs/09_DEPLOY_E_OPERACAO.md`
- `docs/README.md`, `TASKFLOW.md`, `docs/MEMORY_FASE_2/5/6.md`
- `project_state/*` (novo), `tools/*` (novo), `architecture/*` (novo)
- `backend/workers/base/connector.py`, `backend/workers/connectors/clinicaltrials/connector.py`, `backend/workers/celery_app.py`, `Makefile`

**Riscos:**  
- Divergência entre `project_state/` e docs se não mantido; mitigado pela ordem de leitura e pelo runbook.
- `beat_schedule` exige processo `celery beat` em operação; documentado em `docs/09` e `Makefile`.

**Próximos passos:**  
- Implementar `healthcheck()` nos conectores futuros (PubMed, openFDA, etc.) e atualizar a matriz Link.
- Declarar automações dos novos jobs em `docs/09` §0.2 ao ativá-los.

**Status:** Implementada na documentação e no código.
# 2026-06-20 — Correção fase 1: identidade e configuração fail-closed

**Área:** Segurança / Frontend / API / Operação

**Decisão:** remover credenciais administrativas padrão, validar configuração de produção no startup, validar issuer/audience de JWT Supabase, obter o papel GennomX de `app_metadata`, proteger o dashboard por sessão Supabase e separar liveness de readiness.

**Motivo:** a revisão técnica identificou possibilidade de acesso administrativo por chave previsível e incompatibilidade entre APIs protegidas e frontend sem bearer token.

**Impacto:** ambientes produtivos incompletos deixam de iniciar; usuários sem sessão são redirecionados ao login; indisponibilidade do banco passa a produzir readiness 503 sem derrubar liveness.

**Riscos:** SSR exige `API_INTERNAL_KEY` somente no ambiente privado do Next; sua exposição com prefixo público continua proibida.

**Status:** Implementada; validação automatizada consolidada na fase final.

---

## 2026-06-20 — Planilha de priorização de fontes como premissa do roadmap

**Área:** Dados / Fontes e Ingestão / Roadmap

**Decisão:**
Criar `project_state/fontes_priorizacao.csv` como fonte única de verdade das fontes candidatas de ingestão (nome, categoria, URL, tipo de export principal, slug de conector, status de implementação, observações) e de sua **ordem de prioridade**, preenchida manualmente pelo usuário. A prosa de `docs/03_FONTES_E_INGESTAO.md` §4 foi resumida para apontar ao CSV em vez de listar prioridades fixas; `docs/08_ROADMAP.md` e `project_state/task_plan.md` passam a referenciar a coluna `prioridade` do CSV como ordem real de implementação de conectores.

**Motivo:**
A lista de fontes vivia espalhada como texto não estruturado em `docs/03` §4.1–4.8, sem URL, sem tipo de export e sem prioridade explícita — dificultando decidir o que entra no roadmap a seguir. Uma planilha estruturada e versionada no controle de código permite priorização manual contínua sem reescrever documentação prosa a cada mudança.

**Alternativas consideradas:**
- Manter a priorização apenas em prosa nos docs: descartado por dificultar atualização rápida e comparação entre fontes.
- Planilha externa (Google Sheets) fora do repositório: descartado por quebrar rastreabilidade via git e exigir sincronização manual.

**Impacto:**
- Novos conectores devem ser implementados seguindo a coluna `prioridade` do CSV.
- `docs/03` §4, `docs/08_ROADMAP.md` (§21 item 9, §23.1) e `project_state/task_plan.md` foram atualizados com referências cruzadas ao CSV, sem remover o histórico de texto.
- A matriz Link (`docs/03` §0B) continua sendo a referência de status de conectividade; o CSV referencia o mesmo `slug_conector`.

**Documentos afetados:**
- `project_state/fontes_priorizacao.csv` (novo)
- `docs/03_FONTES_E_INGESTAO.md`
- `docs/08_ROADMAP.md`
- `project_state/task_plan.md`
- `docs/11_CHANGELOG_DECISOES.md`

**Riscos:**
- Divergência entre o CSV e a prosa histórica dos docs se um for atualizado sem o outro; mitigado por estes apontarem explicitamente ao CSV como fonte da verdade.

**Próximos passos:**
- Usuário preenche manualmente a coluna `prioridade` do CSV para guiar a ordem real de implementação de novos conectores.

**Status:** Substituída pela decisão seguinte (planilha Excel em vez de CSV).

---

## 2026-06-20 — Planilha de priorização de fontes migra de CSV para Excel

**Área:** Dados / Fontes e Ingestão / Roadmap

**Decisão:**
Substituir `project_state/fontes_priorizacao.csv` por **`project_state/fontes_priorizacao.xlsx`** como fonte única de verdade de priorização de fontes. O usuário expandiu o arquivo para um schema mais granular (28 colunas: nome, escopo/nome alternativo, fontes incluídas, categoria, conteúdo principal, URL, domínio, tipo de acesso, possui API, exportação estruturada/bulk, requer scraping, requer licença comercial, autenticação, idioma, complexidade estimada, status de implementação, fora do MVP, recurso técnico, restrição de uso, pontos de verificação, observações, alertas de qualidade, slugs de conector original/sugerido e notas de organização). O CSV foi removido; todas as referências em `docs/03`, `docs/08_ROADMAP.md` e `project_state/task_plan.md` passam a apontar para o `.xlsx` e para a coluna `Prioridade` (maiúscula, conforme planilha).

**Motivo:**
O formato Excel permite ao usuário editar e analisar a planilha com as ferramentas habituais (Excel/Sheets), e o usuário já a enriqueceu manualmente com colunas adicionais de due diligence técnica (API/scraping/licença/idioma/complexidade) que não existiam no CSV original gerado nesta sessão.

**Alternativas consideradas:**
- Manter CSV e XLSX em paralelo: descartado por risco de divergência entre as duas fontes.
- Reescrever o XLSX no formato/colunas do CSV original: descartado; o schema expandido pelo usuário é estritamente superior e deve ser preservado como está.

**Impacto:**
- `project_state/fontes_priorizacao.csv` removido (criado e substituído na mesma sessão; sem perda de histórico de produto, apenas de um artefato de transição).
- `docs/03_FONTES_E_INGESTAO.md` §4, `docs/08_ROADMAP.md` (§21 nota do item 9, §23.1) e `project_state/task_plan.md` atualizados para referenciar `fontes_priorizacao.xlsx` / coluna `Prioridade`.
- A coluna `Prioridade` na planilha ainda está vazia em todas as linhas — o usuário a preencherá manualmente para definir a ordem real de implementação dos próximos conectores.
- Observação aberta: a planilha expandida sinaliza slugs de conector duplicados (`pubmed_pmc` usado tanto para PubMed quanto PubMed Central) com slugs sugeridos individualizados (`pubmed`, `pubmed_central`) — ainda não propagado para `docs/03` §0B; resolver ao implementar esses conectores.

**Documentos afetados:**
- `project_state/fontes_priorizacao.xlsx` (passa a ser a fonte canônica)
- `project_state/fontes_priorizacao.csv` (removido)
- `docs/03_FONTES_E_INGESTAO.md`
- `docs/08_ROADMAP.md`
- `project_state/task_plan.md`
- `docs/11_CHANGELOG_DECISOES.md`

**Riscos:**
- Arquivos `.xlsx` têm diff binário no git — mudanças na planilha não são revisáveis linha a linha como o CSV; mitigado por ser um artefato de planejamento manual, não código.

**Próximos passos:**
- Usuário preenche a coluna `Prioridade` na planilha.
- Resolver a duplicação de slug `pubmed_pmc` ao priorizar PubMed/PubMed Central.

**Status:** Implementada.

---

## 2026-06-20 — Programa de correção técnica, Fase 5

**Área:** Dashboard / API / Testes / Segurança / CI

**Decisão:** concluir as seis telas pendentes com APIs reais, expor auditoria administrativa
sanitizada, adicionar Playwright ao gate de release e tornar typecheck/SAST/dependency scan
bloqueantes. Substituir `python-jose` por PyJWT e elevar dependências com advisories ativos.

**Motivo:** os stubs impediam operação real, o Makefile chamava um teste E2E inexistente e os
scans de segurança eram não bloqueantes. Logs brutos também não deveriam chegar ao frontend.

**Impacto:** dashboard operacional completo para o modelo persistido atual; sete E2E;
78 testes unitários; build reproduzível sem download de Google Fonts; zero vulnerabilidades
npm conhecidas; auditoria visível somente a admins e com minimização de dados.

**Riscos:** o bypass E2E é aceito apenas fora de produção; B608 é excluído do Bandit porque
fragmentos SQL são internos e valores seguem parametrizados. Novos SQLs dinâmicos exigem a
mesma revisão explícita.

**Status:** Implementada e validada localmente; execução remota do workflow permanece gate de release.

---

## 2026-06-20 — Refino estratégico do MVP: inteligência emergente como camada + priorização de fontes

**Área:** Produto / Dados / Fontes / Roadmap / Documentação

**Decisão:**

Após parecer crítico sobre o posicionamento do MVP, foram adotadas as seguintes refinações:

1. **Inteligência emergente como camada, não como recorte de fonte.** O valor de "dados recentes e
   emergentes" vem de uma camada de scoring (`evidence_maturity`, `novelty_score`,
   `clinical_impact_score`, `validation_status`) aplicada sobre fontes confiáveis — não de trocar
   o backbone estruturado por congressos/preprints.

2. **Manutenção do backbone API-first:** ClinicalTrials.gov, PubMed/PMC, openFDA, DailyMed, EMA,
   Open Targets, ANVISA continuam **P1 (MVP)** — transversais a área terapêutica, baratos, com
   API/export oficial, licença clara.

3. **Multi-área desde o início (no backbone).** Pois as fontes P1 são inerentemente transversais.
   A multiplicação por área só encarece congressos — por isso ficam em ondas (MVP+ com ASCO/ESMO/
   ASH primeira; depois AACR, neuro, endócrino, gene/cell, imuno).

4. **Taxonomia de maturidade da evidência:** 8 tiers (preprint → consolidado), sem mistura opaca
   entre preliminar e peer-reviewed/regulatório. Políticas de congresso + preprints + recorte
   temporal por fonte.

5. **Priorização de fontes:** planilha `project_state/fontes_priorizacao.xlsx`, coluna
   `Prioridade`, preenchida manualmente. MVP = P1+P2 (ClinicalTrials + PubMed/MEDLINE/PMC +
   openFDA + EMA + DailyMed + Open Targets + ANVISA + bioRxiv/medRxiv + ASCO/ESMO/ASH). P3 =
   congressos demais + registros complementares. P4 = comercial/fora.

**Motivo:**

O usuário propôs front-load de congressos/preprints em detrimento de regulatório/targets. Parecer
técnico identificou (a) contradição interna (medicina de precisão sem Open Targets?), (b) inversão
perigosa de custo/benefício (congressos são caros e ruidosos; openFDA/EMA/DailyMed são baratos e
confiáveis), (c) oportunidade de posicionar-se como "inteligência emergente" sem sacrificar o
backbone de confiabilidade que é o real diferencial em life sciences.

**Alternativas consideradas:**

- Manter lista proposta de 13+ congressos no MVP: descartado por risco de diluição de qualidade.
- Adiar congressos para pós-MVP: considerado, mas first-mover advantage em ASCO/ESMO/ASH é real;
  compromisso: começar por esses 3 em MVP+.
- Remover preprints inteiramente: descartado; o sinal "emergente" é valioso se bem marcado.

**Impacto:**

- `docs/00` §14: novo trecho sobre posicionamento.
- `docs/02`: seção "Camada de inteligência emergente" documentando campos de scoring.
- `docs/03` §7A–7D: taxonomia de maturidade (8 tiers), política de congressos (ASCO/ESMO/ASH
  primeira onda), política de preprints (opt-out por padrão), recorte temporal por fonte (rolling,
  não rígido).
- `docs/08` Fase 1: scoring integrado no MVP (não adiado).
- `docs/08` Fase 5: congressos em ondas (primeira: ASCO/ESMO/ASH; depois: AACR, neuro, etc.).
- `project_state/fontes_priorizacao.xlsx`: coluna `Prioridade` preenchida (P1: 8 fontes; P2: 6
  fontes; P3: 13 fontes; P4: 6 fontes; "Fase 2": 2 fontes press/SEC).

**Riscos:**

- Desalinhamento futuro entre docs/prosa e planilha se não mantidas sincronizadas; mitigado por
  `docs/03` §4 apontar explicitamente ao `.xlsx` como fonte de verdade.
- Scoring de maturidade é uma feature adicional; pode ser adiado se o MVP ficar acuado; mas o
  parecer recomenda entrar em Fase 1 pois é o diferencial central.

**Próximos passos:**

- Implementar a camada de scoring (campos + lógica de `PersistenceDecisionEngine`).
- Ativar conectores P1 (PubMed, openFDA) conforme planilha.
- Iniciar scraping/parsing de ASCO/ESMO/ASH (MVP+) com políticas de compliance.
- Validar entrega de "inteligência emergente" via ferramentas MCP (`get_emerging_signals`,
  `compare_evidence_maturity`).

**Documentos afetados:**

- `docs/00_CONTEXTO_ESTRATEGICO.md` §14
- `docs/02_MODELO_DE_DADOS.md` nova seção "Camada de inteligência emergente"
- `docs/03_FONTES_E_INGESTAO.md` §7A–7D (taxonomia, congressos, preprints, recorte temporal)
- `docs/08_ROADMAP.md` Fase 1 (scoring) e Fase 5 (congressos em ondas)
- `project_state/fontes_priorizacao.xlsx` coluna `Prioridade` (completa)
- `docs/11_CHANGELOG_DECISOES.md` (este)

**Status:** Implementada na documentação e na planilha.

---

## 2026-07-02 — Reorganização documental: arquivamento de históricos e higiene de estrutura

**Área:** Documentação / Organização do repositório

**Decisão:**
Consolidar os registros históricos em `project_state/archive/`, que já era o local de arquivamento do projeto: `TASKFLOW.md` (raiz) e `docs/MEMORY_FASE_2/5/6.md` foram movidos para lá, sem alteração de conteúdo. A pasta `Referências de Design/` (raiz, com espaços e acentos no nome, sem nenhuma referência no código ou docs) foi movida para `docs/_referencias_design/`, seguindo o padrão de `docs/_fontes_originais/`. O diretório vazio `.agents/` foi removido. O índice `docs/README.md` foi reescrito para mapear docs de área às fases VLAEG e listar os diretórios complementares (`architecture/`, `tools/`, `project_state/`, arquivos históricos e referências).

**Motivo:**
Após a adoção do VLAEG, os históricos sucedidos permaneciam espalhados na raiz e em `docs/`, ao lado dos documentos vivos, dificultando distinguir fonte viva de registro preservado. Nomes de pasta com espaços/acentos na raiz são frágeis para scripts, CI e ferramentas multiplataforma.

**Alternativas consideradas:**
- Excluir os históricos: descartado; `AGENTS.md` §14 exige preservação de histórico.
- Manter tudo no lugar e apenas documentar: descartado; o custo de mover é baixo (arquivos ainda não commitados no git) e o ganho de clareza é imediato.

**Impacto:**
- `project_state/archive/` passa a ser o único local de registros históricos sucedidos.
- Referências atualizadas em `AGENTS.md` §14A, `docs/13_PROTOCOLO_VLAEG.md` (§3 e §5), `project_state/task_plan.md` e `project_state/progress.md`.
- Entradas antigas deste changelog que citam os caminhos anteriores (`TASKFLOW.md`, `docs/MEMORY_FASE_*`) são registros da época e não foram reescritas.

**Documentos afetados:**
- `project_state/archive/TASKFLOW.md`, `project_state/archive/MEMORY_FASE_2/5/6.md` (movidos)
- `docs/_referencias_design/` (movida da raiz)
- `AGENTS.md`, `docs/13_PROTOCOLO_VLAEG.md`, `docs/README.md`, `project_state/task_plan.md`, `project_state/progress.md`
- `docs/11_CHANGELOG_DECISOES.md` (este)

**Riscos:**
- Links externos ou anotações pessoais apontando para os caminhos antigos quebram; mitigado por o repositório ainda não ter commits publicados e pelas referências internas terem sido todas atualizadas (verificado por busca global).

**Status:** Implementada.




## 2026-07-10 - Freios operacionais para a primeira ingestao VPS

**Area:** Ingestao / Operacao / Governanca

**Implementacao:** concluidas as fases de codigo DRY-0 a DRY-4 do plano de correcao. As seis tasks
respeitam `data_sources.is_enabled` em execucao real; dry-run autorizado para a allowlist percorre
fetch, parser e normalizer sem gravar dominio, raw ou cursor; `IngestionJob` e mantido como trilha
auditavel. Foram adicionadas rotas administrativas para ativacao auditada, trigger limitado e
preflight de storage MinIO/S3-compatible.

**Cobertura:** `WarehouseCoverageService` e `GET /api/v1/warehouse/coverage` foram adicionados
como DRY-5. A resposta separa inventário e rastreabilidade de uma alegação de cobertura de mercado
e declara lacunas conhecidas para consumidores administrativos.

**Decisao operacional:** nenhuma fonte foi ativada automaticamente. A sequencia obrigatoria na VPS
e handshake, preflight, dry-run revisado, ativacao individual, smoke-run real e somente entao Beat.
`partial` nao e tratado como falha operacional e nao avanca cursor.

**Validacao:** testes unitarios/integracao dos controles e retry de jobs verdes; execucao real contra
VPS, storage e fontes externas permanece pendente.

---
