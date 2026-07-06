# project_state / task_plan.md — GennomX AI

## Preparação do deploy do MVP — plano aprovado 2026-07-02

Análise do estado real (código, não documentação) confirmou: 9 ferramentas MCP completas,
conectores ClinicalTrials.gov/PubMed/openFDA/DailyMed/Open Targets/EMA implementados, dashboard
Next.js real (13 telas) com auth Supabase/RBAC, CI com 8 gates, banco Supabase real bootstrapado
e migrado até `0005`. Lacunas originalmente identificadas: conectores P1 faltantes, tabela
`regulatory_approvals` sem fonte, ausência de infra de deploy, migração `0006` não aplicada em
produção e hardening MCP/Redis remoto.

Decisões do usuário: escopo = todos os conectores P1; host do backend = Hostinger VPS (frontend em
Vercel/Netlify); prioridade = fechar conectores primeiro, depois prontidão de deploy.

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
| Stack backend Hostinger VPS (API + worker + beat + Caddy + Redis TLS) | ✅ Base implementada 2026-07-02 |
| Planilha `fontes_priorizacao.xlsx` com P1 implementados | ✅ Atualizada 2026-07-02 |
| Git/segredos (primeiro commit, `.env` fora do versionamento) | ⏳ Pendente de ação operacional |
| `alembic upgrade head` real em Supabase produção (`0006`) | ⏳ Pendente de credenciais/rede |
| Frontend em Vercel/Netlify | ⏳ Pendente de provisionamento |
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
