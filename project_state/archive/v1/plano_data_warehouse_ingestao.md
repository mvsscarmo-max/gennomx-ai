<!-- validate-links: illustrative-paths -->
# Arquivo VLAEG v1 - data warehouse e ingestao recorrente

**Data de aprovacao:** 2026-07-09  
**Aprovado por:** Marcus  
**Status:** aprovado para inicio de implementacao por fases  
**Escopo:** GennomX AI  
**Protocolo:** VLAEG

## 1. Objetivo

Transformar a base ja implementada da GennomX AI em um data warehouse operacional vivo, com ingestao real e periodica dos conectores ja implementados, cobertura medida por fonte/entidade/ferramenta MCP, dados brutos preservados, dados canonicos rastreaveis, historico bitemporal, qualidade auditavel e expansao racional por ondas.

A meta nao e recriar a arquitetura. O projeto ja possui schema, workers, conectores, MCP, dashboard, Supabase/PostgreSQL e governanca temporal. A meta agora e operacionalizar, medir e expandir.

## 2. Premissas

- A GennomX AI e infraestrutura proprietaria de dados biomedicos e competitivos + MCP, nao chatbot nem gerador final de relatorios.
- O banco principal do MVP e Supabase/PostgreSQL.
- O warehouse operacional se organiza em camadas: raw, processed, curated/current e history/audit.
- O MCP deve consultar somente dados estruturados, seguros, limitados e auditaveis.
- Conectores devem seguir VLAEG: Visao -> Link/handshake -> Arquitetura -> testes/docs -> Gatilho/automacao.
- APIs/exports oficiais tem prioridade. Scraping so entra com politica de dominio, compliance, allowlist, rate limit, kill switch e protecoes SSRF.

## 3. Estado atual a preservar

### 3.1 Conectores implementados

| Fonte | Slug | Frequencia prevista | Principais tabelas alimentadas |
|---|---|---:|---|
| ClinicalTrials.gov | `clinicaltrials_gov` | diaria | `clinical_trials`, `drug_assets`, `source_documents`, `evidence_snippets`, `ingestion_jobs` |
| PubMed | `pubmed` | diaria | `publications`, `source_documents`, `evidence_snippets`, linking por NCT |
| openFDA | `openfda` | diaria | `regulatory_approvals`, evidencias regulatorias |
| DailyMed | `dailymed` | diaria ou 2-3x/semana | `regulatory_approvals.label_url`, evidencias SPL |
| Open Targets | `open_targets` | semanal | `targets`, aliases, associacoes alvo-indicacao |
| EMA | `ema` | semanal | `regulatory_approvals`, evidencias EMA/EU |

Todos os seis estao registrados no `beat_schedule` de `backend/workers/celery_app.py` e possuem task em `backend/workers/tasks/ingest.py`.

### 3.2 Entidades ja modeladas

O schema ja possui modelos para `DrugAsset`, `Company`, `ClinicalTrial`, `ClinicalTrialAsset`, `Indication`, `Target`, `Endpoint`, `TrialResult`, `AdverseEvent`, `RegulatoryApproval`, `Publication`, `DataSource`, `SourceDocument`, `EvidenceSnippet`, `FieldAssertion`, `DataConflict`, `ManualCorrection`, `IngestionJob`, `MCPQueryLog`, `SecurityEvent` e `LLMCallLog`.

### 3.3 Ferramentas MCP ja disponiveis para IA Host

As ferramentas read-only ja previstas/implementadas incluem `search_drugs`, `find_trials`, `compare_assets`, `get_company_pipeline`, `get_trial_results`, `search_publications`, `get_regulatory_status`, `build_report_data_bundle` e `fetch_source_evidence`.

Valor atual provavel para IA Host:

- bom para busca inicial de ativos, trials, publicacoes, targets e status regulatorio;
- medio para pipeline de empresa, pois depende de normalizacao/enriquecimento de companies/sponsors;
- ainda fraco para resultados clinicos granulares, endpoints, safety e mecanismos de acao, porque os modelos existem, mas a ingestao granular ainda precisa evoluir.

## 4. Estrategia de implementacao por ondas

### Onda 1 - Ativacao operacional e inventario real

Objetivo: saber exatamente o que esta pronto, o que roda e o que ja existe no banco real.

Entregas:

- validar `.env.example` versus variaveis reais necessarias;
- confirmar status de Supabase, Alembic, Redis, Celery worker e Celery beat;
- rodar `make handshake` em ambiente com rede liberada;
- criar script/service/endpoint de inventario de cobertura do warehouse;
- registrar contagens por tabela e fonte: ativos, trials, publicacoes, aprovacoes regulatorias, targets, documentos-fonte, evidencias, jobs, conflitos, correcoes e logs MCP;
- medir quais ferramentas MCP retornam dados uteis com o banco atual.

Criterios de aceite:

- diagnostico documentado em `project_state/progress.md`;
- `make handshake` executado ou bloqueio registrado com causa;
- contagens do banco e lacunas registradas;
- nenhuma credencial versionada;
- nenhuma alteracao destrutiva em dados.

### Onda 2 - Ingestao recorrente dos conectores existentes

Objetivo: ligar o backbone ja implementado de forma periodica, idempotente e audivel.

Entregas:

- validar os seis jobs Celery existentes;
- confirmar `beat_schedule` e filas (`ingest`, `process`, `ai`);
- configurar limites por fonte: `*_MAX_RECORDS_PER_RUN`, lookback, rate limits, timeouts, retries/backoff;
- executar dry-run ou execucao controlada por fonte;
- validar persistencia em `IngestionJob`;
- validar raw payload em storage quando aplicavel;
- validar `SourceDocument` + `EvidenceSnippet`;
- validar que reexecucao nao duplica registros nem regride canonico;
- atualizar `docs/09_DEPLOY_E_OPERACAO.md` se a automacao mudar.

Cadencia recomendada:

| Fonte/job | Cadencia | Janela UTC sugerida | Fila | Observacao |
|---|---:|---:|---|---|
| ClinicalTrials.gov | diaria | 03:00 | `ingest` | incremental com lookback; fonte primaria para trials e ativos |
| PubMed | diaria | 03:15 | `ingest` | janela movel; abstracts/metadados |
| openFDA | diaria | 03:30 | `ingest` | sem delta confiavel; upsert idempotente + cap |
| DailyMed | diaria inicialmente; depois 2-3x/semana se volume baixo | 03:45 | `ingest` | labels/SPL; alerta de queda/mudanca de volume |
| Open Targets | semanal | segunda 04:00 | `ingest` | termos-semente/EFO; ampliar depois |
| EMA | semanal | segunda 04:15 | `ingest` | export oficial XLSX; alerta de schema drift |
| Freshness | diaria | 02:30 | `process` | marcar assertions stale sem apagar dados |
| Retencao | semanal | domingo 04:00 | `process` | arquivo/manifesto/checksum antes de expurgo |

### Onda 3 - Painel e contrato de qualidade do warehouse

Objetivo: tornar a expansao mensuravel, nao baseada em impressao.

Entregas:

- definir metricas de cobertura por entidade/fonte: total de registros, percentual com `SourceDocument`, percentual com `EvidenceSnippet`, percentual com relacoes essenciais, entidades stale, conflitos abertos, rejeitados/skipped por fonte, ultima ingestao bem-sucedida por fonte, latencia e duracao de jobs;
- criar API interna ou query/service de cobertura;
- refletir no dashboard existente ou criar tela inicial de `Data Warehouse Health`;
- criar testes unitarios/integracao para o service;
- documentar limiares de alerta.

Qualidade por nivel:

| Nivel | Nome | Criterio |
|---:|---|---|
| 1 | Raw preservado | payload original salvo com hash, timestamp e fonte |
| 2 | Parseado | campos estruturados extraidos e validados |
| 3 | Normalizado | fase/status/datas/nomes/IDs padronizados |
| 4 | Canonico com evidencia | entidade corrente + `SourceDocument` + `EvidenceSnippet` |
| 5 | Enriquecido/conectado | relacoes asset-trial-publication-target-company-regulatory |
| 6 | Curado/confiavel | conflitos resolvidos ou explicitados; freshness e revisao humana versionada |

### Onda 4 - Granularidade clinica: endpoints, resultados e safety

Objetivo: destravar o valor analitico mais importante para due diligence e competitive intelligence.

Entregas:

- analisar `resultsSection` do ClinicalTrials.gov e publicacoes PubMed/PMC para identificar fontes de endpoints/resultados;
- implementar ou expandir parsers para endpoints, bracos, populacoes, timepoints, medidas, valores, comparator values, p-value, CI, hazard ratio, odds ratio e adverse events quando disponiveis;
- persistir em `endpoints`, `trial_results` e `adverse_events`;
- gerar evidencias por campo critico;
- atualizar `get_trial_results` para retornar dados reais e lacunas;
- criar testes de parser, normalizer, idempotencia e MCP.

Criterios de aceite:

- pelo menos um subconjunto de trials com resultados publicos passa a alimentar `endpoints` e `trial_results`;
- `get_trial_results` retorna dados reais quando existirem e gaps quando nao existirem;
- nenhuma inferencia clinica sem evidencia;
- dados negativos/inconclusivos nao sao filtrados silenciosamente.

### Onda 5 - ANVISA e Brasil regulatorio

Objetivo: adicionar diferencial Brasil sem quebrar o backbone global. Esta onda fica fora da primeira rodada.

Entregas futuras: contrato `anvisa`, fase Link/handshake, avaliacao de Dados Abertos/Bulario/consultas, preferencia por API/export, persistencia em `regulatory_approvals` e suporte a `region=BR`/`agency=ANVISA`.

### Onda 6 - PMC full-text / OA subset

Objetivo: ampliar capacidade de extrair resultados, endpoints e contexto alem de abstracts. Esta onda fica fora da primeira rodada.

Entregas futuras: slug separado, controle de licenca artigo-a-artigo, full-text apenas quando permitido, linking PMCID/DOI/PMID, extracao com schema validation e sinalizacao correta de `open_access`.

### Onda 7 - Inteligencia emergente e fontes ruidosas

Objetivo: adicionar sinais recentes sem contaminar evidencia consolidada. Fora da primeira rodada.

Ordem futura: bioRxiv/medRxiv, ASCO/ESMO/ASH, press releases, investor decks e SEC/EDGAR.

## 5. Informacoes disponiveis para IA Host por maturidade

| Area | Disponibilidade atual esperada | Qualidade atual | Proxima melhoria |
|---|---|---|---|
| Ativos/moleculas | Sim, via CT.gov e enriquecimento regulatorio | Boa para nomes/intervencoes; limitada para aliases complexos | entity resolution e aliases |
| Trials | Sim, via ClinicalTrials.gov | Boa para metadados; limitada para resultados | `resultsSection` e endpoints/resultados |
| Publicacoes | Sim, via PubMed | Boa para abstract/metadados; limitada para full-text | PMC/OA subset |
| Regulatorio FDA/EMA/labels | Sim, via openFDA/DailyMed/EMA | Boa quando asset match existe; limitada por match exato | ANVISA + melhor entity resolution |
| Targets | Sim, via Open Targets | Boa como semente; nao exaustiva | ampliar termos/EFO e relacoes asset-target |
| Empresas/pipelines | Parcial | Depende de sponsors e normalizacao | company normalization + fontes corporativas |
| Mecanismos de acao | Parcial/conceitual | Ainda pouco alimentado | Open Targets + labels + curated aliases |
| Endpoints/resultados | Modelos existem; ingestao granular insuficiente | Baixa | Onda 4 |
| Safety/adverse events | Modelos existem; ingestao insuficiente | Baixa | labels, FAERS/openFDA safety, resultsSection |
| Evidencias | Sim para fontes implementadas | Boa onde conector persiste `EvidenceSnippet` | evidencias por campo mais granular |

## 6. Automacao e operacao

Componentes: API FastAPI, Celery worker, Celery beat, Redis, Supabase/PostgreSQL, Supabase Storage/S3-compatible, dashboard Next.js e MCP read-only.

Alertas minimos:

- fonte sem sucesso por mais de 1 periodo esperado;
- queda de volume maior que 70% versus media movel;
- aumento brusco de rejected/skipped;
- schema drift em export/API;
- falha de raw storage;
- job encerrado verde com zero persistencias por erro sistemico;
- latencia acima do limite;
- MCP retornando dados sem evidencia onde deveria haver evidencia;
- uso anomalo de ferramenta MCP.

## 7. Backlog de features

Alta prioridade:

- `WarehouseCoverageService` ou equivalente;
- tela/API de `Data Warehouse Health`;
- dry-run por conector;
- retry manual por fonte/job com parametros seguros;
- reprocessamento por `SourceDocument`;
- painel de freshness/staleness;
- painel de conflitos e correcoes humanas;
- alertas de schema drift e volume;
- bundles MCP com evidencias, lacunas, freshness e conflitos.

Media prioridade:

- busca global cross-entity;
- gerenciador de aliases/entity resolution;
- revisao humana de merges;
- cobertura por area terapeutica;
- export CSV/JSON de bundles;
- lineage viewer fonte -> documento -> assertion -> entidade -> MCP.

Baixa/futura prioridade:

- OpenSearch;
- vector DB dedicado;
- data warehouse analitico externo;
- fontes licenciadas;
- API comercial/billing;
- multi-tenant enterprise.

## 8. Riscos e mitigacoes

| Risco | Impacto | Mitigacao |
|---|---|---|
| Rodar ingestao real sem saber volume/custo | custo, lentidao, quotas | dry-run, caps, janelas, metricas |
| Dados sem evidencia chegarem ao MCP | perda de confianca | quality gates e gaps explicitos |
| Matching exato perder dados regulatorios | cobertura subestimada | painel de skipped + fila de aliases |
| Fuzzy merge unir ativos errados | erro grave de due diligence | merge fuzzy proibido sem revisao humana |
| Scraping violar termos/robots | risco juridico | usar API/export; compliance por dominio |
| Celery beat nao rodar em producao | banco fica stale | healthcheck e alerta de ultimo sucesso |
| Supabase Storage mal configurado | perda de raw auditavel | readiness/storage check antes de ingestao recorrente |
| CI/commit ainda pendente | falta de gate remoto | primeiro commit/push com secret scan antes de operacao real |
| VPS compartilhada sobrecarregar | degradacao do ecossistema | baixa concorrencia, filas separadas, limits |

## 9. Etapas 1-4 aprovadas para inicio

As primeiras quatro etapas aprovadas para outro agente implementar sao:

1. Diagnostico e inventario real do banco, conectores, jobs, MCP e ambiente.
2. Ativacao controlada dos conectores existentes com handshake/dry-run/execucao limitada e validacao de idempotencia.
3. Contrato e camada inicial de qualidade/cobertura do warehouse (`WarehouseCoverageService`/API/dashboard se couber).
4. Granularidade clinica inicial: planejamento tecnico e primeiro incremento seguro para endpoints/resultados/safety.

Nao incluir nesta primeira rodada: ANVISA, PMC full-text, congressos, press releases, investor decks, fontes licenciadas, mudancas amplas de arquitetura ou geracao final de relatorios.

## 10. Validacoes esperadas

Executar conforme ambiente permitir:

```bash
make handshake
make release-check
cd backend && python -m alembic -c migrations/alembic.ini current
cd backend && pytest tests/unit tests/integration -v --tb=short
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm run build
```

Se rede, dependencias ou credenciais bloquearem algum comando, registrar o bloqueio, causa e proxima acao em `project_state/progress.md`.

## 11. Registro obrigatorio ao final de cada fase

Ao concluir qualquer etapa:

- atualizar `project_state/progress.md`;
- atualizar este plano se houver mudanca de escopo;
- atualizar `project_state/task_plan.md` com status;
- atualizar `docs/03_FONTES_E_INGESTAO.md` se alterar conector/fonte;
- atualizar `docs/04_MCP_TOOLS.md` se alterar ferramenta MCP;
- atualizar `docs/09_DEPLOY_E_OPERACAO.md` se alterar automacao;
- registrar decisao em `docs/11_CHANGELOG_DECISOES.md` se houver decisao de arquitetura, fonte, cadencia ou governanca.

## 12. Dependencia nova: migracao do banco para PostgreSQL VPS

Em 2026-07-09, Marcus decidiu migrar o banco principal da GennomX AI do PostgreSQL hospedado da Supabase para PostgreSQL/pgvector hospedado diretamente na VPS. Plano canonico: `project_state/plano_migracao_supabase_postgres_vps.md`.

Consequencia para este plano: a ativacao produtiva pesada da ingestao recorrente deve ocorrer depois do cutover do banco para a VPS. Desenvolvimento de diagnostico, cobertura, qualidade e granularidade clinica pode continuar em local/staging, mas a nova fonte de verdade operacional sera o PostgreSQL VPS.
