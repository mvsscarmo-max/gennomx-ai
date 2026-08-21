<!-- validate-links: illustrative-paths -->
# Arquivo VLAEG v1 - prompt de implementacao do data warehouse

Você trabalhará no projeto `GennomX AI`, dentro do workspace da GennomX.

Antes de qualquer ação, leia obrigatoriamente:

1. `AGENTS.md`
2. `project_state/task_plan.md`
3. `project_state/findings.md`
4. `project_state/progress.md`
5. `project_state/plano_data_warehouse_ingestao.md`
6. `docs/00_CONTEXTO_ESTRATEGICO.md`
7. `docs/01_ARQUITETURA.md`
8. `docs/02_MODELO_DE_DADOS.md`
9. `docs/03_FONTES_E_INGESTAO.md`
10. `docs/04_MCP_TOOLS.md`
11. `docs/08_ROADMAP.md`
12. `docs/09_DEPLOY_E_OPERACAO.md`
13. `docs/11_CHANGELOG_DECISOES.md`
14. `project_state/fontes_priorizacao.xlsx`

## Objetivo

Iniciar a implementação das etapas 1-4 do plano aprovado de data warehouse e ingestão recorrente da GennomX AI.

Não trate o projeto como se estivesse do zero. A base já possui schema, workers, conectores, MCP, dashboard, Supabase/PostgreSQL, raw storage, evidências e governança temporal. Sua missão é operacionalizar, medir e expandir com segurança.

## Escopo desta rodada

Implemente somente as etapas 1-4:

1. Diagnóstico e inventário real do banco, conectores, jobs, MCP e ambiente.
2. Ativação controlada dos conectores existentes com handshake/dry-run/execução limitada e validação de idempotência.
3. Contrato e painel/API/service inicial de qualidade/cobertura do data warehouse.
4. Planejamento técnico e primeiro incremento seguro de granularidade clínica para endpoints/resultados/safety, preferencialmente com fixtures e testes antes de persistência ampla.

Fora de escopo nesta rodada:

- ANVISA;
- PMC full-text;
- congressos;
- press releases;
- investor decks;
- fontes licenciadas;
- vector DB dedicado;
- OpenSearch;
- API comercial/billing;
- chatbot ou geração final interna de relatórios;
- mudanças amplas de arquitetura.

## Estado atual esperado

Conectores existentes:

- `clinicaltrials_gov`
- `pubmed`
- `openfda`
- `dailymed`
- `open_targets`
- `ema`

Arquivos-chave:

- `backend/workers/celery_app.py`
- `backend/workers/tasks/ingest.py`
- `backend/workers/connectors/`
- `backend/workers/persistence/`
- `backend/app/models/db/`
- `backend/app/mcp/tools/`
- `tools/handshake.py`
- `Makefile`

Ferramentas MCP já existentes:

- `search_drugs`
- `find_trials`
- `compare_assets`
- `get_company_pipeline`
- `get_trial_results`
- `search_publications`
- `get_regulatory_status`
- `build_report_data_bundle`
- `fetch_source_evidence`

## Regras obrigatórias

- Não exponha segredos e não versionar `.env`.
- Não rode ações destrutivas no banco.
- Não apague dados, logs, evidências ou histórico.
- Não faça scraping novo nesta rodada.
- Não permita escrita via MCP por IA Host.
- Não use saída de LLM como fonte primária.
- Não implemente conector novo sem fase Link/handshake e contrato em `docs/03`.
- Toda alteração de schema exige migração Alembic versionada e testes.
- Toda mudança em automação exige atualização de `docs/09_DEPLOY_E_OPERACAO.md`.
- Toda mudança em MCP exige atualização de `docs/04_MCP_TOOLS.md`.
- Ao final, registre progresso em `project_state/progress.md`.

## Etapa 1 - Diagnóstico e inventário real

Primeiro, confirme o estado real do código e do ambiente.

Tarefas:

- verificar quais conectores estão implementados e importáveis;
- verificar quais jobs Celery existem e quais estão no `beat_schedule`;
- verificar quais tabelas/modelos existem;
- verificar quais ferramentas MCP consultam quais tabelas;
- verificar comandos disponíveis no `Makefile`;
- comparar `.env.example` com variáveis usadas por config;
- identificar bloqueios de rede, credenciais, dependências ou migrações;
- se possível, rodar:

```bash
make handshake
cd backend && python -m alembic -c migrations/alembic.ini current
```

Se algum comando falhar por rede/credenciais/dependências, registre o bloqueio claramente.

Entregável:

- diagnóstico registrado em `project_state/progress.md`;
- lista objetiva do que está pronto, bloqueado e pendente.

## Etapa 2 - Ativação controlada dos conectores existentes

Objetivo: validar a ingestão recorrente dos conectores já existentes sem risco operacional.

Tarefas:

- revisar `run_clinicaltrials_ingest`, `run_pubmed_ingest`, `run_openfda_ingest`, `run_dailymed_ingest`, `run_opentargets_ingest`, `run_ema_ingest`;
- confirmar idempotência, retry e tratamento de falha total;
- criar, se ainda não existir, um modo seguro de dry-run ou execução limitada por `max_records`;
- executar apenas quando o ambiente permitir e com limites conservadores;
- validar `IngestionJob`, `SourceDocument`, `EvidenceSnippet` e contadores;
- confirmar que os dados ficam consultáveis por API/MCP.

Cadência alvo a preservar:

- ClinicalTrials.gov: diário 03:00 UTC;
- PubMed: diário 03:15 UTC;
- openFDA: diário 03:30 UTC;
- DailyMed: diário 03:45 UTC;
- Open Targets: semanal segunda 04:00 UTC;
- EMA: semanal segunda 04:15 UTC;
- freshness: diário 02:30 UTC;
- retenção: semanal domingo 04:00 UTC.

Entregável:

- status por conector: pronto, bloqueado, precisa ajuste, executado com sucesso;
- registros em `project_state/progress.md`;
- docs atualizados se houver mudança operacional.

## Etapa 3 - Cobertura e qualidade do data warehouse

Objetivo: criar a primeira camada mensurável de qualidade/cobertura. Implemente preferencialmente um service/API simples antes de UI complexa.

Métricas mínimas:

- total de `drug_assets`;
- total de `clinical_trials`;
- total de `publications`;
- total de `regulatory_approvals`;
- total de `targets`;
- total de `source_documents`;
- total de `evidence_snippets`;
- total de `ingestion_jobs`;
- total de conflitos abertos;
- última ingestão bem-sucedida por `data_source`;
- registros com e sem evidência quando mensurável;
- fontes stale ou sem execução recente.

Possíveis nomes:

- `WarehouseCoverageService`
- endpoint interno `GET /api/v1/warehouse/coverage`
- testes `test_warehouse_coverage_service.py` e/ou `test_warehouse_coverage_route.py`

Critérios:

- SQL parametrizado;
- paginação/limites quando aplicável;
- rota protegida como demais rotas internas;
- resposta clara para dashboard e agente;
- sem expor payloads brutos ou segredos.

## Etapa 4 - Granularidade clínica inicial

Objetivo: iniciar, com segurança, a camada que mais aumenta valor analítico: endpoints, resultados e safety.

Nesta rodada, priorize análise, fixtures e primeiro incremento pequeno. Não tente resolver tudo.

Tarefas:

- analisar se o parser ClinicalTrials.gov já captura `resultsSection` e como;
- identificar modelos `Endpoint`, `TrialResult` e `AdverseEvent`;
- verificar `get_trial_results` e suas lacunas atuais;
- selecionar fixtures pequenas de `resultsSection` ou registros mockados;
- implementar parser/normalizer ou plano de persistência mínimo para endpoint primário/secundário, braço, população, timepoint, medida, valor e adverse event quando disponível;
- criar testes primeiro ou junto com a implementação;
- garantir evidência por campo crítico;
- manter dados negativos/inconclusivos, sem filtragem silenciosa.

Critérios:

- não persistir inferência sem evidência;
- não sobrescrever dados canônicos sem `PersistenceDecisionEngine`/assertions quando aplicável;
- `get_trial_results` deve retornar dados reais quando existirem ou gaps claros quando não existirem;
- mudanças devem ser pequenas, reversíveis e cobertas por testes.

## Validação esperada

Execute conforme o ambiente permitir:

```bash
make handshake
make release-check
cd backend && pytest tests/unit tests/integration -v --tb=short
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm run build
```

Se algum comando não puder rodar, explique por quê no registro final.

## Saída final esperada

Ao finalizar, entregue:

1. resumo do que foi implementado;
2. arquivos alterados;
3. comandos executados e resultados;
4. bloqueios;
5. riscos remanescentes;
6. próximo passo recomendado.

Atualize obrigatoriamente:

- `project_state/progress.md`;
- `project_state/task_plan.md` se houver mudança de status;
- `docs/11_CHANGELOG_DECISOES.md` se houver decisão relevante;
- docs de área quando alterar comportamento.
