# POP — Ingestão de uma nova fonte de dados

**Procedimento Operacional Padrão (VLAEG — Arquitetura, Camada 3).** Define o fluxo determinístico para adicionar/operar um conector. Ver `../docs/13_PROTOCOLO_VLAEG.md`, `../docs/03_FONTES_E_INGESTAO.md`.

> Regra: usar API/export oficial sempre que existir; scraping só com salvaguardas legais (`AGENTS.md` §10).

---

## Pré-requisitos (fases V e L)

1. **V — Visão:** registrar em `project_state/task_plan.md` o objetivo da fonte, o que entra/sai e o critério de sucesso.
2. **Contrato de dados (3.1):** declarar o bloco `{input, processamento, output}` em `docs/03` §0 **antes** de codar.
3. **L — Link:** implementar `healthcheck()` no conector e registrá-lo em `tools/handshake.py`; rodar `make handshake` e atualizar a matriz Link (`docs/03` §0B). Não desenvolver a lógica final sobre integração não validada.

---

## Fluxo determinístico

```text
Conector (BaseConnector)
  → coleta (API/export/upload/scraping) com paginação, rate limit, retry/backoff
  → raw payload + hash (compute_hash) + timestamp
Parser
  → representação intermediária estruturada
Normalizer
  → padronização de fase, status, datas, aliases
Dedup / resolução de entidades
  → idempotência por chave natural (ex.: NCT ID, DOI, INN)
Evidência
  → SourceDocument (documento-fonte) + EvidenceSnippet (trecho que sustenta o dado)
Validação automática
  → schema, campos obrigatórios, plausibilidade
Persistência
  → entidades canônicas + relacionamentos (PostgreSQL)
Auditoria
  → IngestionJob (status, contadores, erro JSON, data_source_id)
```

## Padrões de implementação

- Herdar de `workers/base/connector.py::BaseConnector`; retornar `ConnectorResult`.
- Reutilizar `_make_request`, `compute_hash` e o padrão de `ConnectorResult`.
- Registrar `IngestionJob` via `workers/base/job_tracker.py::JobTracker`.
- Tarefa Celery em `workers/tasks/ingest.py`, fila `ingest`, com `timeout`/`retry`.
- Nunca persistir extração por IA sem schema validation, evidência e confidence score (`AGENTS.md` §9).

## Fases E e G

- **E — Estilo:** se a fonte alimentar telas novas, atualizar `docs/07_DASHBOARD_UX.md`.
- **G — Gatilho:** se a ingestão for agendada, declarar a automação em `docs/09` §0 e adicionar entrada no `beat_schedule` (`workers/celery_app.py`).

## Testes obrigatórios (`docs/06`)

- handshake/healthcheck (sucesso, timeout, credencial inválida);
- contrato de schema com fixture de payload real;
- parser e normalizer;
- idempotência (re-execução não duplica);
- registro de `IngestionJob`.

## Encerramento

- Atualizar `docs/03` (estado implementado + limitações), `project_state/progress.md` e registrar decisão em `docs/11_CHANGELOG_DECISOES.md`.
