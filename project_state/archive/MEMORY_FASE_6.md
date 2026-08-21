<!-- validate-links: illustrative-paths -->
> ⚠️ **Histórico consolidado em `project_state/progress.md`.** Preservado como registro detalhado da fase (regra `AGENTS.md` §14).

# MEMORY — Fase 6: Testing Infrastructure + CI/CD

**Data de conclusão:** 2026-06-09  
**Status:** ✅ Concluída (estrutura base)

---

## Objetivo

Estabelecer infraestrutura de testes (pytest, fixtures, unit + integration) e pipeline CI/CD
com GitHub Actions para lint, type check, testes unitários e de integração.

---

## Arquivos Criados

### Backend — Testes

| Arquivo | Descrição |
|---|---|
| `backend/pytest.ini` | Config: asyncio_mode=auto, markers (unit, integration, mcp, connector, slow), testpaths=tests |
| `backend/tests/__init__.py` | Pacote raiz |
| `backend/tests/conftest.py` | Fixtures: `mock_db` (AsyncMock), `FakeRow`, `FakeResult`, `override_settings` (monkeypatch env vars) |
| `backend/tests/unit/__init__.py` | Pacote unit |
| `backend/tests/unit/test_asset_service.py` | Testes de `AssetService`: list vazia, shape, filtro q, offset paginação, NotFoundError no detail |
| `backend/tests/unit/test_clinicaltrials_parser.py` | Testes de `ClinicalTrialsParser`: NCT ID, títulos, status, condições, fase, módulos faltantes, `_parse_date` |
| `backend/tests/unit/test_clinicaltrials_normalizer.py` | Testes de `ClinicalTrialsNormalizer`: STATUS_MAP, PHASE_MAP, `extract_drug_names` |
| `backend/tests/unit/test_connector_base.py` | Testes de `ConnectorResult` e `BaseConnector`: contadores, hash SHA-256, finish() |
| `backend/tests/unit/test_mcp_server.py` | Testes de auth (`_authenticate_mcp`), rate limiting (`_check_rate_limit`, `_rate_buckets`), blocklist |
| `backend/tests/integration/__init__.py` | Pacote integration |
| `backend/tests/integration/conftest.py` | Fixtures de integração: engine real + sessão com rollback |
| `backend/tests/integration/test_health.py` | Teste de `/health` endpoint com `httpx.AsyncClient + ASGITransport` |

### CI/CD

| Arquivo | Descrição |
|---|---|
| `.github/workflows/ci.yml` | Pipeline com 5 jobs paralelos: backend-lint, backend-unit, frontend-lint, frontend-build, security |

---

## Design dos Testes

### Padrões aplicados

1. **Fixtures de mock**: `mock_db` usa `AsyncMock(spec=AsyncSession)` — qualquer método não configurado explicitamente falha, evitando testes que passam por acidente.

2. **FakeRow / FakeResult**: Simula `Row` e `Result` do SQLAlchemy sem precisar de banco. Cada teste configura os retornos diretamente.

3. **`override_settings` autouse**: Toda suite recebe variáveis de ambiente válidas via monkeypatch — evita `ValidationError` de settings ao importar módulos.

4. **Rollback em integration**: `test_db` fixture faz `rollback()` no teardown — testes de integração não deixam dados persistidos.

5. **Markers segregados**: `@pytest.mark.unit` (sem deps externas), `@pytest.mark.integration` (requer DB + Redis), `@pytest.mark.mcp`, `@pytest.mark.connector`.

### Cobertura atual (Fase 6)

| Módulo | Testes unit | Testes integração |
|---|---|---|
| `AssetService` | ✅ 5 testes | ⏳ Pendente |
| `ClinicalTrialsParser` | ✅ 11 testes | — |
| `ClinicalTrialsNormalizer` | ✅ 6 testes | — |
| `ConnectorResult / BaseConnector` | ✅ 7 testes | — |
| `MCP server auth + rate limit` | ✅ 6 testes | — |
| `FastAPI /health` | — | ✅ 2 testes |
| `CompanyService` | ⏳ | ⏳ |
| `TrialService` | ⏳ | ⏳ |
| `SourceService` | ⏳ | ⏳ |
| `MCP tools (search_drugs etc.)` | ⏳ | ⏳ |

---

## Atualização 2026-06-12

- Adicionado teste unitário para confirmar que `_dispatch_tool()` recebe e repassa a sessão de banco injetada pelo FastAPI.
- Adicionado `backend/tests/unit/test_source_service.py` cobrindo `SourceService.list_jobs()` e `SourceService.get_job_detail()`.
- Adicionado `backend/tests/unit/test_job_tracker.py` cobrindo resolução de `data_source_id` e serialização JSON de erro/metadados.
- Adicionado `backend/tests/unit/test_clinicaltrials_asset_linking.py` cobrindo criação inicial de `DrugAsset` a partir de intervenções ClinicalTrials.gov e backfill `trial→asset`.
- Corrigido `pyproject.toml` para instalação editável com `setuptools.build_meta:__legacy__`.
- Corrigido logging `structlog` para usar `structlog.stdlib.LoggerFactory()`.
- Corrigidos atributos ORM reservados `metadata` em modelos SQLAlchemy.
- Corrigido `ConnectorResult` nos testes para a API atual.
- Backend validado com `py -m ruff format .`, `py -m ruff check .` e `py -m pytest tests -q` — 50 testes passando.
- Frontend atualizado para Next 15.5.18, com `package-lock.json` gerado e CI usando `npm ci`.
- Frontend validado com `npm run lint`, `npm run typecheck` e `npm run build`.

---

## Pipeline CI/CD — GitHub Actions

```
Trigger: push/PR para main ou develop
Concurrency: cancela runs anteriores do mesmo branch

Jobs:
  backend-lint      → ruff check + ruff format --check + mypy (non-blocking)
  backend-unit      → pytest tests/unit/ (sem serviços externos)
  backend-integration → migrate + pytest tests/integration/ (com postgres + redis)
  frontend-lint     → eslint + tsc --noEmit
  frontend-build    → npm run build
  security          → pip-audit + bandit (non-blocking)

Deps:
  backend-integration depende de: backend-lint + backend-unit
  frontend-build depende de: frontend-lint
  security depende de: backend-unit
```

---

## Pendências

- [ ] Testes unit para `CompanyService`, `TrialService`, `SourceService`
- [ ] Testes unit para todos os 9 MCP tools
- [ ] Testes de integração para endpoints REST com DB real
- [ ] Testes de conectores com `httpx.MockTransport` (mock da ClinicalTrials.gov API)
- [ ] Playwright e2e para frontend (assets list + asset detail)
- [ ] Coverage report (pytest-cov) + upload para Codecov
- [ ] Dockerfile multi-stage para frontend (`FROM node:20-alpine`)
- [ ] Job de deploy (Vercel para frontend, Railway/Render para backend)
