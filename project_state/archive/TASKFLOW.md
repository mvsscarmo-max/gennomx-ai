<!-- validate-links: illustrative-paths -->
> ⚠️ **Documento sucedido — ver `project_state/task_plan.md`.**
> A partir da adoção do Protocolo VLAEG (`docs/13_PROTOCOLO_VLAEG.md`), o plano de execução vivo passou para `project_state/task_plan.md`. Este arquivo é preservado como registro histórico (regra `AGENTS.md` §14) e não deve mais ser atualizado.

---

# TASKFLOW — GennomX AI
**Criado em:** 09/06/2026  
**Modelo:** Claude Sonnet 4.6  
**Status:** Histórico (sucedido por `project_state/task_plan.md`)

---

## Visão geral do Taskflow

Este documento define o plano de implementação incremental da GennomX AI, dividido em fases executáveis com objetivos, escopos, entregáveis, dependências, critérios de conclusão e riscos.

A premissa central que guia todas as decisões está em `AGENTS.md`:
> A GennomX AI é uma infraestrutura proprietária de dados biomédicos e competitivos com acesso via MCP. Não é um chatbot nem gerador de relatórios.

Stack aprovada: **Next.js + FastAPI + Celery/Redis + DuckDB (workers) + Supabase/PostgreSQL + pgvector + LiteLLM + MCP server read-only**.

---

## Fase 0 — Estrutura do projeto e infraestrutura de desenvolvimento

### Objetivo
Criar o scaffold completo do projeto com monorepo organizado, Docker Compose para desenvolvimento local, configuração de variáveis de ambiente, tooling de backend e frontend, e `.gitignore`.

### Escopo
- Estrutura de diretórios do monorepo
- Projeto Python (backend) com pyproject.toml/requirements.txt e estrutura FastAPI
- Projeto Node (frontend) com Next.js App Router e Tailwind CSS
- Docker Compose local com PostgreSQL + Redis + pgAdmin
- `.env.example` com todas as variáveis necessárias
- `.gitignore` completo para Python + Node + secrets
- `Makefile` com comandos de desenvolvimento

### Arquivos criados/editados
```
/
├── .env.example
├── .gitignore
├── Makefile
├── TASKFLOW.md
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── auth/
│   │   ├── api/v1/
│   │   ├── models/
│   │   ├── services/
│   │   ├── mcp/
│   │   └── middleware/
│   ├── workers/
│   │   ├── celery_app.py
│   │   ├── connectors/
│   │   ├── parsers/
│   │   ├── normalizers/
│   │   ├── dedup/
│   │   └── tasks/
│   ├── migrations/
│   ├── tests/
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   └── styles/
│   ├── package.json
│   └── Dockerfile
└── infra/
    └── docker-compose.yml
```

### Dependências
- Nenhuma dependência anterior

### Critérios de conclusão
- [ ] `docker-compose up` sobe Postgres, Redis e pgAdmin localmente
- [ ] `cd backend && pip install -e .` não retorna erros de dependência
- [ ] `cd frontend && npm install` não retorna erros críticos
- [ ] Variáveis de ambiente documentadas em `.env.example`
- [ ] Estrutura de diretórios coerente com a arquitetura em `docs/01_ARQUITETURA.md`

### Riscos
- Versões de dependências Python/Node podem conflitar: fixar versões no `requirements.txt`
- Docker pode não estar disponível em CI: preparar opção de instalação sem Docker

---

## Fase 1 — Schema do banco de dados e migrações

### Objetivo
Criar o schema completo do Supabase/PostgreSQL com todas as entidades centrais, sistema de evidências, tabelas de auditoria, políticas RLS e índices.

### Escopo
- Configuração do Alembic para migrações versionadas
- Tabelas de entidades canônicas: DrugAsset, Company, ClinicalTrial, Indication, Target, MechanismOfAction, Endpoint, TrialResult, AdverseEvent, RegulatoryApproval
- Tabelas de publicações: Publication, ConferenceAbstract, PressRelease, InvestorDeck
- Sistema de rastreabilidade: SourceDocument, EvidenceSnippet, DataSource
- Tabelas operacionais: IngestionJob, MCPQueryLog, SecurityEvent, TestRun
- Tabelas de usuários: User, Organization
- Tabelas de relatórios: Report
- Índices para busca textual (tsvector) e lookups frequentes
- Políticas RLS mínimas preparadas desde o MVP
- Extensões: uuid-ossp, pgvector (preparado), pg_trgm

### Arquivos criados/editados
```
backend/
├── migrations/
│   ├── env.py
│   ├── alembic.ini
│   └── versions/
│       ├── 0001_initial_schema.py        ← entidades canônicas
│       ├── 0002_evidence_system.py       ← SourceDocument, EvidenceSnippet
│       ├── 0003_operational_tables.py    ← IngestionJob, MCPQueryLog, etc.
│       └── 0004_indexes_and_rls.py       ← índices e políticas
└── app/
    └── models/
        ├── __init__.py
        ├── db/                           ← SQLAlchemy ORM models
        │   ├── drug_asset.py
        │   ├── company.py
        │   ├── clinical_trial.py
        │   ├── indication.py
        │   ├── target.py
        │   ├── endpoint.py
        │   ├── trial_result.py
        │   ├── adverse_event.py
        │   ├── regulatory_approval.py
        │   ├── publication.py
        │   ├── source_document.py
        │   ├── evidence_snippet.py
        │   ├── data_source.py
        │   ├── ingestion_job.py
        │   ├── mcp_query_log.py
        │   └── security_event.py
        └── schemas/                      ← Pydantic schemas (v2)
```

### Dependências
- Fase 0 concluída (backend Python configurado, Docker rodando)

### Critérios de conclusão
- [ ] `alembic upgrade head` executa sem erro contra Postgres local
- [ ] `alembic downgrade base` e re-upgrade funciona (rollback)
- [ ] Tabelas criadas com todos os campos documentados em `docs/02_MODELO_DE_DADOS.md`
- [ ] Relacionamentos e foreign keys corretos
- [ ] Índices de busca textual aplicados nas colunas críticas
- [ ] Teste de migração em ambiente separado passa

### Riscos
- Schema pode exigir ajustes quando conectores reais forem implementados: usar JSONB para campos semi-estruturados onde a forma ainda é incerta
- RLS incorreta pode bloquear aplicação ou vazar dados: testar com usuários de diferentes roles

---

## Fase 2 — Backend FastAPI: fundação

### Objetivo
Construir a aplicação FastAPI com estrutura de camadas, autenticação, endpoints base protegidos, Pydantic v2 models, logging estruturado e documentação OpenAPI.

### Escopo
- FastAPI app com lifespan, middleware, CORS controlado
- Configuração por ambiente via Pydantic Settings
- Conexão com Supabase/PostgreSQL via asyncpg + SQLAlchemy async
- Auth middleware: JWT via Supabase Auth + API keys internas
- Endpoints iniciais: `/health`, `/api/v1/assets`, `/api/v1/trials`, `/api/v1/companies`, `/api/v1/indications`, `/api/v1/sources`, `/api/v1/jobs`
- Rate limiting por rota (slowapi ou similar)
- Logging estruturado (structlog)
- Tratamento de erros padronizado
- Documentação OpenAPI completa

### Arquivos criados/editados
```
backend/app/
├── main.py
├── config.py
├── database.py
├── auth/
│   ├── __init__.py
│   ├── jwt.py
│   ├── api_key.py
│   └── dependencies.py
├── api/
│   └── v1/
│       ├── __init__.py
│       ├── router.py
│       ├── assets.py
│       ├── companies.py
│       ├── trials.py
│       ├── indications.py
│       ├── sources.py
│       ├── jobs.py
│       └── admin.py
├── services/
│   ├── asset_service.py
│   ├── trial_service.py
│   ├── company_service.py
│   └── source_service.py
├── middleware/
│   ├── logging.py
│   └── rate_limit.py
└── core/
    ├── exceptions.py
    └── responses.py
```

### Dependências
- Fase 1 concluída (schema do banco existe)

### Critérios de conclusão
- [ ] `uvicorn app.main:app --reload` sobe sem erros
- [ ] `/health` retorna 200
- [ ] Endpoints protegidos retornam 401 sem token
- [ ] Endpoints retornam 200 com token válido
- [ ] Documentação OpenAPI acessível em `/docs`
- [ ] Logging estruturado visível no console
- [ ] Testes de unidade dos services passam
- [ ] Testes de integração dos endpoints passam

### Riscos
- asyncpg pode ter comportamentos inesperados com Supabase pooler: testar conexão com PgBouncer
- Rate limiting pode bloquear workers internos: usar allowlist por IP/API key

---

## Fase 3 — Worker Infrastructure: Celery + Redis + DuckDB

### Objetivo
Criar a infraestrutura de workers assíncronos com Celery, Redis como broker, DuckDB para processamento batch e sistema de registro de jobs (IngestionJob).

### Escopo
- Celery app com configuração por ambiente
- Fila de ingestão, fila de parsing, fila de AI/embeddings
- Classe base de conector (BaseConnector) com contrato padrão
- Classe base de parser (BaseParser)
- Integração DuckDB para transformação local de grandes exports
- Registro automático de IngestionJob com status, métricas e erros
- Retry/backoff configurável por tarefa
- Health check de workers exposto via API

### Arquivos criados/editados
```
backend/workers/
├── celery_app.py
├── config.py
├── base/
│   ├── connector.py         ← BaseConnector ABC
│   ├── parser.py            ← BaseParser ABC
│   └── job_tracker.py       ← registro automático de IngestionJob
├── connectors/
│   └── __init__.py
├── parsers/
│   └── __init__.py
├── normalizers/
│   ├── __init__.py
│   ├── phase_normalizer.py
│   ├── status_normalizer.py
│   └── entity_normalizer.py
├── dedup/
│   ├── __init__.py
│   └── strategies.py
├── duck/
│   ├── __init__.py
│   └── processor.py         ← DuckDB batch processor
└── tasks/
    ├── __init__.py
    ├── ingest.py
    └── process.py
```

### Dependências
- Fase 2 concluída (API e banco funcionando)

### Critérios de conclusão
- [ ] `celery -A workers.celery_app worker` inicia sem erro
- [ ] Tarefa de teste registra IngestionJob corretamente no banco
- [ ] DuckDB processa CSV de teste sem erro
- [ ] Retry funciona após falha simulada
- [ ] Health check de worker visível via `/api/v1/jobs/worker-status`

### Riscos
- DuckDB em workers pode consumir muita memória com exports grandes: definir limite de memória por worker
- Jobs sem timeout podem travar fila: timeout obrigatório em todas as tarefas

---

## Fase 4 — Connector: ClinicalTrials.gov

### Objetivo
Implementar o primeiro conector completo: ClinicalTrials.gov API v2, com parser, normalizador, deduplicação, extração de evidências, testes e registro de IngestionJob.

### Escopo
- Conector ClinicalTrials.gov API v2 (paginação, rate limit, retry, backoff)
- Parser de resposta JSON → estruturas intermediárias Python
- Mapeamento para entidades canônicas: ClinicalTrial, Indication, Company (sponsor), DrugAsset, Endpoint
- Normalização de fases, status de trial, países, datas
- Deduplicação por NCT ID
- Extração de EvidenceSnippet para campos críticos
- Cálculo de confidence score inicial
- Armazenamento de raw payload em Supabase Storage
- Testes: unit, contrato (payload salvo), idempotência, regressão

### Arquivos criados/editados
```
backend/workers/connectors/
├── clinicaltrials/
│   ├── __init__.py
│   ├── connector.py
│   ├── parser.py
│   ├── normalizer.py
│   └── mapper.py
└── __init__.py

backend/tests/connectors/
├── fixtures/
│   └── clinicaltrials_sample.json   ← payload real salvo
├── test_ct_connector.py
├── test_ct_parser.py
└── test_ct_normalizer.py
```

### Dependências
- Fase 3 concluída (workers, DuckDB e job tracker funcionando)

### Critérios de conclusão
- [ ] Conector busca trials reais da API do ClinicalTrials.gov
- [ ] Payload bruto salvo em Storage com hash e timestamp
- [ ] IngestionJob registrado com status, volume e erros
- [ ] Trials inseridos no banco com campos críticos preenchidos
- [ ] EvidenceSnippet criado para campos com suporte em fonte primária
- [ ] Teste de idempotência: re-executar não cria duplicatas
- [ ] Teste de contrato com fixture salvo passa
- [ ] Rollback possível (migração de dados reversa)

### Riscos
- API do ClinicalTrials.gov pode ter rate limits não documentados: adicionar sleep adaptativo
- Campos opcionais ausentes em registros reais: parser deve lidar com None graciosamente

---

## Fase 5 — Servidor MCP read-only

### Objetivo
Criar o servidor MCP interno com as ferramentas iniciais, autenticação por token, logging completo, rate limiting e proteções de segurança.

### Escopo
- Servidor MCP integrado ao FastAPI
- Ferramentas iniciais: `search_drugs`, `find_trials`, `get_trial_results`, `get_company_pipeline`, `get_regulatory_status`, `fetch_source_evidence`, `build_report_data_bundle`
- Autenticação: tokens separados por cliente (ChatGPT, Claude, agentes privados)
- Rate limiting por token/ferramenta
- Logging completo: MCPQueryLog com ferramenta, argumentos, entidades acessadas, latência, status
- Validação de argumentos por Pydantic
- Allowlist de campos retornáveis
- Bloqueio de queries SQL ou expressão arbitrária
- Modo read-only obrigatório
- Documentação de ferramentas (schema de entrada e saída)
- Sandbox para testes por modelos host Sandbox de agente, ai-jail e YOLO estão excluídos por D-044; a menção neste parágrafo é isolamento de produto, histórico ou finding, não adoção.

### Arquivos criados/editados
```
backend/app/mcp/
├── __init__.py
├── server.py               ← MCP server entry (FastMCP ou implementação própria)
├── auth.py                 ← token auth para MCP
├── rate_limit.py           ← rate limit por cliente
├── logger.py               ← MCPQueryLog writer
├── tools/
│   ├── __init__.py
│   ├── search_drugs.py
│   ├── find_trials.py
│   ├── get_trial_results.py
│   ├── get_company_pipeline.py
│   ├── get_regulatory_status.py
│   ├── fetch_source_evidence.py
│   └── build_report_data_bundle.py
└── schemas/
    ├── inputs.py
    └── outputs.py

backend/tests/mcp/
├── test_search_drugs.py
├── test_find_trials.py
└── test_mcp_auth.py
```

### Dependências
- Fase 4 concluída (dados de trials reais no banco)

### Critérios de conclusão
- [ ] ChatGPT/Claude consegue chamar `search_drugs` e receber resposta estruturada
- [ ] Token inválido retorna erro 401
- [ ] Rate limit bloqueia após N chamadas configuradas
- [ ] MCPQueryLog registra cada chamada com campos completos
- [ ] Ferramenta retorna EvidenceSnippet e fontes
- [ ] Bloqueio de SQL injection em argumentos
- [ ] Testes de segurança MCP passam
- [ ] Sandbox operacional para testes Sandbox de agente, ai-jail e YOLO estão excluídos por D-044; a menção neste parágrafo é isolamento de produto, histórico ou finding, não adoção.

### Riscos
- Implementação do protocolo MCP pode ter bugs em versões de cliente diferentes: testar com Claude e ChatGPT separadamente
- Ferramentas complexas como `build_report_data_bundle` podem ser lentas: implementar como job assíncrono com polling de status

---

## Fase 6 — Frontend Dashboard: fundação

### Objetivo
Criar o dashboard Next.js com o Design System GennomX (dark mode), fluxo de autenticação, layout base com navegação, página de visão geral e busca global funcional.

### Escopo
- Next.js 15 com App Router e TypeScript
- Design System GennomX: tokens de cor, tipografia, sombras e componentes base
  - Paleta: secondary-slate, brand-rose, neutrals, semantic, dataviz
  - Fontes: Montserrat (display) + Inter (body)
  - Modo escuro como padrão
- Autenticação via Supabase Auth (login por e-mail + magic link)
- Layout base: sidebar, topbar, breadcrumbs, notificações
- Página de Overview: métricas de ativos, trials, fontes, últimas ingestões, alertas
- Busca global funcional (DrugAsset, Company, ClinicalTrial, Indication)
- Tabelas refinadas com filtros e paginação
- Tela de logs de ingestão

### Arquivos criados/editados
```
frontend/src/
├── app/
│   ├── layout.tsx
│   ├── page.tsx                    ← redirect para /dashboard
│   ├── (auth)/
│   │   └── login/page.tsx
│   └── (dashboard)/
│       ├── layout.tsx
│       ├── page.tsx                ← overview
│       ├── search/page.tsx
│       ├── assets/
│       │   ├── page.tsx
│       │   └── [id]/page.tsx
│       ├── trials/
│       │   ├── page.tsx
│       │   └── [id]/page.tsx
│       ├── companies/
│       │   └── [id]/page.tsx
│       ├── logs/page.tsx
│       └── admin/page.tsx
├── components/
│   ├── ui/                         ← design system base (Button, Card, Table, Badge, etc.)
│   ├── layout/                     ← Sidebar, Topbar, Breadcrumbs
│   ├── dashboard/                  ← Overview widgets
│   ├── search/                     ← Global search
│   └── data-tables/                ← Refined tables
├── lib/
│   ├── api-client.ts               ← axios/fetch client para FastAPI
│   ├── auth.ts                     ← Supabase client
│   └── utils.ts
└── styles/
    ├── globals.css
    └── design-tokens.css           ← CSS custom properties do design system
```

### Dependências
- Fase 2 concluída (API funcionando com endpoints de busca)

### Critérios de conclusão
- [ ] `npm run dev` sobe sem erros
- [ ] Login via e-mail funciona (redirect para dashboard)
- [ ] Dashboard overview exibe métricas reais da API
- [ ] Busca global retorna resultados filtráveis
- [ ] Telas de DrugAsset e ClinicalTrial exibem dados do banco
- [ ] Design System GennomX aplicado corretamente (dark mode, tipografia, cores)
- [ ] Testes e2e essenciais com Playwright passam
- [ ] Build de produção (`npm run build`) não tem erros TypeScript

### Riscos
- Design System em dark mode pode ter problemas de contraste: revisar com WCAG 2.1 AA
- API client pode ter problemas de CORS em desenvolvimento: configurar proxy no Next.js

---

## Fase 7 — Testes, CI/CD e consolidação MVP

### Objetivo
Criar a suíte completa de testes automáticos, pipeline CI/CD com gates de qualidade e consolidar o MVP com conectores adicionais (PubMed, openFDA).

### Escopo
- pytest com fixtures, factories e cobertura mínima de 70% em código crítico
- Playwright para testes e2e do dashboard
- Testes de contrato para todos os conectores MVP
- Testes de idempotência e deduplicação
- Data quality checks (Great Expectations ou checks customizados)
- GitHub Actions: lint → type check → unit → integration → security scan → build → e2e
- Secret scanning (git-secrets ou similar)
- Dependency scanning (Safety, pip-audit)
- Conectores adicionais: PubMed/PMC, openFDA
- Documentação de comandos em `AGENTS.md` (seção 16)

### Critérios de conclusão
- [ ] Pipeline CI/CD passa do zero em branch limpa
- [ ] Cobertura mínima de testes críticos atingida
- [ ] Nenhum segredo hardcoded detectado
- [ ] Dependências sem CVE crítico
- [ ] Testes e2e do dashboard passam em headless
- [ ] Conectores PubMed e openFDA funcionais com testes

---

## Fase 8 — Consolidação e documento de memória

### Objetivo
Ao final de cada fase, consolidar tudo o que foi criado, editado, decidido ou pendente em documento de memória Markdown.

### Documentos de memória
- `docs/MEMORY_FASE_0.md` — scaffold, decisões de estrutura
- `docs/MEMORY_FASE_1.md` — schema, migrations, campos críticos
- `docs/MEMORY_FASE_2.md` — API, auth, endpoints
- `docs/MEMORY_FASE_3.md` — workers, Celery, DuckDB
- `docs/MEMORY_FASE_4.md` — ClinicalTrials.gov connector
- `docs/MEMORY_FASE_5.md` — MCP server, tools, logs
- `docs/MEMORY_FASE_6.md` — frontend, design system

---

## Registro de decisões técnicas tomadas durante implementação

| Data | Decisão | Racional |
|---|---|---|
| 09/06/2026 | MCP implementado via FastMCP integrado ao FastAPI | Menor complexidade que servidor MCP separado no MVP |
| 09/06/2026 | SQLAlchemy async + asyncpg para conexão banco | Compatível com FastAPI async e Celery |
| 09/06/2026 | Pydantic v2 para todos os schemas | Performance e validação mais rígida |
| 09/06/2026 | structlog para logging estruturado backend | JSON logs indexáveis |
| 09/06/2026 | Tailwind CSS 4 + CSS custom properties para design system | Tokens do design system como CSS vars, Tailwind para utilities |

---
