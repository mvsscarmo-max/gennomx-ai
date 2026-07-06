# 09 — Deploy, Operação, Observabilidade e Manutenção

## Automações de governança — 2026-06-21

| Gatilho | Agenda UTC | Comportamento |
|---|---:|---|
| `governance-freshness-daily` | 02:30 diária | marca assertions/trials vencidos para revalidação |
| `governance-retention-weekly` | domingo 04:00 | manifesta, arquiva e expurga somente classes elegíveis |

Simular antes da primeira execução produtiva. Execução real exige Storage Supabase; falha de upload
marca manifesto `failed` e impede exclusão. Exclusão exige `archive_items`, cutoff e ausência de
legal hold. Restore: recuperar `storage_uri`, validar SHA-256 e reimportar em staging.

## Roles PostgreSQL obrigatórios em produção — 2026-06-21

| Processo | Variável | Role exigido | Permissão |
|---|---|---|---|
| FastAPI/MCP | `DATABASE_URL` | `gennomx_app` | leitura + logs explicitamente permitidos |
| Celery workers | `WORKER_DATABASE_URL` | `gennomx_worker` | escrita governada pelos pipelines |
| Alembic | `DATABASE_URL_SYNC` | `gennomx_migrator` | DDL somente na etapa de migração |

Os três roles devem ser `NOSUPERUSER NOBYPASSRLS`. Startup da API e início da ingestão falham
fechados se o role runtime não corresponder ou puder ignorar RLS. Nunca usar `postgres` ou
`service_role` como conexão de aplicação. O dashboard SSR encaminha a sessão do usuário e usa
`cache: no-store`; não recebe segredo administrativo em produção.

## Stack produtiva mínima — Hostinger VPS / Docker Compose — 2026-07-02 — ⚠ LEGADA (ver nota 2026-07-06)

> **Atualização 2026-07-06 (revisão técnica, workspace raiz PLAN-003):** esta seção descreve a
> topologia original (`api.gennomx.ai` + Caddy próprio em 80/443 + frontend Vercel/Netlify),
> aprovada em 2026-07-02. Em 2026-07-04 o fundador decidiu (D-011, `project_state/DECISIONS.md` da
> raiz) que o GennomX AI passa a viver sob `gennomx.com`: hub `admin.gennomx.com/ai`, API via
> `admin.gennomx.com/api/ai`, MCP em `mcp.gennomx.com`, atrás do Traefik já compartilhado com outro
> projeto na VPS (F-006, `project_state/FINDINGS.md` da raiz). O compose abaixo (`infra/docker-compose.prod.yml`)
> **não deve ser usado** nessa VPS: o Caddy publicando 80:80/443:443 disputaria as portas do Traefik.
> `make prod-up` recusa subir esse compose sem `ACKNOWLEDGE_LEGACY_TOPOLOGY=yes` (ver `Makefile`).
> A migração real para `basePath=/ai`, `API_ALLOWED_HOSTS`/CORS de `gennomx.com` e integração com o
> nginx interno da `maquina-conteudo/` é a **F4 do PLAN-002** (raiz), ainda pendente — não iniciada
> neste ciclo para evitar mudança grande sem necessidade confirmada. Até lá, esta seção permanece
> como registro histórico da topologia `api.gennomx.ai`, não como plano ativo.

Artefatos implementados:

- `infra/docker-compose.prod.yml`: API FastAPI, worker Celery, beat Celery, Redis TLS e Caddy;
- `infra/Caddyfile`: reverse proxy HTTPS para `API_DOMAIN`;
- `Makefile`: `make prod-up`, `make prod-down`, `make prod-logs` e `make release-check`.

Variáveis obrigatórias novas:

- `API_DOMAIN`: domínio público da API, usado pelo Caddy;
- `TLS_ADMIN_EMAIL`: e-mail para ACME/Let's Encrypt;
- `API_ALLOWED_HOSTS`: allowlist do `TrustedHostMiddleware`, separada por vírgulas.

Redis em produção permanece TLS obrigatório. O compose produtivo usa `rediss://` e espera os
certificados em `secrets/redis/`:

```txt
secrets/redis/ca.crt
secrets/redis/redis.crt
secrets/redis/redis.key
```

`secrets/` é ignorado pelo Git. Gerar/instalar certificados antes de `make prod-up`; se a opção
operacional for Redis gerenciado, apontar `REDIS_URL`, `CELERY_BROKER_URL` e
`CELERY_RESULT_BACKEND` para o endpoint `rediss://` do provedor e remover/ignorar o serviço Redis
local do compose produtivo.

### Pré-deploy MVP

1. Confirmar `.env` produtivo fora do Git, sem placeholders e com `ENVIRONMENT=production`.
2. Confirmar `API_ALLOWED_HOSTS`, `CORS_ORIGINS`, `SUPABASE_JWKS_URL`, tokens MCP e URLs Redis TLS.
3. Aplicar migrações no Supabase real com `gennomx_migrator`: `cd backend && python -m alembic -c migrations/alembic.ini upgrade head`.
4. Verificar que `alembic_version` está em `0006`.
5. Executar `make release-check` em ambiente com dependências completas.
6. Executar `make handshake` em ambiente com rede liberada.
7. Subir backend na VPS com `make prod-up`.
8. Validar `/health`, `/ready`, login do dashboard, worker status e um job de ingestão controlado.
9. Configurar frontend em Vercel/Netlify com `NEXT_PUBLIC_API_URL` apontando para `https://API_DOMAIN`.
10. Registrar resultado em `project_state/progress.md` e `docs/11_CHANGELOG_DECISOES.md`.

## Política de retenção, particionamento e arquivamento — 2026-06-20

| Classe | Retenção operacional | Destino após janela quente |
|---|---|---|
| canônico corrente | enquanto existir | PostgreSQL |
| assertions clínicas/regulatórias | indefinida; mínimo 10 anos | partição histórica/Parquet |
| raw oficial/evidência crítica | 7–10 anos ou indefinida | object storage imutável |
| processed intermediário | 90–365 dias | remover se reprocessável |
| quarentena rejeitada | 30–90 dias | remover, salvo incidente |
| logs detalhados | 90–180 dias | agregados em Parquet |
| resumo de jobs | 2–5 anos | partição histórica |
| auditoria/MCP/security | 1–5 anos conforme risco | storage restrito |
| embeddings substituídos | até validar reindexação | exclusão controlada |

Particionar assertions/logs mensalmente quando partição superar 10 GB, índice superar 5 GB ou p95
ficar fora do SLO por duas semanas. Usar BRIN temporal e índices parciais `is_current=true`. O
arquivamento executa dry-run, valida contagens/hash, grava manifesto e só então remove a partição
quente. Nunca remover assertion corrente, evidência referenciada, conflito aberto, correção pendente
ou legal hold. Testar restore de amostra trimestralmente.

## Correção operacional fase 4 — 2026-06-20

- `/health` é liveness; `/ready` exige PostgreSQL e Redis e retorna 503 em indisponibilidade.
- A imagem backend é multi-stage, sem root/toolchain no runtime, e possui healthcheck em `/ready`.
- Postgres/pgvector e Redis usam tags versionadas; Redis exige autenticação e persistência.
- UIs de desenvolvimento ficam em loopback e usam `no-new-privileges`.
- O runtime Python suportado é `>=3.11,<3.14`; CI e container usam Python 3.12.

```bash
cd backend
python -m alembic -c migrations/alembic.ini upgrade head
python -m alembic -c migrations/alembic.ini downgrade -1
```

Antes do upgrade `0002`, executar backup e verificar órfãos. Conversão UUID/FKs falha fechada; não
editar a migração para apagar registros inválidos. Corrija os dados, repita e valide `/ready`.

Este documento deve orientar ambientes, deploy, monitoramento, observabilidade, manutenção, alertas, incidentes, backups e operação contínua.

> **VLAEG:** este documento materializa a fase **G — Gatilho** (Pilar 4, Automação controlada) e o Princípio 3.5 (Autocorreção estruturada). Ver `docs/13_PROTOCOLO_VLAEG.md`.

---

# 0. Declarações de automação (VLAEG Pilar 4)

Toda automação (cron, webhook, fila, listener) deve ser declarada com o template abaixo antes de ser ativada. Automações são rastreáveis, reversíveis quando possível, auditáveis e monitoradas.

## Template

```text
Evento de disparo:
Condição de execução:
Dados necessários:
Ação executada:
Destino do resultado:
Responsável:
Fallback:
Log obrigatório:
Critério de sucesso:
Critério de falha:
```

## 0.1 Ingestão agendada — ClinicalTrials.gov (implementada)

```text
Evento de disparo:     Celery beat — agendamento diário (UTC)
Condição de execução:  worker da fila "ingest" disponível
Dados necessários:     DataSource "clinicaltrials_gov" registrada; acesso à API v2
Ação executada:        workers.tasks.ingest.run_clinicaltrials_ingest (job_type=incremental)
Destino do resultado:  clinical_trials, drug_assets, source_documents, evidence_snippets, ingestion_jobs
Responsável:           operação de dados GennomX
Fallback:              retry/backoff (tenacity); reenfileiramento via POST /api/v1/jobs/{id}/retry
Log obrigatório:       IngestionJob (status, contadores, erro JSON) + logs estruturados do worker
Critério de sucesso:   IngestionJob "completed", trials upsertados idempotentes por NCT ID, evidências vinculadas
Critério de falha:     IngestionJob "failed" com error_type/error_detail; alerta operacional
```

> Idempotência garantida por dedup de NCT ID; timeout por `task_soft_time_limit=3600` / `task_time_limit=7200` (`backend/workers/celery_app.py`). O agendamento vive em `celery_app.conf.beat_schedule` e é operado por `celery -A workers.celery_app beat` (alvo `make dev-beat`; worker: `make dev-worker`).

## 0.1B Ingestão agendada — openFDA, DailyMed, Open Targets, EMA (implementadas em 2026-07-02)

```text
Evento de disparo:     Celery beat — openfda/dailymed diários (UTC), open_targets/ema semanais (segunda)
Condição de execução:  worker da fila "ingest" disponível
Dados necessários:     DataSource correspondente registrada (seed em 0001_initial_schema); DrugAsset
                        pré-existente para resolução por nome (openfda/dailymed/ema); acesso à
                        API/export de cada fonte
Ação executada:        workers.tasks.ingest.run_openfda_ingest / run_dailymed_ingest /
                        run_opentargets_ingest / run_ema_ingest (job_type=incremental)
Destino do resultado:  regulatory_approvals (openfda/dailymed/ema) ou targets (open_targets),
                        source_documents, evidence_snippets, ingestion_jobs
Responsável:           operação de dados GennomX
Fallback:              retry/backoff (tenacity); reenfileiramento via POST /api/v1/jobs/{id}/retry
Log obrigatório:       IngestionJob (status, contadores, erro JSON) + logs estruturados do worker
Critério de sucesso:   IngestionJob "completed"; registros upsertados idempotentes pela chave
                        corrente de cada tabela; evidências vinculadas
Critério de falha:     IngestionJob "failed" com error_type/error_detail; alerta operacional
```

> Nenhuma das quatro fontes expõe um filtro de delta confiável; `incremental` é limitado por
> `*_MAX_RECORDS_PER_RUN` e depende de upserts idempotentes, não de um cursor real. Detalhe por
> conector em `docs/03_FONTES_E_INGESTAO.md` §6.8C. Handshake: `make handshake`.

## 0.2 Automações futuras

Cada novo job agendado (ANVISA, etc.), webhook ou listener deve adicionar sua declaração nesta seção antes de ser ativado, e registrar o gatilho no `beat_schedule` quando agendado.

---

# 0C. Runbook de autocorreção estruturada (VLAEG 3.5)

Diante de erro, falha de integração, bug ou comportamento inesperado, aplicar o ciclo:

1. **Analisar:** ler erro, logs estruturados, payload, `IngestionJob.error_detail` e `mcp_query_logs`.
2. **Isolar:** classificar a origem — dados, regra de negócio, integração/fonte, infraestrutura ou interface.
3. **Corrigir:** ajustar código, configuração ou regra, em mudança pequena e reversível (`AGENTS.md` §14).
4. **Testar:** executar teste unitário/integração/contrato pertinente, ou simulação via `tools/handshake.py`.
5. **Documentar:** registrar em `docs/11_CHANGELOG_DECISOES.md` e/ou `project_state/progress.md`.
6. **Prevenir recorrência:** criar validação, teste de regressão ou alerta.

> **Regra:** o mesmo erro não deve ocorrer duas vezes sem gerar melhoria documental, teste ou validação preventiva.

---

# 15. CI/CD, ambientes e gates de release

## 15.1 Ambientes

Recomenda-se:

- **local**: desenvolvimento;
- **test**: execução automática de testes;
- **staging**: ambiente semelhante ao production;
- **production**: ambiente estável;
- **sandbox MCP**: ambiente para testes de ferramentas por modelos host.

## 15.2 Gates mínimos antes de deploy

Nenhum deploy para produção deve ocorrer se falharem:

- testes unitários críticos;
- testes de integração essenciais;
- testes MCP essenciais;
- testes de migração de banco;
- secret scanning;
- dependency scanning crítico;
- lint/type checks mínimos;
- build do frontend;
- testes end-to-end essenciais;
- testes de segurança de autorização.

## 15.3 Estratégia de migração

- migrações versionadas;
- rollback planejado;
- backup antes de migração crítica;
- testes de migração em staging;
- validação de dados após migração;
- não apagar colunas críticas sem fase de depreciação.

## 15.4 Estratégia de releases

MVP interno:

- releases frequentes;
- changelog simples;
- validação manual final;
- monitoramento pós-deploy.

Futuro comercial:

- versionamento semântico;
- release notes;
- feature flags;
- canary deploy;
- rollback automático;
- SLAs internos.

---

# 17. Observabilidade e manutenção

## 17.1 Monitoramento de jobs

Métricas:

- jobs executados;
- jobs com sucesso;
- jobs com falha;
- duração;
- registros coletados;
- registros rejeitados;
- deltas por fonte;
- erros por tipo;
- última execução bem-sucedida.

## 17.2 APIs externas

Monitorar:

- disponibilidade;
- latência;
- erros HTTP;
- mudanças de schema;
- rate limit;
- mudanças de autenticação;
- queda de volume.

## 17.3 Scrapers

Monitorar:

- falha de parsing;
- alteração de layout;
- bloqueio de acesso;
- aumento de redirects;
- aumento de captchas;
- mudanças em robots/termos;
- aumento de rejeições.

## 17.4 MCP

Monitorar:

- chamadas por ferramenta;
- latência;
- erros;
- consultas sem resultado;
- volume por cliente;
- tokens mais usados;
- tentativas não autorizadas;
- consultas amplas;
- custo indireto.

## 17.5 Custos de IA

Monitorar:

- chamadas de extração;
- tokens consumidos;
- custo por fonte;
- custo por documento;
- taxa de erro;
- custo por entidade enriquecida;
- modelos utilizados.

## 17.6 Qualidade dos dados

Monitorar:

- completude;
- duplicidade;
- conflitos;
- evidência ausente;
- campos obrigatórios vazios;
- freshness;
- entidades órfãs;
- confidence score médio;
- campos editados manualmente.

## 17.7 Segurança

Monitorar:

- falhas de login;
- tokens expirados ou abusados;
- chamadas bloqueadas;
- rate limits acionados;
- uploads rejeitados;
- alertas de SAST/dependency scanning;
- segredos expostos;
- alterações administrativas;
- eventos MCP anômalos.

## 17.8 Alertas recomendados

- fonte crítica sem atualização por mais de X dias;
- queda abrupta de registros;
- aumento abrupto de registros;
- falha repetida em conector;
- mudança de schema;
- teste de segurança falhou;
- token MCP com uso anômalo;
- consulta MCP muito ampla;
- erro 5xx recorrente;
- backup falhou;
- parsing de PDF com erro alto;
- custo de IA acima do limite.

---

## Runbooks operacionais a criar

Criar runbooks específicos conforme a implementação evoluir:

- falha de conector;
- mudança de schema em fonte externa;
- falha de scraping;
- falha de job de ingestão;
- falha de pipeline de normalização;
- falha de testes de contrato;
- alerta de segurança MCP;
- token MCP comprometido;
- restauração de backup;
- rollback de migration;
- reprocessamento de dados;
- bloqueio de fonte por risco jurídico/compliance.

## Gate de release da Fase 5

O workflow `.github/workflows/ci.yml` bloqueia integração quando falharem Ruff/format,
mypy, testes unitários ou integração, migrations, ESLint/TypeScript, npm audit, build Next,
Playwright, pip-audit ou Bandit. O job E2E instala Chromium isolado e usa respostas de API
determinísticas; não depende de dados produtivos nem aceita bypass de autenticação em produção.

Antes de deploy, executar `make test`, `make test-e2e`, `make security-scan` e
`make build-frontend`. A validação local não substitui a migration real do CI com PostgreSQL.


## 20A. Operação da stack refinada

### Ambientes mínimos

- `local`: desenvolvimento e testes manuais;
- `staging`: validação de migrations, conectores, dashboard, MCP e workers;
- `production`: ambiente operacional.

### Serviços mínimos do MVP

- frontend Next.js em Vercel ou Netlify;
- backend FastAPI;
- worker Celery;
- Redis broker;
- Supabase/PostgreSQL;
- Supabase Storage ou storage S3-compatible;
- OPENCODE/LLM configurado por variáveis protegidas (`OPENCODE_API_KEY`, `OPENCODE_BASE_URL`);

### Variáveis e segredos

Separar credenciais para:

- Supabase anon key;
- Supabase service role key, nunca exposta ao frontend;
- database URL;
- Redis URL;
- provedores LLM;
- tokens MCP;
- chaves de API externas;
- secrets de assinatura JWT/session.

### Monitoramento operacional

Monitorar:

- saúde da API;
- fila Redis;
- workers ativos;
- jobs travados;
- memória/CPU dos workers;
- falhas de parsing;
- custos de IA por job;
- latência MCP;
- uso do Supabase;
- volume de storage;
- falhas de backup e restore.
