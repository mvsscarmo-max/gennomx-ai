
# Arquivo VLAEG v1 - task_plan

## Plataforma GennomX - admin auth e storage segregado (2026-07-10)

Plano local: `project_state/plano_platform_admin_auth_storage.md`. Plano raiz: `../project_state/plans/PLAN-008-plataforma-admin-auth-storage.md`.

| Etapa | Escopo | Estado |
|---|---|---|
| AI-P0 | Reconciliar com trilha JWT proprio + Cloudflare R2 ja em curso | Concluida 2026-07-10; runtime MinIO transitorio inventariado |
| AI-P1 | Validar token da plataforma para dashboard `/ai` com scopes `ai:*` | Preparado 2026-07-10; ainda nao integrado ao dashboard |
| AI-P2 | Manter MCP externo separado da sessao admin | A iniciar |
| AI-P3 | Confirmar buckets/credenciais Cloudflare R2 proprios da AI e preflight de storage | A iniciar |
| AI-P4 | Integrar scopes a ingestao dry-run/run, curadoria e seguranca | A iniciar |
| AI-P5 | Testes auth/MCP/storage/frontend/backend | A iniciar |# project_state / task_plan.md — GennomX AI

## Correcao dos issues de ingestao com dry-run - plano aprovado 2026-07-10

Marcus aprovou corrigir os issues de ativacao da ingestao com **dry-run real** antes de qualquer rodada recorrente ampla. A substituicao de Supabase Auth/JWKS por JWT proprio e Supabase Storage por MinIO/S3-compatible ja esta sendo conduzida por outro agente; este plano deve preservar essa trilha e integrar-se apenas por contrato de storage/auth.

Plano canonico: `project_state/plano_correcao_issues_ingestao_dry_run.md`.

### Etapas planejadas

| Etapa | Escopo | Estado |
|---|---|---|
| DRY-0 | Revalidar fronteiras com a trilha JWT proprio + MinIO antes de tocar em auth/storage | Concluida 2026-07-10: runtime atual e MinIO/S3-compatible; R2 futuro por contrato |
| DRY-1 | Ativacao auditavel dos 6 `data_sources` implementados; manter `anvisa`/`pubmed_pmc` inativos | Implementada em codigo 2026-07-10; fontes permanecem desativadas ate dry-run revisado |
| DRY-2 | Implementar `dry_run` real nas 6 tasks de ingestao, sem persistir entidades/raw/evidencias nem avancar cursor | Implementada em codigo 2026-07-10; pendente execucao real na VPS |
| DRY-3 | Criar disparo admin controlado por fonte com `dry_run`, `max_records` e allowlist de slugs | Implementada em codigo 2026-07-10; pendente execucao real na VPS |
| DRY-4 | Adicionar preflight de storage/env, compativel com provider ativo (Supabase temporario ou MinIO quando concluido) | Implementada em codigo 2026-07-10 para MinIO/S3; pendente preflight real na VPS |
| DRY-5 | Implementar `WarehouseCoverageService`/API para cobertura e qualidade do warehouse | Implementada em codigo 2026-07-10; pendente dados reais na VPS |
| DRY-6 | Agendar pos-processamento (`link_trials_to_assets`, `deduplicate_assets`, `compute_confidence_scores`) apos primeira ingestao validada | Pendente DRY-2/DRY-5 e smoke-run real |
| DRY-7 | Primeiro incremento CT.gov `resultsSection` para endpoints/resultados/adverse events | Pendente backbone estavel |

### Fora de escopo desta correcao

Remover Supabase do runtime, implementar JWT proprio, implementar MinIO/S3-compatible, ANVISA, PMC full-text, congressos, press releases, investor decks, fontes licenciadas e mudancas amplas de arquitetura.

---
## Ingestao recorrente e data warehouse proprietario - plano aprovado 2026-07-09 (cutover VPS autorizado)

Marcus autorizou o cutover para fins de ingestao/operacionalizacao: a ingestao deve acontecer contra o PostgreSQL da VPS, nao mais contra a Supabase (Auth/JWKS/Storage permanecem ativos). Plano canonico: `project_state/plano_ingestao_fase_operacional.md`.

### Etapas planejadas

| Etapa | Escopo | Estado |
|---|---|---|
| INGEST-0 | Diagnostico real do codigo (conectores, tasks, beat, persistencia, storage, entidades) | Concluida 2026-07-09: 6 conectores prontos + 6 tasks + beat_schedule existente; lacunas P1 mapeadas (endpoints/resultados/AD events granulares, empresas, indicacoes, ANVISA) |
| INGEST-1 | Plano operacional + compose de deploy da aplicacao VPS + runbook + `.env.example` + teste de contratos | Concluida 2026-07-09 nesta sessao |
| INGEST-2 | Deploy efetivo na VPS (copiar codigo, `.env` staging, handshake, smoke-run incremental controlado) | Pendente on-VPS (exige SSH + rede de saida + Redis/Storage Supabase validados) |
| INGEST-3 | Ativar beat recorrente e monitorar 24-72h | Pendente INGEST-2 validado |
| INGEST-4 | Complementos ao `beat_schedule`: `link_trials_to_assets`, `deduplicate_assets`, `compute_confidence_scores` | Pendente pos-primeira-ingestao |
| INGEST-5 | Onda 2 lacunas P1: endpoints/resultados/AD events granulares CT.gov resultsSection; ANVISA; normalizador de indicacoes; entity resolution de empresas; PMC full-text | Pendente backbone estavel |
| INGEST-6 | Onda 3 fontes complexas: preprints, congressos, press releases, investor decks, SEC/EDGAR | Pendente Onda 2 |

Orcamento operacional em `plano_ingestao_fase_operacional.md`: diagnostico, ordem racional de ingestao (backbone estruturado antes de fontes ruidosas), camadas raw/processado/curado/current/history sobre o modelo existente (ADR-001), agenda por fonte com frequencia/janela/fila/limites/retries, pre-requisitos (env/rede/gates/git/seguranca), backlog priorizado de workflows/features, riscos e mitigacao, criterios de aceite verificaveis e plano por fases pequenas com comandos e rollback.

---

## Migracao do banco Supabase PostgreSQL para PostgreSQL na VPS - plano 2026-07-09

Marcus decidiu substituir o PostgreSQL hospedado da Supabase por PostgreSQL/pgvector hospedado diretamente na VPS. A migracao deve ser faseada: **banco primeiro**, mantendo Supabase Auth/JWKS e Supabase Storage temporariamente ate decisoes especificas posteriores.

Plano canonico: `project_state/plano_migracao_supabase_postgres_vps.md`.

### Etapas planejadas

| Etapa | Escopo | Estado |
|---|---|---|
| PGVPS-0 | Confirmar escopo: migrar somente banco; manter Auth/Storage Supabase temporariamente | Concluida 2026-07-09 |
| PGVPS-1 | Inventario do Supabase atual: versao, extensoes, `alembic_version`, contagens, grants/RLS | Concluida 2026-07-09 (segunda sessao): MCP Supabase ativo; projeto restaurado; inventario real coletado via `execute_sql` read-only. Origem: PostgreSQL 17.6, `alembic_version=0005`, `vector=0.8.0`, 28 tabelas, 27 RLS, 60 policies, 8 data_sources (todas inactive, sem ingestao), 5 retention_policies, demais 26 tabelas vazias. Schemas/roles Supabase-specific identificados para nao migrar. Banco 12 MB |
| PGVPS-2 | Provisionar PostgreSQL/pgvector na VPS com rede privada, TLS, volume e backup | Parcialmente concluida em staging: `gennomx-ai-postgres-ready` rodando healthy, sem porta publicada, com TLS interno; backup offsite ainda pendente |
| PGVPS-3 | Bootstrap de roles `gennomx_app`, `gennomx_worker`, `gennomx_migrator`, `gennomx_readonly` e Alembic `head` | Concluida em staging 2026-07-09: Alembic aplicado ate `0006`, grants reaplicados e roles/extensoes/RLS validados |
| PGVPS-4 | Dump/restore em staging e validacao de contagens/checksums | Dispensavel 2026-07-09: inventario mostrou que Supabase so tem dados de seed (`data_sources`/`retention_policies`) ja semeados pelas proprias migracoes Alembic 0001/0004 com `ON CONFLICT DO NOTHING` e reproduzidos no alvo. Demais 26 tabelas vazias. `pg_dump --data-only` acrescentaria risco operacional sem beneficio. Comparacao conceitual: origem e alvo tem as mesmas seeds funcionais; alvo a frente em `0006` com `llm_call_logs`. Limitacao: UUIDs de `data_sources` diferem (aleatorios por migracao), irrelevante porque app referencia por `slug` |
| PGVPS-5 | Testes de aplicacao contra PostgreSQL VPS mantendo Supabase Auth/Storage | Config preparada; bloqueada nesta sessao: VPS Postgres em rede Docker interna nao alcancavel desta maquina. Validar requires backend up on-VPS ou tunnel |
| PGVPS-6 | Cutover controlado com pausa de ingestao, backup final, restore final e rollback pronto | Autorizado para fins de ingestao/operacionalizacao (2026-07-09, Marcus): ingestao contra PostgreSQL VPS. Deploy efetivo + cutover produtivo (ENVIRONMENT=production) ainda exigem runbook on-VPS validado |
| INGEST-1 | Operacionalizar ingestao recorrente dos 6 conectores contra PostgreSQL VPS | Plano + artefatos prontos (2026-07-09): `project_state/plano_ingestao_fase_operacional.md`; `infra/docker-compose.vps-app.yml` (Redis+worker+beat+API) com teste de contratos; `.env.example` e `docs/09` runbook atualizados. Pendente on-VPS: copiar codigo, preencher `.env` staging, handshake, smoke-run, up beat |
| PGVPS-7 | Pos-cutover: docs/env/backups/monitoramento e plano posterior para Auth/Storage | Parcial: docs/env/runbook preparados; pos-cutover real pendente |

### Impacto no plano de data warehouse

A ativacao produtiva pesada da ingestao recorrente deve ocorrer **depois** do cutover do banco para PostgreSQL VPS. DW-1/DW-2 podem fazer diagnostico/dry-run com cautela, mas a nova fonte de verdade deve ser a VPS antes de rodar ingestao recorrente em escala.

### Registro de continuidade — 2026-07-09

Rodada de hardening sem credenciais reais: `bootstrap_roles_vps.sql` agora reaplica senhas por variaveis `psql`, usa `current_database()` em vez de banco hardcoded e concede sequences a `gennomx_readonly` para backup/inspecao. `docker-compose.postgres-vps.yml` exige TLS tambem no servico `backup`. Teste unitario novo (`test_postgres_vps_artifacts.py`) trava esses contratos. Inventario real, provisionamento, restore e cutover seguem pendentes.

### Registro de provisionamento VPS — 2026-07-09

VPS Hostinger `1817951` recebeu firewall `gennomx-ai-vps-public-ingress` (`325948`) sincronizado, permitindo apenas SSH/HTTP/HTTPS/ICMP de entrada. Stack segura de banco `gennomx-ai-postgres-ready` foi criada e esta healthy, com `pgvector/pgvector:0.8.1-pg16`, TLS interno, rede Docker interna e sem `ports:`. Bootstrap concluiu (`Exited (0)`) com extensoes e roles dedicadas. Na continuidade aprovada, os projetos intermediarios e o legado `postgresql-spko` foram removidos. Bloqueios remanescentes apos Alembic staging: MCP Supabase nao exposto, inventario Supabase, dump/restore e comparacao.

### Registro de Alembic staging — 2026-07-09

Alembic `head` foi aplicado no PostgreSQL VPS staging por SQL offline compactado em dois chunks e executado por projeto Docker temporario na rede `gennomx-ai-postgres-ready-private`, sem publicar `5432`. Resultado validado: `alembic_version=0006`, extensoes `pg_trgm=1.6`, `pgcrypto=1.3`, `uuid-ossp=1.1`, `vector=0.8.1`, roles `gennomx_app`, `gennomx_migrator`, `gennomx_readonly`, `gennomx_worker` com `rolsuper=false` e `rolbypassrls=false`, 27 tabelas com RLS, 60 policies, 29 tabelas publicas e `data_sources=8`. Grants gerais e inserts de auditoria para `gennomx_app` foram reaplicados. Inventario/dump/restore Supabase e comparacao seguem bloqueados por ausencia de MCP Supabase e URL direta funcional.

### Registro de inventario real Supabase via MCP — 2026-07-09 (segunda sessao)

MCP Supabase esta disponivel nesta sessao. Projeto `qfanrziwepkqkgtvfrdt` estava `INACTIVE` (pausado) e foi restaurado para `ACTIVE_HEALTHY` (reversivel; Marcus pode repausar). Inventario real coletado:

- PostgreSQL 17.6; banco 12 MB.
- `alembic_version = 0005` (alvo VPS em `0006`).
- Extensao `vector=0.8.0` (alvo em `0.8.1`); demais compativeis.
- 28 tabelas publicas; 27 RLS; 60 policies.
- Roles `gennomx_app`, `gennomx_migrator`, `gennomx_readonly`, `gennomx_worker` com `rolsuper=false`/`rolbypassrls=false`.
- Schemas/roles Supabase-specific a NAO migrar: `auth`, `graphql`, `graphql_public`, `realtime`, `storage`, `vault`, `extensions`; roles `anon`, `authenticated`, `service_role`, `supabase_admin`, `supabase_auth_admin`, `supabase_storage_admin`.
- Contagens: `data_sources=8` (todas inactive, sem ingestao); `retention_policies=5`; demais 26 tabelas = 0.

Decisao: `pg_dump --data-only`/`pg_restore` fica dispensavel porque a origem so tem seeds ja replicados no alvo pelas proprias migracoes Alembic (`0001`+`0004`, `ON CONFLICT DO NOTHING`). Comparacao e conceitual; `tools/compare_postgres_migration.py` nao foi executado porque nao houve restore. UUIDs de `data_sources` diferem entre origem e alvo (aleatorios por migracao), irrelevante porque app referencia por `slug`. Aplicacao (`backend`/pytest) contra VPS DB nao foi validada nesta sessao pois o Postgres da VPS esta em rede Docker interna nao alcancavel desta maquina. Cutover produtivo permanece nao executado por restricao do Marcus. Projeto Supabase segue `ACTIVE_HEALTHY` ao final da sessao.

---

### Registro de correcao MCP Supabase — 2026-07-09

MCP Supabase foi corrigido/autenticado localmente. No Codex, `codex mcp login supabase` concluiu via OAuth e a entrada `supabase` deixou de exigir `SUPABASE_ACCESS_TOKEN`, passando a `auth_status=o_auth`. No OpenCode, a entrada ativa foi trocada de `mcp-server-supabase` local sem token para o MCP remoto oficial e `opencode mcp auth supabase` concluiu; `opencode mcp list` mostra `supabase connected`. A sessao atual ainda nao injeta ferramentas novas dinamicamente, entao o inventario real deve ser retomado em nova sessao.

---

## Data warehouse e ingestao recorrente - plano aprovado 2026-07-09

Marcus aprovou o inicio da construcao operacional do banco/data warehouse da GennomX AI, partindo do estado real ja implementado: conectores `clinicaltrials_gov`, `pubmed`, `openfda`, `dailymed`, `open_targets` e `ema`; schema PostgreSQL/Supabase; raw storage; evidencias; Celery/Redis; MCP read-only; dashboard e governanca temporal.

Plano canonico: `project_state/plano_data_warehouse_ingestao.md`. Prompt de continuacao para outro agente: `project_state/prompt_implementacao_dw_etapas_1_4.md`.

### Escopo aprovado para inicio

| Etapa | Escopo | Estado |
|---|---|---|
| DW-1 | Diagnostico e inventario real do banco, conectores, jobs, MCP e ambiente | A iniciar |
| DW-2 | Ativacao controlada dos conectores existentes com handshake/dry-run/execucao limitada e validacao de idempotencia | A iniciar |
| DW-3 | Contrato e camada inicial de qualidade/cobertura do warehouse (`WarehouseCoverageService`/API/dashboard se couber) | A iniciar |
| DW-4 | Granularidade clinica inicial: planejamento tecnico e primeiro incremento seguro para endpoints/resultados/safety | A iniciar |

### Fora de escopo da primeira rodada

ANVISA, PMC full-text, congressos, press releases, investor decks, fontes licenciadas, OpenSearch, vector DB dedicado, API comercial/billing, chatbot ou geracao final interna de relatorios.

### Cadencia alvo

Backbone diario: ClinicalTrials.gov, PubMed, openFDA, DailyMed e freshness. Backbone semanal: Open Targets, EMA, retencao e qualidade/cobertura. Fontes event-driven entram apenas em ondas posteriores, apos estabilidade do backbone estruturado.

---

## Descomissionamento total da Supabase - plano aprovado 2026-07-09

Marcus aprovou remover a Supabase por completo do runtime da GennomX AI. O banco principal ja foi cortado para a VPS; agora a migracao final substitui Auth/JWKS e Storage por componentes proprios.

Plano canonico: `project_state/plano_remocao_supabase_jwt_minio.md`.

### Etapas planejadas

| Etapa | Escopo | Estado |
|---|---|---|
| SUPA-0 | Mapear usos remanescentes de Supabase no backend/frontend/docs | Concluida na analise inicial |
| SUPA-1 | Implementar JWT proprio no backend e middleware/frontend | Concluida |
| SUPA-2 | Substituir raw payload por MinIO/S3-compatible | Concluida |
| SUPA-3 | Remover `@supabase/*`, `supabase` Python e envs antigas | Concluida |
| SUPA-4 | Atualizar docs, changelog, progress e runbook | Em andamento |
| SUPA-5 | Validar login, rotas protegidas, upload raw e deploy | Concluida |

### Observacao operacional

O front-end e o backend ja leem `AUTH_*`/`MINIO_*` e usam JWT proprio + MinIO no caminho de login e storage. A pendencia restante desta etapa e alinhar a documentacao operacional/historica ao novo runtime.

---

## Preparação do deploy do MVP — plano aprovado 2026-07-02

Análise do estado real (código, não documentação) confirmou: 9 ferramentas MCP completas,
conectores ClinicalTrials.gov/PubMed/openFDA/DailyMed/Open Targets/EMA implementados, dashboard
Next.js real (13 telas) com auth Supabase/RBAC, CI com 8 gates, banco Supabase real bootstrapado
e migrado até `0005`. Lacunas originalmente identificadas: conectores P1 faltantes, tabela
`regulatory_approvals` sem fonte, ausência de infra de deploy, migração `0006` não aplicada em
produção e hardening MCP/Redis remoto.

Decisões do usuário: escopo = todos os conectores P1; topologia F4 = GennomX AI sob `gennomx.com`
(`admin.gennomx.com/ai`, `admin.gennomx.com/api/ai`, `mcp.gennomx.com`); prioridade = fechar
conectores primeiro, depois prontidão de deploy.

Plano completo: `C:\Users\marcu\.claude\plans\analise-o-projeto-e-replicated-marshmallow.md`.

### Onda A — Conectores P1 (padrão VLAEG replicando o conector PubMed)

| Conector | Popula | Ordem | Estado |
|---|---|---|---|
| openFDA | `regulatory_approvals` (FDA), enriquece `search_drugs` | 1 | ✅ Implementado 2026-07-02 |
| DailyMed | `regulatory_approvals` (label_url, SPL) | 2 | ✅ Implementado 2026-07-02 |
| Open Targets | `targets`, associações alvo↔ativo | 3 | ✅ Implementado 2026-07-02 |
| EMA | `regulatory_approvals` (EMA/EU) | 4 | ✅ Implementado 2026-07-02 |

Detalhe: `docs/03_FONTES_E_INGESTAO.md` §0.2C–0.2F (contratos) e §6.8C (estado implementado);
`docs/09_DEPLOY_E_OPERACAO.md` §0.1B (automação); `docs/11_CHANGELOG_DECISOES.md` 2026-07-02.
39 testes novos, suíte completa 223 passed/2 skipped ambientais. Onda A concluída.

Cada conector: `workers/connectors/<slug>/` (connector+parser+normalizer) → persistência
reaproveitando `workers/persistence/common.py`/`evidence.py` (+ `regulatory.py`/`targets.py` novos)
→ task Celery em `ingest.py` → beat schedule em `celery_app.py` → registro em `tools/handshake.py`
→ migração Alembic de `data_sources.<slug>` → testes unitários (parser/normalizer/healthcheck/
persistence_flow) → docs (`docs/03`, `docs/04`, `docs/09` §0.2, `docs/11`) → planilha de priorização.

### Onda B — Prontidão de deploy (após Onda A)

| Item | Estado |
|---|---|
| Retry manual para todos os conectores P1 implementados | ✅ Implementado 2026-07-02 |
| `API_ALLOWED_HOSTS` configurável / sem domínio hardcoded | ✅ Implementado 2026-07-02 |
| Stack backend GennomX AI sob `admin.gennomx.com/api/ai` + `mcp.gennomx.com` (API + worker + beat + Redis TLS) | ✅ Base implementada 2026-07-02 |
| Planilha `fontes_priorizacao.xlsx` com P1 implementados | ✅ Atualizada 2026-07-02 |
| Git/segredos (primeiro commit, `.env` fora do versionamento) | ⏳ Pendente de ação operacional |
| `alembic upgrade head` real em Supabase produção (`0006`) | ⏳ Pendente de credenciais/rede |
| Frontend em `admin.gennomx.com/ai` | ⏳ Pendente de provisionamento |
| `make release-check` e `make handshake` em ambiente com rede | ⏳ Pendente de execução externa |
| Observabilidade/backup e rotação formal de tokens MCP | ⏳ Pendente de operação |

---

## Integração Supabase — 2026-06-23

| Entrega | Estado |
|---|---|
| Normalizar URLs Supabase para asyncpg/psycopg2 | ✅ |
| Configurar `.env.example` para Supabase hospedado | ✅ |
| Criar bootstrap SQL de roles, extensões e grants | ✅ |
| Documentar ativação e segurança operacional | ✅ |
| Aplicar bootstrap/migrações no projeto Supabase real | ✅ Alembic `0005` verificado |

## Fase 11 — Motor LLM OPENCODE — 2026-06-23

| Entrega | Estado |
|---|---|
| Decisão de não executar benchmark comparativo | ✅ |
| Planejamento de integração OPENCODE + DeepSeek V4 Pro | ✅ `project_state/plano_fase_11_llm_opencode.md` |
| Handshake OPENCODE antes da lógica final | ✅ `tools/handshake_llm.py` + `make handshake-llm` |
| Serviço interno LLM com schema validation e auditoria | ✅ `backend/app/services/llm/` (client, service, schemas, errors) |
| Migração/logs de chamadas LLM | ✅ `0006_llm_call_logs.py` + model `LLMCallLog` |
| Testes unitários LLM (config, client, service, injection) | ✅ `backend/tests/unit/test_llm_module.py` |
| Atualização de docs stack/segurança/testes/operação | ✅ `.env.example`, `config.py`, `Makefile` atualizados |

## Conector PubMed — 2026-06-23

| Entrega | Estado |
|---|---|
| Config (PUBMED_API_BASE_URL, max retries, lookback, default query, ingest hour) | ✅ |
| Connector (ESearch/EFetch/ELink, paginação WebEnv, rate limit, retry tenacity) | ✅ |
| Parser (PM/DOI/PMCID/title/abstract/journal/authors/keywords/NCT DataBank) | ✅ |
| Normalizer (publication_type controlado, evidence_maturity, registry_source) | ✅ |
| Task Celery (run_pubmed_ingest + _persist_publications) | ✅ |
| SourceDocument + EvidenceSnippet + NCT linking | ✅ |
| Migração 0005 (data_sources `pubmed`) | ✅ |
| Handshake + beat schedule diário | ✅ |
| Testes unitários (healthcheck, parser, normalizer, persistence flow) | ✅ |
| Documentação (docs/03 §0/0B/6.8B, docs/04, changelog) | ✅ |

## Fechamento operacional dos passos aprovados — 2026-06-21

| Bloco | Evidência executável | Estado |
|---|---|---|
| Política de atualização | registry + `AssertionService` + motor determinístico + freshness job | ✅ |
| Granularidade | chaves obrigatórias + índices correntes para dados granulares | ✅ |
| Metadados | migração `0004`, checks, expiração, maturidade e validação | ✅ |
| Pré-gravação | DuckDB em duplicatas, quality gates, evidence e decisão | ✅ |
| Edição/correção | proposta/revisão admin, supersession e assertion curada | ✅ |
| Retenção/exclusão | policies, legal hold, manifesto, checksum, arquivo antes de delete | ✅ |
| Scraping controlado | allowlist/SSRF/rate/concorrência/sanitização/kill switch/painel | ✅ |
| Passo 11 — modelos LLM | ✅ implementado como OPENCODE + DeepSeek V4 Pro, sem benchmark |

## Remediação do parecer externo — 2026-06-21

| Entrega | Estado |
|---|---|
| Corrigir persistência crítica + falha silenciosa | ✅ |
| Testar fluxo real insert/update/noop/falha | ✅ fluxo de persistência coberto nos quatro casos |
| Tratar limite de lote como parcial | ✅ |
| Forçar roles PostgreSQL/RLS efetivo | ✅ |
| Remover chave admin/cache do SSR | ✅ |
| Remover auth morta e comparação não constante | ✅ |
| Unificar runner assíncrono | ✅ |
| Dedup/confidence determinísticos | ✅ |
| Validar endpoint MCP HTTP, toolchain, caches e gates | ✅ 104 passed, 1 skip ambiental |
| Passo 11 — seleção de LLM | ✅ OPENCODE + DeepSeek V4 Pro, motor implementado |

## Programa de governança temporal — 2026-06-20

| Passo | Entrega | Estado |
|---|---|---|
| 1 | ADR bitemporal e precedência | ✅ |
| 2 | Matriz de granularidade, autoridade e freshness | ✅ |
| 3 | Assertions, conflitos e correções | ✅ |
| 4 | Metadados temporais/current/supersession | ✅ |
| 5 | `PersistenceDecisionEngine` determinístico | ✅ |
| 6 | Proteção contra regressão temporal CT.gov | ✅ |
| 7 | Estágio corrente, máximo histórico e status | ✅ |
| 8 | Relação trial↔ativo temporal; demais relações por conector | ✅ MVP |
| 9 | Evidência por campo crítico CT.gov | ✅ |
| 10 | Staging DuckDB integrado e quality gates | ✅; gate local DuckDB pula no Python 3.14 sem pacote |
| 11 | Motor LLM OPENCODE, sem benchmark comparativo | ⏳ Planejado |
| 12 | Retenção, particionamento e arquivamento | ✅ |
| 13 | Compliance formal de scraping | ✅ |
| 14 | Testes temporalidade/conflito/reprocessamento | ✅ |

Próxima evolução: expandir o padrão temporal para indications, sponsors, locations, endpoints e
resultados à medida que os respectivos conectores forem ativados; o modelo já suporta a expansão.

**Fonte única de plano de execução.** Sucede `TASKFLOW.md` (preservado como histórico em `project_state/archive/TASKFLOW.md`).
**Protocolo de referência:** VLAEG (`docs/13_PROTOCOLO_VLAEG.md`).

> Premissa central (`AGENTS.md` §1): a GennomX AI é infraestrutura proprietária de dados biomédicos + MCP. Não é chatbot nem geradora final de relatórios.

---

## Fases de implementação (status)

| Fase | Escopo | Status |
|---|---|---|
| Fase 0 | Scaffold do monorepo, Docker Compose, `.env.example`, `Makefile`, tooling | ✅ Concluída |
| Fase 1 | Schema PostgreSQL + Alembic + entidades canônicas + evidências | ✅ Concluída (`0001_initial_schema.py`) |
| Fase 2 | Backend FastAPI: serviços, schemas Pydantic, endpoints, MCP, conector CT.gov | ✅ Concluída |
| Fase 3 | Workers Celery + Redis + DuckDB + JobTracker | ✅ Implementada; teste DuckDB local depende de ambiente Python suportado |
| Fase 4 | Conector ClinicalTrials.gov completo (parser, normalizer, evidências, linking) | ✅ Concluída |
| Fase 5 | Servidor MCP read-only + 9 ferramentas + auth + rate limit + logs | ✅ Concluída |
| Fase 6 | Frontend Next.js: Design System, layout, overview, assets, trials, sources | ✅ Concluída (MVP) |
| Fase 7 | Testes + CI/CD + conectores adicionais (PubMed, openFDA, DailyMed, Open Targets, EMA) | ✅ Todos os conectores P1 implementados (2026-07-02); ANVISA pendente |

Detalhe histórico por fase: `project_state/progress.md`.

---

## Adoção do Protocolo VLAEG (em curso)

Trilho A — overlay de governança:
- [x] `docs/13_PROTOCOLO_VLAEG.md` (mapeamento de fases e docs)
- [x] `project_state/` (task_plan, progress, findings)
- [ ] Contratos de dados em `docs/03` e `docs/04`
- [ ] Declarações de automação + runbook de autocorreção em `docs/09`
- [ ] Atualização de `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` e changelog `docs/11`

Trilho B — correções de engenharia expostas pelo VLAEG:
- [ ] Fase L (Link): `BaseConnector.healthcheck()` + CT.gov + `tools/handshake.py` + teste
- [ ] Fase G (Gatilho): `beat_schedule` no Celery + `Makefile` + endpoint healthcheck
- [ ] `tools/` determinístico e `architecture/` POPs

---

## Próximas entregas do roadmap (pós-VLAEG)

Ordem canônica em `docs/08_ROADMAP.md` (§23.1), exceto novos conectores de fonte de dados, cuja ordem é definida pela coluna `Prioridade` (preenchida manualmente pelo usuário) em **`project_state/fontes_priorizacao.xlsx`** — essa planilha Excel é a premissa viva do projeto para priorização de fontes. Demais prioridades imediatas:

1. Conectores adicionais — seguir `Prioridade` de `project_state/fontes_priorizacao.xlsx`, reutilizando `BaseConnector` + `healthcheck()`.
2. Medir volume/latência do staging DuckDB e calibrar limiares com fixtures reais, sem habilitar
   merge automático; isto é otimização/calibração, não lacuna funcional.
3. Schemas Pydantic tipados para `Company`, `Trial`, `Indication`.
4. Autenticação Supabase no frontend + páginas stub (companies, indications, targets, jobs, mcp-logs, security).
5. Testes: services restantes, 9 tools MCP, conectores com `httpx.MockTransport`, Playwright e2e.

---

## Critérios de conclusão do MVP

Referência completa: `docs/08_ROADMAP.md` §22. Resumo: fontes prioritárias integradas, rastreabilidade fonte→dado→evidência funcional, MCP consultável por modelos host com logs completos, segurança/testes como requisitos de primeira classe, jobs reexecutáveis e agendados.

---

## Programa de correção técnica — 2026-06-20

| Fase | Critério verificável | Estado |
|---|---|---|
| 1. Identidade e configuração | produção falha fechada; JWT valida issuer/audience; dashboard envia sessão | ✅ Implementada; gates finais pendentes |
| 2. MCP | transporte MCP padrão, escopos e rate limit distribuído | ✅ Implementada; gate integrado na fase 5 |
| 3. Ingestão e evidência | incremental real, retry, isolamento transacional e raw payload recuperável | ✅ Implementada; gate integrado na fase 5 |
| 4. Dados e operação | constraints/FKs, readiness, menor privilégio e imagens reproduzíveis | ✅ Implementada; migração real validada pela CI |
| 5. Dashboard e qualidade | telas operacionais, testes API/MCP/E2E e CI executável | ✅ Implementada; gates locais aprovados |

### Encerramento do programa de correção

As cinco fases foram implementadas. O backlog remanescente é evolução de produto — novos
conectores conforme `fontes_priorizacao.xlsx`, DuckDB/deduplicação, busca global e edição
corretiva — e não correção dos achados críticos deste programa.

---

# Plano de Implementação para Correção dos Issues — 2026-07-02 (Revisão técnica sênior)

## Objetivo
Corrigir os achados da revisão técnica de 2026-07-02, priorizando coerência
funcional do dashboard/API e reforço de governança, sem regressões e sem
remover rastreabilidade/testes (AGENTS.md §9, §13).

## Premissas
- Achados críticos anteriores já tratados (findings.md, Programa 2026-06-20).
- Correções pequenas, rastreáveis e reversíveis (AGENTS.md §14).
- A confirmar antes de implementar: (a) semântica desejada de `phase` para
  ativos (mapear para `development_stage` vs. remover o parâmetro); (b) se
  segregação de funções em correções é requisito de MVP.

## Escopo
Corrige A1–A7 (abaixo). Fora de escopo: novos conectores, DuckDB/dedup,
busca global, seleção de modelos LLM (passo 11 segue diferido).

## Issues a Corrigir
- Média: A1 endpoint /overview ausente; A2 filtro phase ignorado; A3 sem
  segregação de funções em correções; A5 ausência de commit/CI nunca executado.
- Baixa/Média: A4 SSRF DNS-rebinding no scraper.
- Baixa: A6 can_write/worker mortos; A7 LLMClient sem close.

## Etapas de Implementação

### Etapa 1 — Correções críticas
(Sem itens críticos remanescentes; achados críticos anteriores já encerrados.)
- [x] Confirmar, com suíte completa verde, que nenhum crítico reaparece.
- Critério de aceite: `pytest` + `npm run build`/`typecheck` sem erros. ✅ confirmado.

### Etapa 2 — Correções de alta prioridade (funcional + processo)
- [x] A1: `GET /api/v1/overview` implementado (`OverviewService` + `app/api/v1/overview.py`,
      agregação em query única). Dashboard consome via `fetchServerOverviewStats`.
      Aceite atingido: dashboard exibe totais reais (validado por teste de integração
      da rota); validação manual em navegador **não** foi feita nesta rodada.
- [x] A2: `phase` aplicado em `asset_service.list_assets` (`da.development_stage = :phase`).
      Achado adicional durante a correção: o vocabulário do dropdown de fase no frontend
      (`PHASE_1`) nunca correspondia ao vocabulário real (`PHASE1`, sem underscore) —
      afetava também o filtro de **trials** e a legenda `phaseLabel` (exibia o código cru
      em vez de "Fase I" etc. em produção). Os três foram corrigidos.
- [ ] A5: **adiado a pedido do usuário.** Preparação feita (nada bloqueando: `.gitignore`
      cobre `.env`/`secrets/`), mas o primeiro commit não foi criado — repositório
      segue sem nenhum commit. Ponto em aberto: decidir se `.claude/` e `.impeccable/`
      entram no primeiro commit ou vão para o `.gitignore` (local tool state).

### Etapa 3 — Melhorias de testes
- [x] Teste de contrato para a visão geral: `test_overview_service.py` (unit, vazio e com
      dados) + `test_overview_route.py` (integração via ASGI real).
- [x] Teste unitário do filtro `phase`: `test_asset_service.py::test_applies_phase_filter`.
- [x] Teste de governança de correção: `test_correction_service.py` (reviewer==requester
      bloqueado, reviewer distinto aprova, correção inexistente) +
      `test_corrections_review_route.py` (mesmos casos via HTTP real, 403/404).
- [x] Teste de SSRF/rebinding: escopo ajustado para a função pura de pinning
      (`test_pin_request_to_address_*` em `test_operational_governance.py`), não um
      teste e2e completo de `ControlledScraper.fetch` com `httpx.MockTransport`
      (feature de scraping ainda inativa em produção).

### Etapa 4 — Melhorias de arquitetura/manutenção/qualidade
- [x] A3: `CorrectionService.review` recusa quando `reviewer == requested_by`
      (`AuthorizationError`, four-eyes). Arquivo: `correction_service.py`.
- [x] A4: DNS-rebinding mitigado — `validate_scrape_url` retorna os IPs validados;
      `ControlledScraper.fetch` conecta ao IP pinado com `Host`/SNI no hostname
      original (`_pin_request_to_address`). Arquivo: `scraping_policy.py`.
- [x] A6: `can_write`/papel `worker` removidos (nunca usados por nenhuma rota;
      `require_admin` já cobria toda escrita). Arquivo: `auth/dependencies.py`.
- [x] A7: `LLMClient`/`LLMService` ganharam `close()` + `__enter__`/`__exit__`.
      Arquivos: `services/llm/client.py`, `services/llm/service.py`.

**Achado extra corrigido, fora da lista original (necessário para A3 funcionar de
verdade):** não havia handler global de exceções — `NotFoundError`/`AuthorizationError`
etc. levantados pelos serviços viravam **500 genérico** em vez de 404/403. Registrado
`exception_handler(GennomXError)` em `app/main.py`.

**Débito técnico pré-existente também corrigido nesta rodada** (não fazia parte de
A1–A7, mas bloqueava os gates de CI que A5 depende de deixar verdes):
- Bandit (médio): XXE em `pubmed/connector.py` — `xml.etree.fromstring` trocado por
  `defusedxml.ElementTree.fromstring`; achado colateral: `query_key is None` não era
  checado antes de paginar (corrigido junto).
- mypy: 20 erros pré-existentes em 7 arquivos (`persistence/assets.py`,
  `auth/dependencies.py`, `services/llm/service.py`+`schemas.py`, `api/v1/assets.py`,
  `persistence/trials.py`+`publications.py`, `pubmed/connector.py`, `api/v1/governance.py`)
  — todos corrigidos na raiz (sem `# type: ignore`), zero erros restantes.
- Formatação: `ruff format` aplicado a 10 arquivos com drift pré-existente que
  quebrariam o gate `ruff format --check` do CI.

### Etapa 5 — Validação final
- [x] `pytest tests/unit tests/integration` (backend) verde — 238 testes, 2 skips
      ambientais (Python 3.14 sem DuckDB/bs4, já documentado em `findings.md`).
- [x] `npm run lint && npm run typecheck && npm run build` (frontend) verde.
- [x] `ruff check . && ruff format --check . && mypy app workers` + `bandit`/`pip-audit`
      — todos verdes (mypy e bandit exigiram a limpeza de débito técnico acima).
- [x] `npm run test:e2e` (Playwright) verde — 7/7.
- [ ] Validar manualmente o dashboard (KPIs reais) e um fluxo MCP autenticado em
      navegador/servidor real — **não executado** (sem ambiente rodando nesta sessão).
- [ ] Atualizar docs afetadas (`docs/05_SEGURANCA_E_GOVERNANCA.md` — four-eyes e SSRF;
      `docs/07_DASHBOARD_UX.md` — overview/filtro de fase) e
      `docs/11_CHANGELOG_DECISOES.md`/`findings.md` conforme AGENTS.md §14 —
      **pendente**.

## Critérios de Aceite Gerais
Dashboard sem KPIs falsamente zerados ✅; filtros expostos sempre funcionais ✅;
governança de correção com segregação ✅; scraper resistente a rebinding ✅; CI real
verde no GitHub ⏳ (depende do commit/push, A5 adiado); nenhuma regressão ✅
(suíte completa); rastreabilidade/testes preservados ✅.

## Riscos da Implementação
- Mudar semântica de `phase`/overview pode afetar e2e — mitigar com seed
  determinístico. Primeiro push pode revelar falhas de CI antes ocultas —
  mitigar tratando o pipeline como gate. Alteração no scraper é de feature
  inativa — baixo risco de regressão em produção.

## Checklist Final
- [x] Problemas de média prioridade corrigidos (A1, A2, A3); A5 preparado mas não
      executado (commit adiado a pedido do usuário)
- [x] SSRF rebinding mitigado (A4)
- [x] Código morto/recursos tratados (A6, A7)
- [x] Testes adicionados/ajustados
- [x] Regressões verificadas (suíte completa)
- [ ] Documentação atualizada (docs/05, docs/07, docs/11, findings.md — pendente)
- [x] Projeto apto para nova revisão técnica (código); commit/push e docs seguem
      como pendências operacionais isoladas, não bloqueiam revisão de código

**Estado de execução — 2026-07-02, pós-implementação.** Todas as correções de código
(A1–A4, A6, A7) e o débito técnico de CI colateral (mypy, bandit, formatação) foram
implementados e validados localmente. A5 (primeiro commit) fica a critério do usuário.
Pendências remanescentes: validação manual em ambiente rodando e atualização de
documentação (docs/05, docs/07, docs/11, findings.md).

