<!-- validate-links: illustrative-paths -->
> ⚠️ **Histórico consolidado em `project_state/progress.md`.** Preservado como registro detalhado da fase (regra `AGENTS.md` §14).

# MEMORY — Fase 2: Serviços FastAPI, Schemas Pydantic, Workers Celery

**Data de conclusão:** 2026-06-09  
**Status:** ✅ Concluída

---

## Objetivo

Criar a camada de serviços da API REST, schemas de validação Pydantic v2, tarefas Celery
(ingest + process), conector ClinicalTrials.gov, server MCP e Dockerfile do backend.

---

## Arquivos Criados / Editados

### Serviços (Service Layer)

| Arquivo | Descrição |
|---|---|
| `backend/app/services/asset_service.py` | `AssetService`: `list_assets()` com filtros + `get_asset_detail(UUID)` |
| `backend/app/services/company_service.py` | `CompanyService`: `list_companies()` com filtros + `get_company_detail(UUID)` |
| `backend/app/services/trial_service.py` | `TrialService`: `list_trials()` com filtros + `get_trial_detail(UUID)` |
| `backend/app/services/source_service.py` | `SourceService`: `list_sources()` paginado + `get_source_detail()` + `list_jobs()` |

**Padrão consistente em todos os serviços:**
- Recebem `AsyncSession` via injeção no construtor
- `list_*()` retorna `tuple[list[dict], int]` (itens + total para paginação)
- `get_*_detail(UUID)` lança `NotFoundError` se não encontrado
- Usam `text()` do SQLAlchemy para SQL direto (performance) + parâmetros nomeados anti-injection

### Schemas Pydantic

| Arquivo | Modelos |
|---|---|
| `backend/app/models/schemas/drug_asset.py` | `DrugAssetList`, `DrugAssetDetail` |

**Pendente:** schemas para `Company`, `Trial`, `Indication` (endpoints usam `dict` por enquanto).

### Workers Celery

| Arquivo | Descrição |
|---|---|
| `backend/workers/tasks/process.py` | Tarefas de pós-processamento: `link_trials_to_assets` com backfill real; `deduplicate_assets` e `compute_confidence_scores` ainda como stubs |
| `backend/workers/tasks/ingest.py` | `run_clinicaltrials_ingest` — tarefa completa com JobTracker + persistência |
| `backend/workers/connectors/clinicaltrials/connector.py` | Conector com paginação, rate limit, retry (tenacity) |
| `backend/workers/connectors/clinicaltrials/parser.py` | `ClinicalTrialsParser` — parseia todos os módulos do protocolSection |
| `backend/workers/connectors/clinicaltrials/normalizer.py` | Mapas de status/phase + `normalize()` + `extract_drug_names()` |

### Infraestrutura

| Arquivo | Descrição |
|---|---|
| `backend/Dockerfile` | Multi-stage build, Python 3.12-slim, non-root user, porta 8000 |

---

## Decisões Técnicas

### 1. SQL direto vs. ORM nos serviços
**Decisão:** `text()` raw SQL nos serviços de listagem, ORM só para inserções/updates.  
**Motivo:** Filtros dinâmicos com ARRAY/JSONB são mais legíveis em SQL raw; COUNT(*) + data em
duas queries separadas é mais simples do que `.count()` com subquery no ORM async.

### 2. Schemas retornam `dict` não `BaseModel` na maioria dos endpoints
**Decisão:** `list_*()` retorna `list[dict]`, serialização feita pelo FastAPI.  
**Motivo:** Evita overhead de validação no sentido service→response; os dados já vêm do banco
estruturados. `DrugAssetDetail` usa `response_model=DrugAssetDetail` no GET detalhe.

### 3. `SourceService.list_sources()` com parâmetros de paginação
**Decisão:** Assinatura com `status`, `page`, `page_size` para alinhar com endpoint `sources.py`.  
**Motivo:** Endpoint chamava `service.list_sources(status=..., page=..., page_size=...)` — service
teve que ser ajustado para retornar `tuple[list[dict], int]`.

### 4. `workers/tasks/process.py` com stubs
**Decisão:** Criar arquivo com tarefas stub (retornam `not_implemented`).  
**Motivo:** `celery_app.py` já referencia `workers.tasks.process` em `include=`. Sem o arquivo
o worker não inicializa. Implementação real na Fase 3.

---

## Estado dos Endpoints API

| Rota | Status | Service | Schema |
|---|---|---|---|
| `GET /api/v1/assets` | ✅ funcional | `AssetService` | `dict` |
| `GET /api/v1/assets/{id}` | ✅ funcional | `AssetService` | `DrugAssetDetail` |
| `GET /api/v1/companies` | ✅ funcional | `CompanyService` | `dict` |
| `GET /api/v1/companies/{id}` | ✅ funcional | `CompanyService` | `dict` |
| `GET /api/v1/trials` | ✅ funcional | `TrialService` | `dict` |
| `GET /api/v1/trials/{id}` | ✅ funcional | `TrialService` | `dict` |
| `GET /api/v1/indications` | ⚠️ stub | — | `dict` |
| `GET /api/v1/sources` | ✅ funcional | `SourceService` | `dict` |
| `GET /api/v1/jobs` | ⚠️ stub | — | `dict` |
| `GET /api/v1/jobs/worker-status` | ✅ funcional | Celery inspect | `dict` |
| `POST /api/mcp/call` | ✅ funcional | 9 tools MCP | `dict` |

---

## Pendências para Fase 3 e além

- [ ] Implementar `IndependenceService` com `list_indications()` e `get_indication_detail()`
- [ ] Criar schemas Pydantic para `Company`, `Trial`, `Indication` (resposta tipada)
- [ ] Implementar lógica real em `deduplicate_assets` e `compute_confidence_scores`
- [ ] Adicionar conectores: PubMed, openFDA, DailyMed, Open Targets, EMA, ANVISA
- [ ] Testes unitários para serviços (mock DB) e integração (Testcontainers PostgreSQL)

### Atualização 2026-06-12

- `GET /api/v1/jobs` passou a usar `SourceService.list_jobs()` com paginação e filtros por `source_id`, `source_slug` e `status`.
- `POST /api/v1/jobs/{job_id}/retry` passou a reenfileirar jobs `clinicaltrials_gov` via Celery.
- `JobTracker` passou a preencher `data_source_id` e serializar `error_detail`/`metadata` como JSON válido.
- ClinicalTrials.gov passou a criar/reusar `SourceDocument` e criar `EvidenceSnippet` básico durante a persistência de trials.
- ClinicalTrials.gov passou a criar/atualizar `DrugAsset` a partir de intervenções terapêuticas, preencher `clinical_trials.drug_asset_ids` e criar evidência vinculada ao ativo.
- `workers.tasks.process.link_trials_to_assets` deixou de ser stub e passou a executar backfill de trials já ingeridos sem vínculo com ativos.

---

## Estrutura de Diretórios — Fase 2

```
backend/
├── Dockerfile
├── pyproject.toml
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── auth/dependencies.py
│   ├── core/{exceptions,logging,responses}.py
│   ├── middleware/logging.py
│   ├── api/v1/{router,assets,companies,trials,indications,sources,jobs}.py
│   ├── mcp/{server.py,tools/*.py}
│   ├── models/
│   │   ├── db/{base,drug_asset,company,trial,indication,...}.py
│   │   └── schemas/drug_asset.py
│   └── services/{asset,company,trial,source}_service.py
├── workers/
│   ├── celery_app.py
│   ├── base/{connector,job_tracker}.py
│   ├── connectors/clinicaltrials/{connector,parser,normalizer}.py
│   └── tasks/{ingest,process}.py
└── migrations/
    ├── env.py
    └── versions/0001_initial_schema.py
```
