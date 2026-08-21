<!-- validate-links: illustrative-paths -->
# Arquivo VLAEG v1 - ingestao recorrente e data warehouse

**Data:** 2026-07-09 (segunda sessão de continuidade)
**Solicitante:** Marcus
**Status:** proposto (execução por fases pequenas, exige aprovação operacional antes de ativar ingestão produtivo)
**Premissas:** migração banco-only concluída em staging (VPS `gennomx-ai-postgres-ready` em `alembic_version=0006`, paridade de seeds com origem Supabase confirmada; ver `progress.md` desta data). Supabase Auth/JWKS e Supabase Storage permanecem ativos.
**Restrições herdadas:** sem chatbot/gerador interno; sem SQL direto via MCP; sem expor ferramentas administrativas a modelos host; sem scraping agressivo/evasão; outputs de LLM não são verdade primária sem schema validation/evidência/versionamento; sem apagar histórico/evidência; conectores novos exigem fase L (handshake) + contrato em `docs/03`; alterações de schema exigem Alembic versionado + testes.

---

## 1. Diagnóstico do estado real da ingestão

### 1.1 Conectores realmente prontos para execução periódica

Confirmado no código (`backend/workers/connectors/`, `backend/workers/tasks/ingest.py`, `tools/handshake.py`):

| Slug | Método | Handshake `healthcheck()` | Task Celery | Já agendado no `beat_schedule` | Persistência wired | Raw storage wired |
|---|---|---|---|---|---|---|
| `clinicaltrials_gov` | API v2 | ✅ registrado | `run_clinicaltrials_ingest` | ✅ diário 03:00 UTC | `_persist_trials` | ✅ `store_raw_payload` |
| `pubmed` | API E-utilities | ✅ registrado | `run_pubmed_ingest` | ✅ diário 03:15 UTC | `_persist_publications` | ✅ |
| `openfda` | API (drugsfda) | ✅ registrado | `run_openfda_ingest` | ✅ diário 03:30 UTC | `_persist_regulatory_approvals` | ✅ |
| `dailymed` | API (spls.json) | ✅ registrado | `run_dailymed_ingest` | ✅ diário 03:45 UTC | `_persist_regulatory_approvals` | ✅ |
| `open_targets` | GraphQL | ✅ registrado | `run_opentargets_ingest` | ✅ semanal seg 04:00 UTC | `_persist_targets` | ✅ |
| `ema` | Export XLSX oficial | ✅ registrado | `run_ema_ingest` | ✅ semanal seg 04:15 UTC | `_persist_regulatory_approvals` | ✅ |

**Conclusão:** os 6 conectores estão implementados, registrados e agendados. A automação Celery/beat já existe e está configurada (`celery_app.py`). Falta validar em ambiente com rede + Redis + DB.

### 1.2 Dependem apenas de configuração/env/rede/credenciais (não de código)

- **Todos os 6:** `healthcheck()` está implementado por conector. Não há implementação pendente de lógica de coleta/parsing/normalização/persistência para nenhum deles.
- **NCBI API key** (`NCBI_API_KEY`): opcional para PubMed (eleva rate limit); sem ela a ingestão roda, mas mais lento.
- **openFDA API key** (`OPENFDA_API_KEY`): opcional (eleva rate limit).
- **Supabase Storage buckets** (`SUPABASE_STORAGE_BUCKET_RAW` etc.): exigem buckets criados no projeto Supabase com `service_role` válido; sem bucket, `store_raw_payload` falha fechado e impede a ingestão (foto imutável é requisito do pipeline, `docs/03` "Pipeline executável").
- **Redis** (`CELERY_BROKER_URL`/`CELERY_RESULT_BACKEND`): worker + beat precisam de Redis acessível; em produção exige `rediss://` (TLS).
- **DB URLs** com roles corretas: `gennomx_worker` para workers, `gennomx_app` para API, `gennomx_migrator` para Alembic — validação fail-closed em `config.py`.

### 1.3 Ainda precisam de handshake real contra fonte externa

- **`pubmed_pmc`**: slug legado, inativo, substituído por `pubmed`. PMC full-text (ordem 3) ainda pendente de handshake próprio.
- **`anvisa`**: não implementado; `healthcheck()` pendente; contrato de dados ainda não declarado em `docs/03` §0.
- **Demais fontes da planilha `fontes_priorizacao.xlsx`** (não localizada nesta máquina — presumo contínua como premissa viva conforme `docs/03` §4): cada conector futuro exige handshake + contrato antes da lógica.

Nota: o handshake dos 6 conectores ativos só pode ser validado em ambiente com rede de saída. `make handshake` roda `BaseConnector.healthcheck()` (read-only, sem side effects), o que o torna um gate natural de pré-ativação.

### 1.4 Jobs Celery já agendados (`celery_app.py` `beat_schedule`)

| Job | Task | Cron UTC | Fila | Retries |
|---|---|---|---|---|
| `clinicaltrials-daily-incremental` | `run_clinicaltrials_ingest` | 03:00 diário | ingest | 3 (backoff exp) |
| `pubmed-daily-incremental` | `run_pubmed_ingest` | 03:15 diário | ingest | 3 |
| `openfda-daily-incremental` | `run_openfda_ingest` | 03:30 diário | ingest | 3 |
| `dailymed-daily-incremental` | `run_dailymed_ingest` | 03:45 diário | ingest | 3 |
| `opentargets-weekly` | `run_opentargets_ingest` | seg 04:00 | ingest | 3 |
| `ema-weekly` | `run_ema_ingest` | seg 04:15 | ingest | 3 |
| `governance-freshness-daily` | `mark_stale_assertions` | 02:30 diário | process | — |
| `governance-retention-weekly` | `run_retention_cycle` | dom 04:00 | process | — |

Tasks de processamento disponíveis mas não agendadas no beat: `deduplicate_assets`, `link_trials_to_assets`, `compute_confidence_scores` (em `process.py`). Estes são candidatos a agendamento complementar (ver §5).

### 1.5 Tabelas já populadas por dados reais (origem Supabase — inventário 2026-07-09)

| Tabela | Contagem | Observação |
|---|---|---|
| `data_sources` | 8 | Seeds da migration `0001`; todas `connector_status=inactive`, `is_enabled=false`, `last_successful_run=NULL` |
| `retention_policies` | 5 | Seeds da migration `0004` |
| Demais 26 tabelas (entities, events, audit) | 0 | **Nenhuma ingestão real foi executada neste banco em nenhum momento** |

**Implicação decisiva:** o banco está em estado bootstrap puro. A "operacionalização da ingestão" começa do zero em volume, mas com toda a infraestrutura de código já pronta. O backlog é majoritariamente operacional (env/rede/Redis/db/storage), não de implementação de conectores.

### 1.6 Tabelas existentes mas vazias/subutilizadas (mapeamento de entidades)

| Entidade | Tabela | Será populada por | Lacuna |
|---|---|---|---|
| `drug_assets` | 0 hoje | CT.gov (intervenções) | Ingestão CT.gov popula via `_upsert_drug_assets_from_trial` |
| `companies` | 0 hoje | Derivado de sponsors (CT.gov) | Lacuna: não há parser/normalizer de empresa dedicado; empresas hoje são strings em `sponsor_names`. Entity resolution de empresa é MVP+ |
| `clinical_trials` | 0 hoje | CT.gov | Pronto para ingerir |
| `clinical_trial_assets` | 0 hoje | CT.gov (linking) | Pronto (`link_trials_to_assets`) |
| `indications` | 0 hoje | CT.gov (conditions) | Lacuna: conditions são strings; mapear para `indications` requer normalizer de indicação (MVP+) |
| `targets` | 0 hoje | Open Targets | Pronto para ingerir |
| `endpoints` | 0 hoje | CT.gov `resultsSection` (quando disponível) | **Lacuna P1:** parser de endpoints granulares não implementado |
| `trial_results` | 0 hoje | CT.gov `resultsSection` | **Lacuna P1:** parser de resultados granulares não implementado |
| `adverse_events` | 0 hoje | CT.gov `resultsSection` / labels | **Lacuna P1:** parser de safety não implementado |
| `regulatory_approvals` | 0 hoje | openFDA, DailyMed, EMA | Pronto para ingerir |
| `publications` | 0 hoje | PubMed | Pronto para ingerir |
| `source_documents` | 0 hoje | Todos os conectores | Pronto (wired) |
| `evidence_snippets` | 0 hoje | Todos os conectores | Pronto (wired) |
| `field_assertions` | 0 hoje | CT.gov (assertions por campo) | Pronto (wired) |
| `data_conflicts` | 0 hoje | `deduplicate_assets` / divergências | Pronto |
| `manual_corrections` | 0 hoje | Dashboard | Pronto |
| `ingestion_jobs` | 0 hoje | Todos (JobTracker) | Pronto |
| `mcp_query_logs` | 0 hoje | MCP | Pronto |
| `security_events` | 0 hoje | Auth/MCP | Pronto |
| `llm_call_logs` | 0 hoje | OPENCODE | Pronto (mig 0006) |

### 1.7 Ferramentas MCP que já se beneficiam diretamente dos dados ingeridos

Confirmado em `docs/04` e `backend/app/mcp/tools/` (9 ferramentas read-only):

- `search_drugs` — consome `drug_assets` + `regulatory_approvals` + `clinical_trial_assets`
- `find_trials` — consome `clinical_trials` (filtra `is_current=true`)
- `compare_assets` — consome `drug_assets` + relações
- `get_company_pipeline` — consome `drug_assets` + `companies` (lacuna: `companies` vazio)
- `get_trial_results` — consome `trial_results` (lacuna: parser granular não implementado)
- `search_publications` — consome `publications` (filtra `is_current=true`)
- `get_regulatory_status` — consome `regulatory_approvals` (filtra `is_current=true`)
- `build_report_data_bundle` — agrega múltiplas entidades
- `fetch_source_evidence` — consome `source_documents` + `evidence_snippets`

**Hoje todas retornam vazio** porque o banco está bootstrap. A ingestão dos 6 conectores já implementados destrava `search_drugs`, `find_trials`, `search_publications`, `get_regulatory_status`, `fetch_source_evidence` e `build_report_data_bundle`. `get_company_pipeline` fica parcial (assets sim, empresas como strings). `get_trial_results` permanece vazio até o parser granular de CT.gov resultsSection.

### 1.8 Lacunas que impedem a base ser útil para competitive intelligence / due diligence

1. **Sem dados ingeridos** (banco bootstrap) — resolvido ativando ingestão.
2. **Endpoints/resultados/adverse events granulares não persistidos** a partir de CT.gov `resultsSection` — limita benchmarking de eficácia/safety, central para due diligence.
3. **Indicações não normalizadas** — `conditions` do CT.gov são strings livres; sem mapeamento para `indications` canônico, landscapes terapêuticos são frágeis.
4. **Empresas não resolvidas** — sponsors são strings; sem `companies` canônicas com aliases, `get_company_pipeline` e competitive intelligence são rasos.
5. **Mecanismo de ação** não persistido como entidade própria (modelado em `docs/02` mas sem conector/normalizer).
6. **ANVISA ausente** — gap regulatório Brasil.
7. **PMC full-text** — abstracts PubMed cobrem evidência primária, mas full-text de OA subset enriquece due diligence; adiado por licença.
8. **Entity resolution / aliases** — dedup exata existe; merge fuzzy proibido por design; resolução humana de aliases é MVP+.
9. **Busca global cross-entity** — PostgreSQL FTS disponível mas sem view/unificação; MVP+.
10. **Observabilidade de ingestão** — `IngestionJob` registra contadores, mas não há painel de freshness/staleness por entidade nem alertas de queda de volume.

---

## 2. Prioridade de dados para ingestão (ordem racional)

### Onda 1 — Ativar conectores já implementados (backbone estruturado)

Ordem sugerida para primeira execução controlada (dry-run primeiro, depois incremental pequeno):

1. **ClinicalTrials.gov** — maior valor transversal (trials + assets + assertions por campo); incremental usa `last_successful_run` como cursor.
2. **PubMed** — evidência científica primária; dedup PMID; linking NCT contra `clinical_trials`.
3. **openFDA** — aprovações FDA; enriquece `regulatory_approvals` e `search_drugs`.
4. **DailyMed** — labels SPL FDA; complementa `regulatory_approvals` (FDA/US).
5. **Open Targets** — `targets` + associações alvo↔doença; destrava análise por target (semanal).
6. **EMA** — aprovações EU; export XLSX (semanal).

### Onda 2 — Fechar lacunas críticas do MVP

Prioridade por valor de competitive intelligence / due diligence:

| Lacuna | Valor | Esforço estimado | Ordem |
|---|---|---|---|
| Endpoints/resultados granulares de CT.gov `resultsSection` | Alto (benchmarking eficácia) | Médio (parser novo + persistência + tests) | P1-a |
| Adverse events de CT.gov `resultsSection` / labels | Alto (safety/DD) | Médio | P1-b |
| ANVISA (regulatório Brasil) | Médio-alto (perspectiva BR) | Médio (healthcheck + contrato + parser) | P1-c |
| Normalizador de indicações (`conditions` → `indications` canônico) | Médio (landscapes) | Médio | P2-a |
| Entity resolution de empresas (`sponsors` → `companies` + aliases) | Médio (CI) | Médio-alto | P2-b |
| PMC full-text OA subset | Médio evidência | Médio (licença) | P2-c |

### Onda 3 — Fontes mais complexas (após backbone estável)

- Preprints bioRxiv/medRxiv (`evidence_maturity=preprint`, excluídos de bundles consolidados por padrão).
- ASCO/ESMO/AACR/ASH em ondas (scraping controlado, compliance, kill switch).
- Press releases corporativos.
- Investor decks.
- SEC/EDGAR (API pública).

Regra: não priorizar congressos/press releases antes de estabilizar fontes estruturadas, salvo prioridade explícita diferente na planilha `fontes_priorizacao.xlsx` (premissa viva, §4 `docs/03`).

---

## 3. Plano técnico do data warehouse (raw / processado / curado / current / history)

O modelo lógico já existe (`ADR-001`, `docs/02` "Camadas lógicas"). Este plano descreve como a ingestão o materializa:

### 3.1 Camadas

| Camada | Onde vive | Como é populada | Regra |
|---|---|---|---|
| **raw** | Supabase Storage (bucket raw), objeto `.json.gz` por `source_slug/data/NCT-or-ID/hash` | `store_raw_payload` em cada conector (já wired nos 6) | Imutável, hash-addressed, idempotente por hash; `SourceDocument` guarda path/hash/timestamp/versão |
| **processed** (intermediário) | Em memória no worker + staging DuckDB quando há chave repetida no lote | Parser → normalizer → `PersistenceDecisionEngine` | Dedup exata; quality gates; campo omitido não apaga valor |
| **curated / current** | Tabelas canônicas (`drug_assets`, `clinical_trials`, `regulatory_approvals`, `publications`, `targets`, `indications`, `companies`, `endpoints`, `trial_results`, `adverse_events`) com `is_current=true` | Decisão determinística (`insert`/`replace`/`enrich`/`noop`/`supersede`) | Somente vencedor; `find_trials`/`get_*` filtram `is_current=true` |
| **assertions (history)** | `field_assertions` (bitemporal: `valid_from/to` vs `system_from/to`) | AssertionService por entidade/campo | Append-only; supersede encerra validade; `data_conflicts` preserva divergências |
| **audit / history** | `clinical_trial_asset_history`, `archive_manifests`/`archive_items` (retenção), `manual_corrections`, `mcp_query_logs`, `security_events`, `ingestion_jobs`, `llm_call_logs` | Workers + API + MCP + retention | Fora do caminho quente; retention semanal arquiva com checksum/manifesto |

### 3.2 Entidades — estado de ingestão funcional

| Entidade | Ingestão funcional hoje? | O que falta |
|---|---|---|
| `DrugAsset` | ✅ (CT.gov interventions) | Entity resolution/INN/aliases = MVP+ |
| `Company` | ❌ (strings de sponsor) | Normalizer/Resolver de empresa = P2-b |
| `ClinicalTrial` | ✅ (CT.gov) | Pronto |
| `ClinicalTrialAsset` (relação) | ✅ (`link_trials_to_assets`) | Pronto |
| `Indication` | ❌ (strings de condition) | Normalizer de indicação = P2-a |
| `Target` | ✅ (Open Targets) | Pronto |
| `MechanismOfAction` | ❌ (modelado, sem conector) | Futuro |
| `Endpoint` | ❌ | Parser CT.gov resultsSection = P1-a |
| `TrialResult` | ❌ | Parser CT.gov resultsSection = P1-a |
| `AdverseEvent` | ❌ | Parser CT.gov resultsSection/labels = P1-b |
| `RegulatoryApproval` | ✅ (openFDA + DailyMed + EMA) | Pronto |
| `Publication` | ✅ (PubMed) | PMC full-text = P2-c |
| `SourceDocument` / `EvidenceSnippet` | ✅ (todos) | Pronto |
| `FieldAssertion` | ✅ (CT.gov) | Expandir para demais fontes incrementalmente |
| `DataConflict` | ✅ (`deduplicate_assets`) | Pronto |
| `IngestionJob` | ✅ (JobTracker) | Pronto |

### 3.3 Relações

- trial↔asset: canônico em `clinical_trial_assets` (wired).
- publication↔trial: `linked_trial_ids` em `publications` (PubMed NCT linking contra `clinical_trials`).
- asset↔target, asset↔company, asset↔indication: arrays/strings hoje; migração para tabelas associativas é MVP+ quando normalizers existirem.

---

## 4. Plano técnico do data warehouse — separação raw/processado/curado/current/history

(Consolida o §3 acima; não duplico aqui para evitar redundância. A separação é: raw=Supabase Storage imutável; processed=worker+DuckDB staging; curated=current=tabelas canônicas `is_current=true`; history=`field_assertions` bitemporal + `clinical_trial_asset_history` + audit; conflitos em `data_conflicts`; correções em `manual_corrections`.)

---

## 5. Proposta de automação Celery/beat por fonte

### 5.1 Agenda existente (já válida — confirmada no código)

| Fonte | Frequência | Janela UTC | Fila | Limite/run | Retries | Estratégia |
|---|---|---|---|---|---|---|
| ClinicalTrials.gov | diário | 03:00 | ingest | `CLINICALTRIALS_MAX_RECORDS_PER_RUN=5000` | 3 (backoff 30→300s) | incremental via `last_successful_run` (lookback 2 dias) |
| PubMed | diário | 03:15 | ingest | `PUBMED_MAX_RECORDS_PER_RUN=5000` | 3 | incremental (lookback) |
| openFDA | diário | 03:30 | ingest | `OPENFDA_MAX_RECORDS_PER_RUN=2000` | 3 | sem delta confiável → upsert idempotente por `application_number` |
| DailyMed | diário | 03:45 | ingest | `DAILYMED_MAX_RECORDS_PER_RUN=2000` | 3 | idempotente por `setid` |
| Open Targets | semanal seg | 04:00 | ingest | `OPEN_TARGETS_MAX_RECORDS_PER_RUN=500` | 3 | termos-semente de doença |
| EMA | semanal seg | 04:15 | ingest | `EMA_MAX_RECORDS_PER_RUN=2000` | 3 | export XLSX idempotente por `product_number` |
| freshness | diário | 02:30 | process | — | — | marca stale assertions/trials |
| retention | semanal dom | 04:00 | process | batch 1000 | — | arquiva + expurga elegíveis |

### 5.2 Proposta de complementos (apenas quandoDados ingeridos existirem)

| Job sugerido | Task | Cron sugerido | Fila | Gatilho |
|---|---|---|---|---|
| pós-ingest CT.gov link | `link_trials_to_assets` | 03:50 diário (após CT.gov) | process |专科garante linking de assets recém-criados |
| pós-ingest dedup | `deduplicate_assets` | 04:30 diário | process | registra duplicate candidates em `data_conflicts` |
| confidence scores | `compute_confidence_scores` | 05:00 diário | process | recalcula scores após ingestão |

Estes 3 hoje existem em `process.py` mas não estão no `beat_schedule`. Podem ser adicionados na Onda 1-b (após primeiras ingestões serem validadas) e gate por `if data exists`.

### 5.3 Regras de segurança por job (já no código)

- `task_acks_late=True`, `worker_prefetch_multiplier=1`, `worker_max_tasks_per_child=50` (reset de memória).
- `task_soft_time_limit=3600`, `task_time_limit=7200` (1h soft / 2h hard).
- Falha sistêmica total da página falha o job (não termina verde com zero inserts por erro).
- `record_limit_reached` não é fatal nem provoca retry do mesmo lote.
- Produção valida role `gennomx_worker` em runtime (`assert_database_role`).

### 5.4 Alertas de queda/mudança de volume — proposta mínima

Como não há alerta automático hoje, propõe-se (MVP, sem novo serviço):
- Job do worker registra `IngestionJob` com `records_fetched/inserted/updated/rejected/skipped`.
- Dashboard `/sources` já exibe jobs; uma view simples "delta vs média 7 dias" sinaliza queda.
- (MVP+) Alerta via log estruturado quando `records_fetched < 0.5 * média_7d` para fontes diárias.

---

## 6. Pré-requisitos operacionais antes de rodar em produção/staging

Lista de checks antes de ativar ingestão recorrente em ambiente real:

### 6.1 Ambiente
- [ ] **Escolher alvo do DB:** confirmar se a ingestão inicial acontecerá contra VPS Postgres (`DATABASE_PROVIDER=vps_postgres`) ou Supabase (`supabase_postgres`) — recomendação: staging contra VPS (alvo final); em produção, após cutover aprovado.
- [ ] **Aplicar Alembic head** no alvo ativo (Supabase origem está em `0005`; VPS em `0006`). Recomendação: aplicar `0006` na origem Supabase antes do cutover para paridade.
- [ ] **Redis** acessível (TLS em prod `rediss://`); worker + beat conseguem conectar.
- [ ] **Supabase Storage buckets** `gennomx-raw`/`gennomx-processed`/`gennomx-evidence` criados e `SUPABASE_SERVICE_ROLE_KEY` válida; sem bucket `store_raw_payload` falha fechado.
- [ ] **Supabase Auth/JWKS** ativo (`SUPABASE_JWKS_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `NEXT_PUBLIC_SUPABASE_URL/ANON_KEY`).

### 6.2 Configuração
- [ ] `.env` preenchido com todas as variáveis obrigatórias (`config.py` validações fail-closed).
- [ ] `API_ALLOWED_HOSTS`, `ROOT_PATH=/api/ai`, `CORS_ORIGINS` alinhados à topologia `admin.gennomx.com/ai` + `mcp.gennomx.com` (F4).
- [ ] Tokens MCP (`MCP_TOKEN_CHATGPT/CLAUDE/PRIVATE_AGENT`) definidos (se MCP for validado nesta fase).
- [ ] Limites por conector conservadores para a primeira rodada (ex.: `CLINICALTRIALS_MAX_RECORDS_PER_RUN=200` em dry-run).

### 6.3 Gates de qualidade
- [ ] `make handshake` verde (6 conectores) em ambiente com rede de saída — gate de pré-ativação (read-only).
- [ ] `make release-check` verde (backend lint/test/mypy/bandit + frontend lint/typecheck/build).
- [ ] pytest `tests/unit tests/integration -v --tb=short` verde.
- [ ] (Opcional, rede) smoke-test de um job de ingestão com `max_records` pequeno antes de habilitar o beat.

### 6.4 Deploy/git
- [ ] **Primeiro commit/push** ainda pendente (A5 do `task_plan.md`); planejar sem versionar segredos (`.gitignore` cobre `.env`/`secrets/`).
- [ ] CI GitHub Actions em 8 gates ainda nunca executou de fato (sem commit). Antes de depender do CI como gate, push inicial + verificação dos gates.
- [ ] Backend/worker/beat containerizados e subindo na topologia VPS (ou ambiente staging equivalente).

### 6.5 Segurança/observabilidade
- [ ] Roles `gennomx_app`/`gennomx_worker`/`gennomx_migrator`/`gennomx_readonly` validadas (`rolsuper=false`, `rolbypassrls=false`).
- [ ] Porta 5432 não exposta publicamente (VPS rede interna).
- [ ] Secret management: `.env` fora do Git; secrets rotacionados se `getProjectContents` foi inspecionado (ver `findings.md`).
- [ ] Backup/restore do DB testado (VPS `/backups` ou snapshot Supabase).
- [ ] Logs estruturados (`LOG_FORMAT=json`) rolando; observabilidade mínima de erro de job acessível.

### 6.6 Concorrência VPS
- [ ] Definir concorrência do worker compatível com VPS compartilhada (Traefik + Postgres + app + worker + beat): prefira `--concurrency=1` por fila no início; escalar só com dados.
- [ ] Soft/hard time limits já configurados (1h/2h); garantir que `MAX_RECORDS_PER_RUN` não cause timeouts em fontes grandes.

---

## 7. Backlog priorizado de workflows/features

### Alta prioridade (destravam ingestão útil + auditoria)
1. **Painel de saúde dos conectores** (dashboard `/sources` já existe; adicionar status handshake + última run + delta vs média).
2. **Fila de falhas e retry manual por fonte** (endpoint `POST /api/v1/jobs/{id}/retry` já existe para CT.gov; estender aos demais 5).
3. **Painel de freshness/staleness por entidade** (consome `lifecycle_status=stale`do `mark_stale_assertions`).
4. **Ingestão dry-run por conector** (param `max_records` + `dry_run=True` sem escrita; hoje não existe flag explícita — propõe-se adicionar).
5. **Reprocessamento por `SourceDocument`** (re-executar parser a partir do raw; hoje o raw está no Storage mas não há reprocess — propõe-se endpoint admin).
6. **Fila de conflitos e correções humanas** (`data_conflicts` + `manual_corrections` já existem; UI de triagem é alta).
7. **Métricas de volume por fonte** (view `ingestion_jobs` agregado por fonte/dia).
8. **Alertas de schema drift** (comparar hash de campos esperados vs recebido; MVP).
9. **Bundles MCP com lacunas e evidências** (envelope `limitations`/`gaps` já existe; garantir preenchido quando dados ausentes).

### Média prioridade (evoluem CI/DD)
10. Busca global cross-entity (PostgreSQL FTS view unificada).
11. Entity resolution / alias management (UI + regras; merge fuzzy continua proibido).
12. Revisão humana de merges (four-eyes em `correction_service` já existe).
13. Painel de cobertura por área terapêutica.
14. Export CSV/JSON de bundles.
15. Lineage viewer fonte→assertion→entidade→MCP.

### Baixa/futura
16. Integrações com fontes licenciadas (Evaluate, Citeline, GlobalData, IQVIA, Cortellis, DrugBank).
17. OpenSearch (busca textual robusta).
18. Vector DB dedicado (Qdrant/Weaviate/Pinecone).
19. Analytics warehouse externo (BigQuery/Snowflake).
20. API comercial / billing.
21. Multi-tenant enterprise.

---

## 8. Riscos e mitigação

| Risco | Impacto | Mitigação |
|---|---|---|
| Ingestão em Supabase origem (`0005`) em vez de VPS (`0006`) | Dados em banco legado; cutover depois migra | Escolher e documentar o alvo antes; preferir VPS staging; se Supabase, aplicar `0006` antes |
| Raw storage Supabase sem bucket → ingestão falha fechada | Sem raw imutável | Pré-criar buckets + validar `service_role` no handshake |
| Redis indisponível → worker/beat não rodam | Sem automação | Validar Redis antes do beat; `rediss://` em prod |
| Primeira ingestão pesada satura VPS compartilhada | Indisponibilidade | Limites conservadores; `--concurrency=1`; escalar com dados |
| Nenhuma ingestão real foi testada contra fontes vivas | Comportamento imprevisto | `make handshake` gate; smoke-run com `max_records` pequeno antes do beat |
| Mudança de schema das fontes (CT.gov/openFDA/etc) | Parser quebra | Versionar conectores; testes de contrato no CI; alerta schema drift |
| Conflitos entre fontes sobrescritos silenciosamente | Perda de evidência | `PersistenceDecisionEngine` registra `data_conflicts`; merge fuzzy proibido |
| LLM interno usado como fonte primária | Hallucination | OPENCODE só auxilia; outputs passam por schema validation + evidência + confidence (regra `AGENTS.md` §9) |
| Repro de segredos no primeiro commit | Vazamento | `.gitignore` cobertor; secret scan no CI; nunca commitar `.env`/`secrets/` |
| Cutover produtivo sem validação | Quebra de produto | Nenhum cutover sem handshake + smoke-run + aprovação explícita do Marcus |
| Dados de entidade vazios limitam MCP | UX pobre | `limitations`/`gaps` no envelope MCP; incrementar fontes na Onda 2 |

---

## 9. Critérios de aceite verificáveis

### Onda 1-a (ativação controlada)
- [ ] `make handshake` verde (6 conectores) em ambiente com rede.
- [ ] Primeiro smoke-run de cada dos 6 conectores com `max_records` pequeno registra `IngestionJob` com `status=success|partial` e `records_inserted>0` (ou `skipped` justificado).
- [ ] `source_documents` e `evidence_snippets` criados para cada registro inserido.
- [ ] Raw payloads persistidos no bucket Supabase Storage (path/hash em `SourceDocument`).
- [ ] `data_sources.last_successful_run` atualizado para conectores com cursor incremental.
- [ ] `find_trials`/`search_drugs`/`search_publications`/`get_regulatory_status`/`fetch_source_evidence` retornam dados não-vazios.

### Onda 1-b (automação recorrente)
- [ ] `celery beat` roda 24h sem falha sistêmica; todos os jobs agendados executam pelo menos 1 vez.
- [ ] Logs estruturados rolando; `IngestionJob` persistido por execução.
- [ ] `governance-freshness-daily` e `governance-retention-weekly` executam sem erro (retenção em dry-run primeiro).
- [ ] Adicionados `link_trials_to_assets`/`deduplicate_assets`/`compute_confidence_scores` ao beat (após dados) e validados.

### Onda 2 (lacunas P1)
- [ ] Endpoints/resultados/adverse events de CT.gov `resultsSection` persistidos com teste de parser + persistência + idempotência.
- [ ] ANVISA: handshake + contrato `docs/03` + task + testes.

### Geral (permanente)
- [ ] Nenhum relaxamento de RLS; roles sem superuser/BYPASSRLS; 5432 não público.
- [ ] Nenhuma remoção de Supabase Auth/JWKS/Storage nesta fase.
- [ ] Documentação e `project_state/` atualizados ao final de cada fase.

---

## 10. Plano de execução por fases pequenas (com testes e comandos)

### Fase A — Validação/handshake (reversível, gate de pré-ativação)

**Objetivo:** confirmar conectividade real com as 6 fontes em ambiente com rede, sem escrever dados.

**Comandos:**
```bash
# 1) Carregar .env real (sem versionar)
cp .env.example .env  # preencher valores reais

# 2) Handshake read-only (gate)
make handshake
# saída esperada: 6 OK; exit code 0
```

**Critério:** 6 conectores OK. Se algum falhar, isolar causa (DNS/timeout/credencial) antes de prosseguir.

**Registro:** atualizar matriz Link em `docs/03` §0B com data e latências reais.

### Fase B — Smoke-run incremental pequeno (reversível)

**Objetivo:** primeira ingestão real controlada, limitada, contra DB staging (preferencialmente VPS), validando o pipeline fim a fim sem beat.

**Comandos:**
```bash
# 1) Confirmar alvo DB + migrations
cd backend && python -m alembic -c migrations/alembic.ini current
# esperado: 0006 (head)

# 2) Smoke-run por conector com max_records conservador (sequencial, sem beat)
# Exemplo CT.gov:
celery -A workers.celery_app call workers.tasks.ingest.run_clinicaltrials_ingest \
  --args='["incremental"]' --kwargs='{"max_records": 200}'

# 3) Validar contagens
# via SQL no alvo:
#   select count(*) from clinical_trials;  -> >0
#   select count(*) from source_documents where source_type ilike '%clinical%'; -> >0
#   select count(*) from evidence_snippets where entity_type='clinical_trial'; -> >0
```

Repetir para pubmed/openfda/dailymed/open_targets/ema, um por vez, com `max_records` pequeno.

**Critério:** `IngestionJob` sucesso/parcial; `records_inserted>0` ou `skipped` justificado; raw em Storage; `data_sources.last_successful_run` preenchido para cursoriais.

**Rollback (se necessário):** truncar tabelas recém-criadas em staging (ambiente não-produtivo); reverter `last_successful_run` para NULL (cursor).

### Fase C — Ativar automação recorrente (após B validado)

**Objetivo:** subir worker + beat em ambiente staging/prod com limites ainda conservadores.

**Comandos:**
```bash
# 1) Subir worker (concorrência 1 no início)
celery -A workers.celery_app worker --queues=ingest,process --concurrency=1 --loglevel=info

# 2) Subir beat
celery -A workers.celery_app beat --loglevel=info

# 3) Monitorar 24h
# acompanhar IngestionJob; confirmar execução dos jobs agendados; sem falha sistêmica
```

**Critério:** 24h sem falha sistêmica; todos os jobs do beat executam; freshness + retention rodaram (retenção em dry-run se houver dados elegíveis limitados).

### Fase D — Complementos de processamento (após dados)

Adicionar ao `beat_schedule` (em `celery_app.py`):
```python
"link-trials-assets-daily": {
    "task": "workers.tasks.process.link_trials_to_assets",
    "schedule": crontab(hour=3, minute=50),
    "options": {"queue": "process"},
},
"deduplicate-assets-daily": {
    "task": "workers.tasks.process.deduplicate_assets",
    "schedule": crontab(hour=4, minute=30),
    "options": {"queue": "process"},
},
"confidence-scores-daily": {
    "task": "workers.tasks.process.compute_confidence_scores",
    "schedule": crontab(hour=5, minute=0),
    "options": {"queue": "process"},
},
```
Testar gates; registrar em `docs/09` §0.1 (automações).

### Fase E — Onda 2 (lacunas P1), após backbone estável

Implementar por etapa, cada uma com migração Alembic (se schema) + testes unitários/integração + contrato em `docs/03` + handshake:
- E1: Endpoints/resultados granulares CT.gov `resultsSection`.
- E2: Adverse events CT.gov `resultsSection`/labels.
- E3: ANVISA (handshake + contrato + conector).
- E4: Normalizador de indicações.
- E5: Entity resolution de empresas.
- E6: PMC full-text OA subset.

### Fase F — Onda 3 (fontes complexas), após E estável

Congressos (scraping controlado), preprints, press releases, investor decks, SEC/EDGAR — cada qual com compliance/contrato/handshake.

---

## Primeira fase segura a executar nesta sessão (recomendação)

Dado o ambiente desta máquina (sem rede de saída confirmada para as fontes, VPS Postgres em rede Docker interna, Redis não validado localmente), a implementação de código nesta sessão fica restrita a **documentação/plano + observabilidade/agendamento já existente**:

- ✅ Este plano (registrado em `project_state/plano_ingestao_fase_operacional.md`).
- ✅ Atualização de `project_state/progress.md`, `task_plan.md`, `findings.md`, `docs/11_CHANGELOG_DECISOES.md`.
- ✅ Proposta concreta (não aplicada) de complementos ao `beat_schedule` (Fase D) e a matriz Link atualizada quando o handshake for executado em ambiente com rede.

Não proponho alterar código de conector/persistência/schema nesta sessão, pois isso exigiria ambiente com rede e DB validados (Fase A/B), e a restrição do `AGENTS.md` §13 (testes antes de concluir) não pode ser honrada sem executar gates.

---

## Critério de aceite deste plano (entregável documental)

- [x] Diagnóstico baseado no código real (não em suposições).
- [x] Ordem de ingestão respeita backbone estruturado antes de fontes ruidosas.
- [x] Camadas raw/processado/curado/current/history mapeadas sobre o modelo existente.
- [x] Agenda por fonte com frequência, janela, fila, limites, retries — já maioritariamente implementada e confirmada no código.
- [x] Pré-requisitos operacionais listados (env/rede/gates/git/segurança).
- [x] Backlog por prioridade;风险的 e mitigações; critérios verificáveis.
- [x] Plano por fases pequenas com comandos e rollback.
