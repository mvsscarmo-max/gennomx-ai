# Arquivo VLAEG v1 - correcao de ingestao com dry-run

**Data de aprovacao:** 2026-07-10  
**Aprovado por:** Marcus  
**Status:** aprovado para implementacao por fases  
**Escopo:** GennomX AI - ingestao recorrente, ativacao segura dos conectores, dry-run, cobertura do warehouse e primeiros incrementos de granularidade clinica  
**Fora de escopo:** substituir Supabase Auth/JWKS por JWT proprio e Supabase Storage por MinIO/S3-compatible. Essa trilha ja esta sendo conduzida por outro agente em `project_state/plano_remocao_supabase_jwt_minio.md`.

## 1. Objetivo

Corrigir os issues identificados no plano de ativacao operacional da ingestao, transformando os seis conectores ja implementados em um fluxo seguro de operacao com:

- dry-run real antes de escrita;
- ativacao explicita dos `data_sources` corretos;
- smoke-run controlado com `max_records`;
- validacao de raw storage via contrato abstrato, sem amarrar a implementacao final a Supabase ou MinIO;
- agendamento posterior das tasks de processamento;
- metricas de cobertura/qualidade do warehouse;
- primeiro incremento tecnico para endpoints, resultados e adverse events.

O objetivo nao e criar novos conectores nesta rodada. O objetivo e reduzir risco antes da primeira ingestao real recorrente contra o PostgreSQL da VPS.

## 2. Premissas confirmadas

- O banco operacional deve ser o PostgreSQL/pgvector da VPS.
- Os conectores `clinicaltrials_gov`, `pubmed`, `openfda`, `dailymed`, `open_targets` e `ema` ja existem, tem `healthcheck()`, tasks Celery e agenda no `beat_schedule`.
- `anvisa` e `pubmed_pmc` permanecem fora desta correcao.
- O banco esta em estado bootstrap: `data_sources` e `retention_policies` seedados, demais tabelas vazias.
- O runtime de Auth/JWT proprio e MinIO/S3-compatible sera alterado por outro agente. Este plano deve evitar reescrever esse trabalho.
- Enquanto a trilha MinIO nao estiver concluida, o codigo de ingestao deve depender de um contrato de storage, nao de chamadas diretas especificas de provider nos pontos novos.

## 3. Issues e solucoes aprovadas

| Issue | Impacto | Solucao |
|---|---|---|
| `data_sources.is_enabled=false` para todas as fontes | overview/operacao podem indicar fonte inativa mesmo com jobs existentes | criar ativacao controlada dos 6 conectores implementados; manter `anvisa`/`pubmed_pmc` inativos |
| Ausencia de dry-run real nas tasks de ingestao | smoke-run escreve no banco e storage; dificulta preflight seguro | adicionar `dry_run` nas tasks e/ou service comum de ingestao que parseia/normaliza/conta sem persistir |
| Raw storage ainda e ponto de falha operacional | ingestao falha se storage nao estiver pronto | adicionar preflight/check de storage por contrato; integrar depois com MinIO quando a outra trilha concluir |
| Tasks `link_trials_to_assets`, `deduplicate_assets`, `compute_confidence_scores` nao agendadas | dados podem ficar menos conectados apos ingestao | adicionar ao `beat_schedule` apos primeira ingestao validada e com testes de contrato |
| Falta camada de cobertura/qualidade do warehouse | nao ha medida clara de expansao e confianca | implementar `WarehouseCoverageService` + API administrativa e, se couber, painel |
| CT.gov ja traz `resultsSection`, mas parser nao persiste endpoints/resultados/safety | `get_trial_results` permanece vazio | implementar primeiro incremento granular pequeno e testado |
| Empresas e indicacoes seguem como strings | limita `get_company_pipeline` e landscapes | manter fora da primeira correcao executavel; planejar normalizadores deterministas sem merge fuzzy |

## 4. Fases de implementacao

### Fase DRY-0 - Revalidar fronteiras com a trilha JWT + MinIO

Objetivo: evitar conflito com o outro agente.

Tarefas:

- ler `project_state/plano_remocao_supabase_jwt_minio.md` antes de tocar em auth/storage;
- nao remover variaveis Supabase nem pacotes nesta trilha;
- nao implementar MinIO se outro agente ja estiver fazendo;
- ajustar chamadas novas para depender de funcao/contrato de storage existente ou adaptado pelo outro agente;
- se houver conflito de arquivos em `raw_payload.py`, `config.py`, auth ou frontend, parar e reconciliar com a implementacao mais recente.

Aceite:

- plano de ingestao nao desfaz JWT proprio/MinIO;
- nenhum segredo novo versionado;
- nenhum relaxamento de RLS/roles.

**Estado 2026-07-10:** concluída. O runtime atual já usa JWT próprio e MinIO/S3-compatible;
nenhum código desta fase reintroduz Supabase. Cloudflare R2 permanece evolução futura por trás do
mesmo contrato S3-compatible.

### Fase DRY-1 - Ativacao segura de data_sources

Objetivo: tornar explicito quais conectores podem operar.

Tarefas:

- criar script ou endpoint admin para ativar/desativar fontes por slug com allowlist fixa:
  - ativar: `clinicaltrials_gov`, `pubmed`, `openfda`, `dailymed`, `open_targets`, `ema`;
  - manter inativos: `anvisa`, `pubmed_pmc`.
- registrar auditoria via `security_events` ou log estruturado se endpoint admin for criado;
- atualizar `connector_status` para estado coerente: `inactive` antes do primeiro sucesso, `active` apos sucesso, `error` apos falha;
- nao usar SQL manual sem artefato reexecutavel.

Arquivos provaveis:

- `backend/app/api/v1/sources.py` ou novo endpoint admin em rotas existentes;
- `backend/app/services/source_service.py`;
- testes unitarios/integracao em `backend/tests/unit` e/ou `backend/tests/integration`.

Aceite:

- fontes implementadas podem ser habilitadas de forma auditavel;
- `anvisa`/`pubmed_pmc` continuam desabilitadas;
- overview/sources nao confundem seed inativo com conector pronto.

**Estado 2026-07-10:** implementada em código. `is_enabled` agora bloqueia execução real nas tasks
e no trigger administrativo; nenhum dos seis seeds foi ativado automaticamente. A ativação é
`PATCH /api/v1/sources/{slug}/activation`, auditada em `security_events`, e só aceita os seis
slugs implementados.

### Fase DRY-2 - Dry-run real nas tasks de ingestao

Objetivo: permitir preflight de ingestao sem escrita.

Comportamento esperado:

- `dry_run=True` deve executar connector, parser e normalizer;
- deve calcular contadores: fetched, parsed, accepted, rejected, skipped;
- nao deve chamar persistencia de entidades;
- nao deve criar `SourceDocument`, `EvidenceSnippet`, `FieldAssertion` ou entidades canonicas;
- nao deve atualizar `data_sources.last_successful_run`;
- deve criar ou registrar um `IngestionJob` com `job_type='dry_run'` ou metadata `dry_run=true`, desde que isso seja intencional e auditavel;
- erros fatais devem falhar o job, nao retornar verde com zero inserts.

Implementacao recomendada:

1. Criar helper comum para executar um conector com `dry_run`.
2. Reutilizar normalizers existentes.
3. Evitar duplicar seis fluxos de task.
4. Adicionar `dry_run` opcional nas seis tasks: `run_clinicaltrials_ingest`, `run_pubmed_ingest`, `run_openfda_ingest`, `run_dailymed_ingest`, `run_opentargets_ingest`, `run_ema_ingest`.
5. Garantir que `max_records` seja obrigatorio ou fortemente recomendado no endpoint de disparo manual.

Arquivos provaveis:

- `backend/workers/tasks/ingest.py`;
- possivel novo `backend/workers/tasks/ingest_runner.py` ou helper interno;
- testes em `backend/tests/unit/test_ingest_dry_run.py`.

Aceite:

- dry-run dos seis conectores retorna contadores sem alterar tabelas canonicas;
- `last_successful_run` nao muda em dry-run;
- testes provam que persistencia e raw storage nao sao chamados em dry-run;
- `max_records` funciona junto com `dry_run`.

**Estado 2026-07-10:** implementada em código para os seis conectores. O `IngestionJob` é
preservado como evidência operacional com `job_type=dry_run` e contagens em `metadata`; nenhum
cursor ou estado da fonte é alterado.

### Fase DRY-3 - Disparo admin controlado

Objetivo: substituir acionamento manual via console por caminho operacional seguro.

Tarefas:

- criar `POST /api/v1/sources/{slug}/run` ou rota equivalente sob admin;
- aceitar payload restrito: `job_type`, `max_records`, `dry_run` e filtros opcionais ja suportados (`query`, `conditions`, `interventions`);
- rejeitar slugs desconhecidos ou fontes desabilitadas, salvo modo dry-run admin explicitamente permitido;
- mapear slug para task sem SQL dinamico nem import arbitrario;
- retornar `celery_task_id`, slug, parametros sanitizados e modo.

Arquivos provaveis:

- `backend/app/api/v1/sources.py` ou `backend/app/api/v1/jobs.py`;
- `backend/app/services/source_service.py`;
- testes em `backend/tests/unit/test_sources_run_api.py`.

Aceite:

- admin consegue agendar dry-run por fonte com `max_records`;
- admin consegue agendar smoke-run real limitado apos dry-run verde;
- usuario nao-admin recebe 403;
- parametros perigosos sao rejeitados.

**Estado 2026-07-10:** implementada em `POST /api/v1/sources/{slug}/run`. Exige admin,
`max_records`, allowlist estática, teto configurável, filtros limitados a fontes que os suportam e
auditoria em `security_events`.

### Fase DRY-4 - Preflight de storage e ambiente

Objetivo: impedir que a ingestao real comece com storage quebrado.

Tarefas:

- criar check de storage usado por readiness operacional ou comando de preflight;
- testar escrita/leitura/delecao ou escrita idempotente de objeto pequeno em prefixo de healthcheck;
- se MinIO ja estiver implementado pelo outro agente, usar o adapter S3-compatible;
- se Supabase Storage ainda for o backend ativo, manter compatibilidade temporaria;
- registrar falha de storage como bloqueio de smoke-run real.

Arquivos provaveis:

- `backend/workers/storage/raw_payload.py` ou adapter equivalente criado pela trilha MinIO;
- `backend/app/api/v1/health.py`/readiness se existir;
- `tools/handshake.py` pode receber uma secao opcional de storage, separada dos conectores externos.

Aceite:

- preflight indica claramente provider ativo e status;
- ingestao real nao e habilitada se storage raw falhar;
- dry-run continua podendo rodar sem storage.

**Estado 2026-07-10:** implementada para o provider ativo por
`POST /api/v1/sources/storage-preflight`. O check escreve, lê e remove um objeto efêmero; dry-run
permanece independente de storage. A task real repete o check como gate fail-closed antes de buscar
dados. A execução real em VPS continua pendente.

### Fase DRY-5 - Coverage/quality service do warehouse

Objetivo: medir se o banco esta crescendo com qualidade.

Tarefas:

- implementar `WarehouseCoverageService`;
- expor API administrativa read-only, por exemplo `GET /api/v1/warehouse/coverage`;
- calcular contagens por entidade/fonte, ultimo sucesso/falha por fonte, percentual com `SourceDocument`, percentual com `EvidenceSnippet`, jobs por status, conflitos abertos, logs MCP recentes, entidades stale e lacunas conhecidas;
- retornar `limitations` para a IA Host nao superestimar cobertura.

Arquivos provaveis:

- `backend/app/services/warehouse_coverage_service.py`;
- `backend/app/api/v1/warehouse.py`;
- docs em `docs/03_FONTES_E_INGESTAO.md` e `docs/09_DEPLOY_E_OPERACAO.md`;
- opcional: tela no dashboard somente se o escopo da rodada permitir.

Aceite:

- API retorna cobertura em banco vazio e em banco com fixtures;
- testes unitarios/integracao cobrem agregados principais;
- lacunas aparecem explicitamente.

**Estado 2026-07-10:** implementada em `GET /api/v1/warehouse/coverage`, restrita a admin. A
resposta separa inventário, rastreabilidade, estado por fonte, jobs e limitações explícitas; não
apresenta contagem como cobertura global de mercado. A validação contra dados reais da VPS segue
pendente.

### Fase DRY-6 - Agendar processamento pos-ingestao

Objetivo: conectar dados apos ingestao sem trabalho manual.

Tarefas:

- adicionar ao `beat_schedule`, apos primeira ingestao real validada: `link_trials_to_assets`, `deduplicate_assets`, `compute_confidence_scores`;
- considerar guard leve para banco vazio, retornando sucesso com `updated=0`;
- documentar em `docs/09`;
- adicionar teste de contrato do `beat_schedule`.

Aceite:

- `beat_schedule` contem os tres jobs de processamento;
- tasks rodam bem em banco vazio;
- docs refletem a automacao.

### Fase DRY-7 - Primeiro incremento CT.gov resultsSection

Objetivo: destravar `get_trial_results` de forma incremental.

Escopo inicial recomendado:

1. endpoints planejados de `protocolSection.outcomesModule`;
2. outcomes/resultados de `resultsSection.outcomeMeasuresModule` para trials com resultados publicos;
3. adverse events de `resultsSection.adverseEventsModule` em incremento separado se o parser ficar grande.

Regras:

- persistir em `endpoints`, `trial_results`, `adverse_events`;
- manter evidencias por campo critico;
- nao inferir eficacia/safety sem dado literal;
- dados ausentes devem virar `gaps`, nao erro;
- idempotencia obrigatoria.

Arquivos provaveis:

- `backend/workers/connectors/clinicaltrials/parser.py`;
- `backend/workers/connectors/clinicaltrials/normalizer.py`;
- `backend/workers/persistence/trials.py` ou novo modulo de persistencia granular;
- `backend/app/mcp/tools/get_trial_results.py`;
- testes de parser, normalizer, persistencia e MCP.

Aceite:

- pelo menos fixtures CT.gov com `resultsSection` populam endpoints/resultados;
- `get_trial_results` retorna dados reais para fixture e gaps para trial sem resultados;
- reexecucao nao duplica endpoints/resultados;
- nenhum dado negativo/inconclusivo e filtrado silenciosamente.

## 5. Sequencia operacional recomendada

1. Merge/rebase com a trilha JWT + MinIO antes de iniciar storage/auth.
2. Implementar DRY-1 a DRY-3 localmente com testes.
3. Implementar DRY-4 usando o provider ativo no momento.
4. Implementar DRY-5.
5. Rodar gates locais.
6. Em staging on-VPS: `make handshake`, dry-run dos seis conectores com `max_records` pequeno, preflight storage, smoke-run real sequencial, coverage e MCP, beat somente depois.
7. Implementar DRY-6 apos primeira ingestao validada.
8. Implementar DRY-7 como evolucao de dados clinicos.

## 6. Validacoes esperadas

```bash
make handshake
make release-check
cd backend && pytest tests/unit tests/integration -v --tb=short
cd backend && python -m alembic -c migrations/alembic.ini current
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm run build
```

Testes especificos esperados:

- dry-run nao persiste entidades/documentos/evidencias;
- dry-run nao atualiza cursor;
- endpoint admin exige admin;
- slugs desconhecidos sao rejeitados;
- `data_sources` corretos sao ativados/desativados;
- coverage service funciona em banco vazio;
- beat schedule contem tasks pos-ingestao quando a fase DRY-6 for implementada;
- parser CT.gov granular cobre fixtures com e sem `resultsSection`.

## 7. Rollback

Rollback de codigo:

- reverter rota/admin trigger se causar risco operacional;
- manter tasks Celery antigas funcionando com defaults `dry_run=False`;
- remover entradas novas do `beat_schedule` se alguma task pos-ingestao falhar.

Rollback de dados em staging:

- dry-run nao escreve dados;
- smoke-run real deve ser feito inicialmente em staging com `max_records` pequeno;
- se necessario, truncar tabelas populadas em staging e resetar `data_sources.last_successful_run`.

Rollback produtivo:

- pausar beat;
- pausar worker;
- manter API read-only se necessario;
- restaurar backup do PostgreSQL VPS conforme runbook;
- reativar apenas dry-run ate causa ser isolada.

## 8. Riscos e mitigacoes

| Risco | Mitigacao |
|---|---|
| Conflito com agente JWT/MinIO | DRY-0 obrigatoria; nao remover Supabase nem implementar MinIO nesta trilha |
| Dry-run virar quase duplicacao de pipeline | criar helper comum e testes de contrato |
| Endpoint admin virar ferramenta perigosa | require_admin, allowlist de slugs, teto de `max_records`, parametros sanitizados |
| Storage falhar apos dados parseados | preflight antes de smoke-run real; dry-run independente de storage |
| Beat processar dados cedo demais | DRY-6 so apos primeira ingestao validada |
| Parser granular CT.gov crescer demais | dividir endpoints/resultados/adverse events em incrementos pequenos |
| MCP parecer vazio mesmo com ingestao parcial | `WarehouseCoverageService` e `limitations` explicitos |

## 9. Estado esperado ao final

- Seis conectores prontos para dry-run e smoke-run controlado.
- Fontes implementadas habilitadas de forma auditavel.
- Preflight de storage/env documentado.
- Coverage service expondo a qualidade real do warehouse.
- Tasks pos-ingestao agendadas apos validacao.
- Primeiro incremento de resultados clinicos pronto ou tecnicamente planejado com fixtures.
- Trilha JWT proprio + MinIO preservada e integrada por contrato, sem conflito de escopo.
