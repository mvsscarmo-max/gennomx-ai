<!-- validate-links: illustrative-paths -->
# Plano de Execução — Conector PubMed (próxima fonte de ingestão)

> **Status:** aprovado, pronto para execução por agente de IA.
> **Leitura obrigatória antes de iniciar:** `AGENTS.md`, `README.md`,
> `docs/00_CONTEXTO_ESTRATEGICO.md`, `docs/01_ARQUITETURA.md`, `docs/13_PROTOCOLO_VLAEG.md`,
> `project_state/task_plan.md` e `docs/03_FONTES_E_INGESTAO.md`.
> **Protocolo:** VLAEG — fazer a fase **L (Link / handshake)** ANTES da lógica final.

---

## 1. Contexto e justificativa

A planilha `project_state/fontes_priorizacao.xlsx` é a **premissa viva de priorização** de novos
conectores (coluna `Prioridade`). Estado atual:

- ClinicalTrials.gov (P1, ordem 1) → **Implementado**.
- **PubMed (P1, ordem 2) → próxima fonte a implementar** (`Recomendação MVP = MVP Core`,
  complexidade Baixa, sem autenticação obrigatória).
- PubMed Central (ordem 3, full-text OA) → **fonte seguinte, FORA desta entrega**.

"Próxima ação técnica" registrada na planilha para PubMed:
*"Implementar ESearch/EFetch/ELink com deduplicação PMID/DOI e enriquecimento por MeSH/NCT."*

Objetivo: alimentar a tabela canônica `publications` (já existe) com dados reais e rastreáveis
(fonte→dado→evidência), dando substrato real ao MCP `search_publications` (já implementado).

### Decisões já tomadas (NÃO reabrir)
1. **Escopo = somente PubMed** (abstracts/metadados via E-utilities). PMC full-text fica para ordem 3.
2. **Slug = `pubmed`**, criado por nova migração. O DataSource legado `pubmed_pmc` permanece
   inativo (não remover).
3. **Incluir linking PMID↔NCT** (ELink + NCT do EFetch) para popular `publications.linked_trial_ids`.

---

## 2. Padrão de referência (reusar — não reinventar)

O conector ClinicalTrials.gov é o template canônico. Reusar diretamente:

| Componente | Arquivo |
|---|---|
| Base do conector + `ConnectorResult` + `HealthcheckResult` | `backend/workers/base/connector.py` |
| Conector exemplo (run/paginate/healthcheck/retry) | `backend/workers/connectors/clinicaltrials/connector.py` |
| Parser exemplo | `backend/workers/connectors/clinicaltrials/parser.py` |
| Normalizer exemplo | `backend/workers/connectors/clinicaltrials/normalizer.py` |
| Task Celery + persistência + helpers | `backend/workers/tasks/ingest.py` |
| JobTracker | `backend/workers/base/job_tracker.py` |
| Raw payload storage | `backend/workers/storage/raw_payload.py` |
| Staging/dedup/quality gate | `backend/workers/base/staging.py` |
| Motor de decisão de persistência | `backend/app/services/persistence_decision.py` |
| Runner assíncrono | `backend/workers/base/async_runner.py` (`run_coroutine`) |
| Handshake (matriz Link) | `tools/handshake.py` |
| Beat schedule | `backend/workers/celery_app.py` |
| Tabela alvo | `backend/app/models/db/publication.py` (`publications`) |
| MCP consumidor | `backend/app/mcp/tools/search_publications.py` |
| Testes exemplo | `backend/tests/unit/test_connector_healthcheck.py`, `test_clinicaltrials_persistence_flow.py` |

### E-utilities (NCBI) — regras de uso
- Base: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils`.
- Sempre enviar `tool=gennomx` e `email=<NCBI_EMAIL>`.
- Rate limit: 3 req/s sem chave; até 10 req/s com `NCBI_API_KEY`. Respeitar
  `PUBMED_RATE_LIMIT_REQUESTS_PER_SECOND`.
- Config já existente em `backend/app/config.py`: `NCBI_API_KEY`, `NCBI_EMAIL`,
  `PUBMED_RATE_LIMIT_REQUESTS_PER_SECOND` (linhas ~89-91).
- Endpoints: `esearch.fcgi` (busca + history), `efetch.fcgi` (metadados/abstract XML),
  `elink.fcgi` (PMID↔NCT), `einfo.fcgi` (healthcheck).

---

## 3. Tarefas de implementação

### Tarefa A — Config (`backend/app/config.py`)
No bloco `# ── Connectors`, ao lado das chaves NCBI já presentes, adicionar:
```python
PUBMED_API_BASE_URL: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PUBMED_MAX_RETRIES: int = 3
PUBMED_INCREMENTAL_LOOKBACK_DAYS: int = 2
PUBMED_MAX_RECORDS_PER_RUN: int = 5000
PUBMED_DEFAULT_QUERY: str = "clinical trial[pt]"   # filtro default, configurável
PUBMED_INGEST_HOUR_UTC: int = 3                      # para o beat schedule
```

### Tarefa B — Pacote do conector `backend/workers/connectors/pubmed/`
Criar espelhando `clinicaltrials/`:

- `__init__.py`
- `connector.py` → `class PubMedConnector(BaseConnector)`, `SOURCE_SLUG = "pubmed"`:
  - `validate_config()` → base URL presente (e-mail recomendado; ausência de chave é permitida).
  - `healthcheck()` → probe leve `einfo.fcgi?db=pubmed&retmode=json`, timeout 10s, retornando
    `ok/unreachable/error/config_error` no mesmo molde do CT.gov.
  - `run(job_type, query=None, updated_since=None, max_records=None, page_handler=None, **kwargs)`:
    1. **ESearch** (`esearch.fcgi`, `db=pubmed`, `usehistory=y`, `retmode=json`) com termo
       (`query` ou `PUBMED_DEFAULT_QUERY`) + janela incremental por data de edição:
       `("YYYY/MM/DD"[EDAT] : "3000"[EDAT])`, derivada de
       `(updated_since or now) - PUBMED_INCREMENTAL_LOOKBACK_DAYS`.
    2. Paginar com `WebEnv` + `query_key` + `retstart`/`retmax` (lote 100–200).
    3. **EFetch** (`efetch.fcgi`, `db=pubmed`, `retmode=xml`) por lote → parsear XML.
       Entregar payloads ao `page_handler` no contrato `{ "raw": <str/dict xml>, "parsed": <obj>,
       "hash": compute_hash(raw) }`.
    - Rate limit via `asyncio.sleep(1/PUBMED_RATE_LIMIT_REQUESTS_PER_SECOND)`.
    - Retry com `tenacity` (backoff exponencial), `MAX_RETRIES = PUBMED_MAX_RETRIES`.
    - `record_limit_reached` (erro NÃO-fatal) ao atingir `max_records`; guardar cursor em metadata.
  - **Parsing XML:** usar `xml.etree.ElementTree` (stdlib) para não adicionar dependência nova.
    Se houver necessidade real de robustez, avaliar `lxml` (já pode estar em deps — verificar
    `backend/pyproject.toml` antes de adicionar).

- `parser.py` → `class PubMedParser` + `ParsedPublication`:
  - Campos: `pmid`, `doi`, `pmcid`, `title`, `abstract`, `journal`, `authors: list[str]`,
    `publication_date: date|None`, `publication_type`, `mesh_terms/keywords: list[str]`,
    `nct_ids: list[str]` (de `<DataBank><DataBankName>ClinicalTrials.gov</…><AccessionNumber>`).
  - Tratar abstracts estruturados (múltiplos `<AbstractText Label=…>`), datas parciais
    (ano/mês/dia) — reaproveitar a lógica de data parcial de `clinicaltrials/parser.py`.

- `normalizer.py` → `class PubMedNormalizer`:
  - Mapear `ParsedPublication` → colunas de `publications`.
  - `publication_type` controlado: `article | preprint | review | abstract | letter`.
  - `evidence_maturity` conforme `docs/03` §7A (default `peer_reviewed_primary`).
  - `registry_source = "pubmed"`; `source_updated_at` a partir da data de edição/`EDAT`.

### Tarefa C — Task Celery (`backend/workers/tasks/ingest.py`)
Adicionar `run_pubmed_ingest` espelhando `run_clinicaltrials_ingest`:
- `@shared_task(bind=True, name="workers.tasks.ingest.run_pubmed_ingest", queue="ingest",
  max_retries=3)`.
- `JobTracker` com slug `"pubmed"`; cursor por `_get_last_successful_run(db, "pubmed")` (helper
  existente, reutilizar).
- `persist_page` → nova `_persist_publications(db, page_result, normalizer)`, análoga a
  `_persist_trials`:
  - stage/dedup por `pmid` (reutilizar `stage_and_deduplicate`);
  - quality gate (criar `validate_publication_record` em `staging.py` OU validação inline mínima:
    `pmid` e `title` obrigatórios);
  - `SourceDocument`: generalizar `_upsert_source_document` para aceitar
    `source_slug/external_id/url/title/source_type`, OU criar
    `_upsert_publication_source_document` (url = `https://pubmed.ncbi.nlm.nih.gov/<pmid>/`,
    `source_type="scientific_publication"`, `license_status="open"`);
  - `PersistenceDecisionEngine.decide(...)` chaveado por `pmid` (mesma estrutura do CT.gov:
    `AssertionCandidate`/`CurrentAssertion`, comparar `source_updated_at` + `value_hash`);
  - upsert em `publications` (insert/update helpers no estilo `_insert_trial`/`_update_trial`,
    respeitando colunas JSONB/ARRAY do modelo);
  - `EvidenceSnippet`: `entity_type='publication'`, fragmento literal (título + abstract + journal +
    pmid), `extraction_method='api_source_fragment'`;
  - **Linking NCT:** preencher `linked_trial_ids` resolvendo cada `nct_id` (do EFetch e/ou ELink
    `dbfrom=pubmed&db=clinicaltrials`) contra `clinical_trials.nct_id`; gravar somente IDs
    existentes; manter NCT não resolvido em `ingestion_metadata` para backfill.
- Invariantes idênticos ao CT.gov: savepoint por registro (`db.begin_nested()`),
  `systemic_failures == len(payloads)` → `RuntimeError` (job falha e reexecuta),
  `record_limit_reached` não dispara retry fatal, `self.retry(exc, countdown)` para erros sistêmicos.
- Reutilizar helpers existentes: `_get_data_source_id`, `_get_last_successful_run`,
  `store_raw_payload`, `_record_data_conflict`.

### Tarefa D — Migração (`backend/migrations/versions/0005_*.py`)
- `INSERT INTO data_sources` para `pubmed` (`category='scientific'`, `access_method='api'`,
  `official_url='https://pubmed.ncbi.nlm.nih.gov'`,
  `api_url='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'`, `license_status='open'`,
  `update_frequency='daily'`, `connector_status='inactive'`, `is_enabled=false`),
  `ON CONFLICT (slug) DO NOTHING` (padrão de `0001_initial_schema.py` ~L676-701).
- **Não** remover/alterar `pubmed_pmc`. `downgrade` remove apenas a linha `pubmed`.
- Confirmar que existem índices únicos em `publications.pmid` e `publications.doi` (o modelo declara
  `unique=True`); se não estiverem materializados na migração inicial, criar nesta migração.

### Tarefa E — Handshake (`tools/handshake.py`)
Em `get_registered_connectors()` importar e adicionar `PubMedConnector()` à lista, para a matriz
Link continuar completa.

### Tarefa F — Beat schedule (`backend/workers/celery_app.py`)
Adicionar entrada `pubmed-daily-incremental` ao `beat_schedule`:
```python
"pubmed-daily-incremental": {
    "task": "workers.tasks.ingest.run_pubmed_ingest",
    "schedule": crontab(hour=getattr(settings, "PUBMED_INGEST_HOUR_UTC", 3), minute=15),
    "kwargs": {"job_type": "incremental"},
    "options": {"queue": "ingest"},
},
```

### Tarefa G — Documentação (obrigatória por `AGENTS.md` §14)
- `docs/03_FONTES_E_INGESTAO.md`:
  - §0 — declarar o **contrato `pubmed`** seguindo o modelo 0.1 (input E-utilities, processamento
    ESearch/EFetch/ELink + dedup PMID, output `publications`+evidências+job).
  - §0B — atualizar a **matriz Link**: linha `pubmed` → Handshake ✅, Status Operacional.
  - §6.8 — registrar o estado implementado do conector PubMed e suas limitações (sem PMC full-text).
- `docs/04_MCP_TOOLS.md`: nota de que `search_publications` passa a ter fonte real `pubmed`.
- `project_state/task_plan.md` e `project_state/progress.md`: registrar a entrega.
- `docs/11_CHANGELOG_DECISOES.md`: registrar decisão de slug `pubmed` (vs. `pubmed_pmc`) e escopo
  (PMC full-text adiado para ordem 3).

### Tarefa H — Testes (`backend/tests/unit/`)
Markers: `@pytest.mark.unit` + `@pytest.mark.connector`.
- `test_pubmed_healthcheck.py` — espelhar `test_connector_healthcheck.py` (ok / unexpected shape /
  timeout / config_error) com `httpx` mockado.
- `test_pubmed_parser.py` — fixture XML EFetch (incluindo `<DataBank>` com NCT e abstract
  estruturado) → asserts de `pmid/doi/title/abstract/authors/nct_ids/publication_date`.
- `test_pubmed_normalizer.py` — mapeamento para colunas `publications` + `publication_type`
  controlado + `evidence_maturity`.
- `test_pubmed_persistence_flow.py` — espelhar `test_clinicaltrials_persistence_flow.py`:
  insert / update / noop / falha sistêmica + linking NCT, com DB mockado.

---

## 4. Critérios de aceite / Verificação

1. **Fase L (Link):** `make handshake` (ou `python tools/handshake.py`) lista `pubmed` com
   status `ok` + latência; matriz Link em `docs/03` §0B atualizada.
2. **Testes:** `cd backend && pytest -m "unit or connector"` todos verdes; sem regressão na suíte
   existente (104+ testes). Usar ambiente Python suportado (<3.14, conforme nota do projeto).
3. **Lint/format:** `ruff check` e `ruff format --check` aprovados no backend.
4. **Migração:** `alembic upgrade head --sql` (offline) inclui o INSERT de `pubmed`; `downgrade`
   reverte só essa linha.
5. **Fluxo real (opcional, requer rede):** disparar `run_pubmed_ingest` com `max_records` pequeno e
   `query` de teste; conferir linhas em `publications`, `source_documents`, `evidence_snippets`,
   `ingestion_jobs` (contadores corretos) e `linked_trial_ids` populado para PMIDs com NCT
   existente.
6. **MCP:** chamar `search_publications` e confirmar retorno com `pmid/doi/abstract` reais e
   rastreabilidade até `SourceDocument`.

---

## 5. Invariantes de conformidade (não violar)

- Nenhuma escrita sem `SourceDocument` + `EvidenceSnippet` + raw payload armazenado (`AGENTS.md` §9).
- Comparar `source_updated_at`/hash antes de atualizar canônico; payload fora de ordem não regride
  o corrente (`docs/03`).
- E-utilities: respeitar rate limit, `tool`+`email`, sem evasão de bloqueios.
- Mudanças pequenas, rastreáveis, reversíveis; atualizar docs e testes na mesma entrega.
- Saída de LLM **não** participa desta entrega (passo 11 adiado).

---

## 6. Fora de escopo (registrar, não implementar)

- PubMed Central full-text / OA subset + controle de licença artigo-a-artigo (**ordem 3** — próxima).
- Deduplicação fuzzy de autores/afiliações; enriquecimento semântico avançado por MeSH.
- Seleção/uso de modelos LLM (passo 11 — adiado pelo usuário).