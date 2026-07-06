# project_state / progress.md — GennomX AI

## PLAN-003 (raiz): bloqueio do compose legado + documentação da topologia atual — 2026-07-06

Trabalho executado a partir do PLAN-003 do workspace raiz
(`project_state/plans/PLAN-003-correcao-issues-revisao-tecnica.md`). Achado: `infra/docker-compose.prod.yml`
ainda publica Caddy em `80:80`/`443:443` para um domínio próprio (`api.gennomx.ai`), topologia
substituída em 2026-07-04 pela decisão D-011 do workspace raiz (GennomX AI passa a viver sob
`gennomx.com`: hub `admin.gennomx.com/ai`, API `admin.gennomx.com/api/ai`, MCP `mcp.gennomx.com`,
atrás do Traefik já compartilhado com outro projeto na VPS — F-006 da raiz). A F4 (migração real
para essa topologia: `basePath=/ai`, `API_ALLOWED_HOSTS`/CORS de `gennomx.com`) **continua pendente**
— por decisão explícita de não fazer uma migração grande sem necessidade confirmada, esta rodada
tratou apenas do mínimo aceitável: impedir uso acidental do compose legado.

- `infra/docker-compose.prod.yml`: adicionado cabeçalho de aviso explicando que o arquivo é legado
  nessa topologia e por quê (disputaria portas 80/443 do Traefik compartilhado).
- `Makefile`: `prod-up` agora recusa subir `docker-compose.prod.yml` sem a variável de ambiente
  `ACKNOWLEDGE_LEGACY_TOPOLOGY=yes`, imprimindo a topologia atual esperada e onde ler mais
  (`docs/09_DEPLOY_E_OPERACAO.md`). Uso legítimo (ambiente isolado, sem Traefik/gennomx.com
  compartilhado) permanece possível com o ack explícito.
- `docs/09_DEPLOY_E_OPERACAO.md`: nota datada de 2026-07-06 na seção "Stack produtiva mínima"
  marcando-a como registro histórico da topologia `api.gennomx.ai` (aprovada em 2026-07-02), não
  como plano ativo, e apontando para a F4 do PLAN-002 da raiz como o caminho de migração real.

**Auditoria de `.env`/segredos (sem expor valores):** confirmado via `git status --ignored` que
`.env`, `backend/.env` e `frontend/.env.local` estão corretamente listados como ignorados pelo
`.gitignore` local; `.env.example` (raiz do app) não está coberto por regra de ignore. Este
repositório segue **sem nenhum commit** (decisão do fundador em 2026-07-02, ver A5 em
"Preparação do deploy do MVP" abaixo) — o achado relevante é que, quando o primeiro commit for
feito, os `.env` reais não serão incluídos por acidente.

**Validação:** `npm audit --audit-level=moderate` em `frontend/` → 0 vulnerabilidades. Guard do
`make prod-up` testado simulando a lógica do shell fora do `make` (não havia `make` disponível no
ambiente desta sessão): bloqueia sem `ACKNOWLEDGE_LEGACY_TOPOLOGY=yes`, prossegue com ele.
`pip-audit` não verificado (não instalado; nenhum arquivo Python foi alterado nesta rodada).

**Pendente:** F4 real (migração de `next.config.ts`/`config.py`/CORS/hosts para a topologia
`gennomx.com`) segue não implementada — este registro cobre apenas o bloqueio operacional do
caminho legado, não a migração.

---

## Prontidão de deploy MVP — 2026-07-02

- Retry manual (`POST /api/v1/jobs/{id}/retry`) agora cobre todos os conectores P1 implementados:
  `clinicaltrials_gov`, `pubmed`, `openfda`, `dailymed`, `open_targets` e `ema`.
- Produção deixou de depender de domínio hardcoded: `API_ALLOWED_HOSTS` alimenta o
  `TrustedHostMiddleware` e rejeita wildcard global/localhost em `ENVIRONMENT=production`.
- Adicionada base produtiva para Hostinger VPS: `infra/docker-compose.prod.yml` (API, worker,
  beat, Redis TLS, Caddy) e `infra/Caddyfile`; `Makefile` ganhou `prod-up`, `prod-down`,
  `prod-logs` e `release-check`.
- `.env.example`, `docs/05`, `docs/09` e `docs/11` atualizados com Redis `rediss://`, domínio API,
  checklist de pré-deploy, migração `0006`, gates e handshake.
- `.gitignore` corrigido para não ignorar `frontend/src/lib/` no primeiro commit; `.env`, caches,
  builds, `node_modules` e `secrets/` seguem ignorados.
- `project_state/fontes_priorizacao.xlsx` atualizado para marcar ClinicalTrials.gov, PubMed,
  openFDA, DailyMed, Open Targets e EMA como implementados, mantendo ANVISA e PMC full-text fora
  desta rodada por decisão explícita.
- Pendente de ambiente externo: executar `make release-check`, `make handshake` com rede liberada,
  aplicar Alembic `0006` no Supabase real, provisionar frontend Vercel/Netlify e realizar primeiro
  commit/push com secret scan.

## Reorganização documental e higiene de estrutura — 2026-07-02

- Históricos sucedidos consolidados em `project_state/archive/`: `TASKFLOW.md` (da raiz) e
  `MEMORY_FASE_2/5/6.md` (de `docs/`), sem alteração de conteúdo.
- `Referências de Design/` (raiz) movida para `docs/_referencias_design/` (nome sem espaços/acentos);
  diretório vazio `.agents/` removido.
- `docs/README.md` reescrito como índice completo (docs de área ↔ fases VLAEG + diretórios
  complementares); referências atualizadas em `AGENTS.md` §14A, `docs/13` §3/§5, `task_plan.md` e este arquivo.
- Higiene verificada: `.gitignore` cobre `.env*`, `secrets/`, caches, builds e logs; nenhuma
  referência quebrada restante (busca global por `TASKFLOW`, `MEMORY_FASE` e nomes movidos).
- Decisão registrada em `docs/11_CHANGELOG_DECISOES.md` (2026-07-02).

## Conectores P1 — openFDA, DailyMed, Open Targets, EMA — 2026-07-02

- Implementados os quatro conectores regulatórios/target P1 restantes, seguindo o padrão VLAEG
  do conector `pubmed` (Link via `healthcheck()` → persistência → task Celery → beat schedule →
  testes → docs).
- Persistência compartilhada nova: `workers/persistence/regulatory.py` (openFDA/DailyMed/EMA →
  `regulatory_approvals`, resolvendo `DrugAsset` por nome/alias) e `workers/persistence/targets.py`
  (Open Targets → `targets`, merge não destrutivo de aliases/indicações).
- Nenhuma migração de schema foi necessária — `regulatory_approvals`, `targets` e as linhas de
  `data_sources` para as quatro fontes já existiam desde `0001_initial_schema.py`.
- `get_regulatory_status` (MCP) passa a retornar dados reais de aprovação FDA/EMA em vez de tabela
  vazia; `search_drugs`/`compare_assets` ganham `special_designations`/`pathway` quando presentes.
- Nova dependência `openpyxl` para parsing do export oficial EMA (`.xlsx`).
- Bug real corrigido durante os testes: consulta de aprovação existente em `regulatory.py` não
  recuperava `source_updated_at`, fazendo o motor de decisão cair sempre em `CONFLICT` em vez de
  `REPLACE` ao reingerir a mesma fonte com dado mais recente.
- Validação: Ruff aprovado (`app workers tests migrations`), 39 testes novos, suíte completa
  223 passed / 2 skipped (skips ambientais pré-existentes de DuckDB no Python 3.14 local).
  `mypy` não pôde ser executado localmente (dependências dev não instaladas no Python 3.14 local);
  gate oficial permanece o CI (Python 3.12).
- Documentação: `docs/03` §0.2C–0.2F (contratos) e §6.8C (estado implementado + limitações),
  matriz Link atualizada, `docs/04` (`get_regulatory_status`), `docs/09` §0.1B (automação),
  `docs/11` (changelog), `.env.example` com as novas variáveis de configuração.
- Pendente (Onda B, prontidão de deploy): atualizar `project_state/fontes_priorizacao.xlsx`
  (status das quatro fontes de "Não implementado" para "Implementado").

## Conector PubMed — 2026-06-23

- Implementado o conector PubMed conforme `project_state/plano_conector_pubmed.md` (P1, ordem 2).
- Slug `pubmed` separado de `pubmed_pmc` (legado, permanece inativo). PMC full-text adiado para ordem 3.
- Connector: E-utilities NCBI (ESearch com history → EFetch via WebEnv/query_key → parsing XML),
  rate limit `PUBMED_RATE_LIMIT_REQUESTS_PER_SECOND`, retry com `tenacity`, batch de 100 registros.
- Parser: `xml.etree.ElementTree` (stdlib) — PMID, DOI, PMCID, title, abstract estruturado (Label),
  journal, authors (LastName+ForeName/CollectiveName), keywords (MeSH), NCT (DataBank).
- Normalizer: `publication_type` controlado (`article|preprint|review|abstract|letter`),
  `evidence_maturity=peer_reviewed_primary`, `registry_source=pubmed`, `source_url` com link PMID.
- Persistência: `_persist_publications` com stage/dedup por PMID, quality gate (PMID+title),
  `PersistenceDecisionEngine`, `SourceDocument` (`source_type=scientific_publication`),
  `EvidenceSnippet` (`entity_type=publication`), NCT linking contra `clinical_trials.nct_id`.
- Task Celery `run_pubmed_ingest` com `JobTracker`, invarianes de savepoint/falha sistêmica/limite de lote.
- Migração `0005` adiciona `data_sources.pubmed`. Alembic upgrade/downgrade testado offline.
- Handshake `tools/handshake.py` inclui `PubMedConnector`; beat schedule diário (`pubmed-daily-incremental`).
- Testes unitários: healthcheck (ok/unreachable/error/config_error), parser (XML completo/mínimo/review),
  normalizer (completo/mínimo/null), persistence flow (insert/update/noop/falha/quality gate).
- Documentação: contrato `pubmed` em `docs/03` §0.2B, matriz Link atualizada, §6.8B (estado implementado),
  `docs/04` (§search_publications) com nota de fonte real, changelog `docs/11` com decisão de slug.

## Integração Supabase como banco — 2026-06-23

- Backend, workers e Alembic agora normalizam URLs Supabase/PostgreSQL para o driver correto
  (`asyncpg` no runtime, `psycopg2` nas migrações).
- `.env.example` documenta conexão hospedada Supabase com pooler para app/worker e direct
  connection para migrações.
- `infra/supabase/bootstrap_roles.sql` cria extensões, roles dedicadas e grants mínimos para
  `gennomx_app`, `gennomx_worker`, `gennomx_migrator` e `gennomx_readonly`.
- README, segurança e changelog registram o fluxo de ativação: bootstrap, `.env`, Alembic e
  readiness.
- Projeto Supabase `qfanrziwepkqkgtvfrdt` recebeu bootstrap real, Alembic `upgrade head` até
  `0005` e grants pós-migração. Verificação confirmou `gennomx_app`, `gennomx_worker` e
  `gennomx_migrator` sem superuser/BYPASSRLS, todas enxergando `alembic_version=0005`.
- Service role legado foi removido dos `.env` locais e marcado para substituição pelo valor
  rotacionado. FastAPI agora valida JWT Supabase via JWKS (`ES256`/`RS256`) com fallback HS256
  apenas para transição.

## Conclusão operacional da governança — 2026-06-21

- Migração `0004` operacionaliza temporalidade granular, metadados, correções, retenção e scraping.
- Registry de políticas falha fechado e o serviço genérico decide insert/replace/enrich/noop/
  reject/archive/conflict/quarantine com evidência e granularidade.
- DuckDB está ligado ao lote quando existe chave natural repetida; quality gates precedem escrita.
- Correções humanas exigem evidência e revisão; não há edição factual destrutiva.
- Freshness diário sinaliza revalidação e MCP/API retornam somente projeções correntes.
- Retenção semanal arquiva com checksum/manifesto, respeita legal hold e só depois expurga.
- Scraping é fail-closed e dispõe de kill switch administrativo no dashboard.
- O passo 11 permanece adiado e nenhum modelo foi selecionado ou acoplado.

Gate final: 115 testes aprovados, 2 skips ambientais (DuckDB e BeautifulSoup ausentes no
Python 3.14 local), Ruff/ESLint/TypeScript aprovados e Alembic upgrade/rollback offline aprovados.
Build Next de produção aprovado, incluindo `/governance`.

## Remediação de revisão externa — 2026-06-21

- Corrigido bug crítico do INSERT de `SourceDocument` e escopo da evidência granular.
- Persistência de página falha quando todos os registros sofrem exceção sistêmica.
- Teste do fluxo completo exige documento, trial, evidência, assertions e contador inserido.
- Limite de lote deixou de acionar retry fatal.
- Roles de API/worker/migrator foram separados e validados por nome, superuser e bypass RLS.
- SSR passou a usar JWT individual + `no-store`; build comprovou rotas dinâmicas protegidas.
- Chave interna virou service sem admin; auth MCP morta removida; compare constante aplicado.
- Runner assíncrono Celery foi unificado.
- Dedup exato abre conflito sem merge; confidence/completeness são calculados por regra versionada.
- `.gitignore` já cobre `.pyc`, caches, `.next` e builds. Python 3.14 local não é gate oficial.

Validações finais desta rodada: 104 testes unitários/de integração aprovados (1 skip por DuckDB
ausente no Python local), incluindo contrato HTTP completo do MCP; Ruff, ESLint, TypeScript e
build Next aprovados; Alembic `upgrade head --sql` aprovado. O warning de cache do pytest é uma
limitação do caminho/sandbox no Windows e não altera o resultado dos testes.

## Governança temporal e persistência — 2026-06-20

- ADR-001 formalizou current state como projeção e assertions como histórico bitemporal.
- Migração `0003` adicionou assertions, conflitos, correções, current/supersession, RLS e índices.
- Motor puro de decisão implementou insert/replace/enrich/noop/reject/archive/conflict/quarantine.
- CT.gov passou a comparar `source_updated_at` e hash antes de atualizar o canônico.
- Relações trial↔ativo são encerradas temporalmente; estágio de ativo foi separado em corrente,
  máximo histórico e status de desenvolvimento.
- Evidências críticas passaram a ser produzidas por campo; staging DuckDB e quality gates foram
  adicionados antes da gravação.
- Retenção, arquivamento, edição corretiva e scraping controlado foram documentados.
- Testes foram adicionados para decisões, versão atrasada, idempotência, conflito, ausência de
  evidência, hashing, quality gates, DuckDB e contrato da migração.
- A escolha de modelos LLM permaneceu fora desta entrega por decisão explícita do usuário.

## Programa de correção — Fase 5 (2026-06-20)

- Stubs de empresas, indicações, targets, jobs, logs MCP e segurança substituídos por telas reais.
- API ganhou catálogos de indicações/targets e auditoria administrativa sanitizada.
- Logs do dashboard omitem argumentos MCP, IDs de ator, hashes de IP e metadados brutos.
- Playwright cobre sete fluxos essenciais do dashboard; build Next de produção aprovado.
- CI ganhou E2E, `npm audit`, mypy, pip-audit e Bandit bloqueantes.
- Dependências vulneráveis foram elevadas; `python-jose` foi substituído por PyJWT e
  LiteLLM vulnerável foi colocado em quarentena fora do runtime principal.
- Validação: Ruff/format, 78 testes unitários, mypy, ESLint, TypeScript, build,
  7 E2E, npm audit, pip-audit e Bandit aprovados.

## Programa de correção — Fase 4 (2026-06-20)

- Migração `0002` converte referências escalares para UUID, cria 19 FKs e quatro checks.
- Relação canônica `clinical_trial_assets` criada e sincronizada pelo worker.
- RLS deny-by-default e políticas por papel habilitadas no domínio e auditoria.
- Senhas fixas removidas do init SQL; papéis locais passaram a grupos `NOLOGIN`.
- Readiness verifica PostgreSQL e Redis; Compose e imagem backend foram endurecidos.
- Comandos Alembic do Makefile/CI corrigidos; Python suportado limitado a `<3.14`.
- Validação: Ruff, 73 testes, SQL offline de upgrade/rollback e Compose config aprovados.

## Programa de correção — Fase 3 (2026-06-20)

- CT.gov usa `data_sources.last_successful_run` como cursor, com sobreposição configurável.
- Paginação é persistida por página; o limite de volume não avança o cursor.
- Retry Celery cobre falhas sistêmicas e cada registro usa savepoint.
- Raw JSON canônico é comprimido, endereçado por hash e registrado em `SourceDocument`.
- Evidências são fragmentos JSON literais da fonte e são idempotentes.
- Validação: Ruff aprovado e 64 testes unitários aprovados.

**Histórico consolidado de execução.** Consolida `MEMORY_FASE_2.md`, `MEMORY_FASE_5.md` e `MEMORY_FASE_6.md` (preservados como histórico em `project_state/archive/`).

## Programa de correção — Fase 1 (2026-06-20)

- Removidos defaults administrativos exploráveis e adicionada validação fail-closed de produção.
- JWT Supabase reforçado com issuer/audience e papel de aplicação em `app_metadata.gennomx_role`.
- Frontend ganhou login Supabase, proteção por middleware e propagação de bearer token.
- Health foi separado em liveness (`/health`) e readiness de banco (`/ready`).
- Documentação de segurança e estado atualizada na mesma fase.

## Programa de correção — Fase 2 (2026-06-20)

- FastMCP/stdio adicionado como transporte padrão; adaptador HTTP legado preservado.
- Escopos por cliente, comparação de token em tempo constante e rate limit Redis aplicados.
- Request limitado, JSON validado, erro 500 sanitizado e entidades acessadas auditadas com limite.
- Testes unitários adicionados para escopos e auditoria bounded.
- Validação: 11 testes MCP aprovados e Ruff aprovado; apenas warning local de cache pytest por caminho sandbox foi emitido.


---

## Fase 2 — Serviços FastAPI, Schemas, Workers (2026-06-09)

- Camada de serviços: `AssetService`, `CompanyService`, `TrialService`, `SourceService` (recebem `AsyncSession`, `list_*` retorna `tuple[list[dict], int]`, `get_*_detail` lança `NotFoundError`).
- Schemas Pydantic v2: `DrugAssetList`, `DrugAssetDetail` (demais endpoints retornam `dict`).
- Workers Celery: `run_clinicaltrials_ingest` (com JobTracker), `link_trials_to_assets` (com
  backfill), deduplicação exata conservadora e cálculo determinístico de confiança/completude.
- Conector ClinicalTrials.gov: paginação, rate limit, retry (tenacity), parser e normalizer.
- `Dockerfile` backend multi-stage (Python 3.12-slim, non-root).

## Fase 5 — Frontend Next.js (2026-06-09)

- Next.js (App Router) + TypeScript + Tailwind; Design System GennomX (rose `#F2829B`, Montserrat/Inter).
- Registro histórico de 2026-06-09: Overview, Assets, Asset detail, Trials e Sources
  funcionais; os stubs então existentes foram substituídos na correção Fase 5 de 2026-06-20.
- API client centralizado em `src/lib/api.ts`; componentes UI base em `src/components/ui`.
- Auth Supabase prevista, ainda não implementada.

## Fase 6 — Testes + CI/CD (2026-06-09)

- pytest com markers (`unit`, `integration`, `mcp`, `connector`, `slow`); fixtures `mock_db`/`FakeRow`/`FakeResult`/`override_settings`.
- CI GitHub Actions: backend-lint, backend-unit, backend-integration, frontend-lint, frontend-build, security.

## Atualização 2026-06-12 — Correções de integração MCP, jobs e rastreabilidade

- MCP `_dispatch_tool()` recebe sessão real do banco; persiste `mcp_query_logs` inclusive em chamadas inválidas/bloqueadas.
- `GET /api/v1/jobs` usa `SourceService.list_jobs()`; `POST /api/v1/jobs/{id}/retry` reenfileira Celery (CT.gov).
- `JobTracker` resolve `data_source_id` e serializa `error_detail`/`metadata` como JSON válido.
- CT.gov cria/reusa `SourceDocument`, cria `EvidenceSnippet` por trial e por ativo; cria/atualiza `DrugAsset` a partir de intervenções (`DRUG`/`BIOLOGICAL`/`GENETIC`) e preenche `clinical_trials.drug_asset_ids`.
- `pyproject.toml` com `setuptools.build_meta:__legacy__`; `structlog.stdlib.LoggerFactory()`; atributos ORM `metadata` renomeados.
- Backend: Ruff + 50 testes passando. Frontend: Next 15.5.18, `npm ci`, lint/typecheck/build ok. Pendem 2 vulnerabilidades moderadas (`postcss` transitivo do Next).

---

## Pendências abertas (rastreadas)

- Executar o teste de staging DuckDB também no ambiente oficial Python 3.11–3.13 com o extra de
  dependências instalado; a implementação existe, mas o Python 3.14 local não possui DuckDB.
- Schemas Pydantic tipados para `Company`, `Trial`, `Indication`.
- Conectores: PMC full-text (ordem 3, adiado do PubMed) e ANVISA seguem pendentes; PubMed,
  openFDA, DailyMed, Open Targets e EMA implementados (2026-06-23 e 2026-07-02).
- Testes ainda desejáveis: services legados restantes, ferramentas MCP individuais,
  conectores futuros com `httpx.MockTransport` e meta formal de cobertura.
- Rodar `make handshake` contra as APIs reais de openFDA/DailyMed/Open Targets/EMA em ambiente com
  rede liberada (handshake não foi executado ao vivo nesta sessão, apenas smoke-tests offline com
  fixtures e a suíte de testes unitários com mocks).

> Registro de decisões formais permanece em `docs/11_CHANGELOG_DECISOES.md`.
