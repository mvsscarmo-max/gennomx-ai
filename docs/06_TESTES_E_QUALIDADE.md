# 06 — Testes Automáticos e Qualidade

## Cobertura de governança operacional — 2026-06-21

> Estado 2026-07-20: testes de Platform Auth validam RS256 e rejeitam audience, tenant, app,
> kind e scope incorretos. Testes também provam que sessão administrativa não substitui token MCP.
> DRY-7 usa fixtures com resultados, valores negativos/inconclusivos, adverse events e trial sem
> resultados; a persistência é reexecutada para provar idempotência.

Há testes para granularidade/freshness, falha fechada de política, staging de duplicatas, merge
parcial não destrutivo, assertion governada, correção com supersession, sanitização/allowlist de
scraping, contrato da migração `0004` e ordem arquivo→legal hold→exclusão. O resultado consolidado
fica em `project_state/PROGRESS.md`.

## Regressões adicionadas após revisão externa — 2026-06-21

O teste `test_clinicaltrials_persistence_flow.py` percorre o caminho real
`_persist_trials → SourceDocument → ClinicalTrial → EvidenceSnippet → FieldAssertion` e exige
`records_inserted > 0`. Também prova que falha sistêmica em todos os registros não produz sucesso
silencioso. Foram adicionados testes para limite de lote não fatal, roles PostgreSQL sem bypass de
RLS, chave interna sem privilégio admin, decisão temporal, staging/quality gates e migração `0003`.

O gate oficial permanece em Python 3.11/3.12 (suporte declarado `<3.14`). Execuções locais em
Python 3.14 são apenas diagnósticas e não substituem CI.

## Gate de governança temporal — 2026-06-20

Mudanças de ingestão devem testar obrigatoriamente: reexecução idempotente, payload fora de ordem,
mesmo hash, fonte concorrente, ausência de evidência, transição temporal, rollback de migração,
reprocessamento com versão de regra e preservação da assertion anterior. Quality gates mínimos:
chave natural válida, enrollment não negativo, datas plausíveis e structured data serializável.

O conjunto inicial cobre o `PersistenceDecisionEngine`, hashing canônico, staging/deduplicação em
DuckDB e presença das estruturas da migração `0003`. Conectores futuros devem reutilizar esses
testes e acrescentar invariantes específicas do domínio.

## Registro fase 4 — 2026-06-20

Ruff passou e 73 testes unitários passaram. Foram adicionados contratos para readiness fail-closed,
migração UUID/FK/check/RLS, rollback e sincronização trial↔ativo. A geração SQL offline de upgrade
`0001→0002` e downgrade foi aprovada. `docker compose config --quiet` passou; o sandbox apenas
negou leitura do config global do Docker. Migração PostgreSQL real permanece no gate de CI.

```bash
python -m ruff check app workers tests migrations
python -m pytest tests/unit -q
python -m alembic -c migrations/alembic.ini upgrade head --sql
python -m alembic -c migrations/alembic.ini downgrade 0002:0001 --sql
docker compose --env-file .env.example -f infra/docker-compose.yml config --quiet
```

## Registro fase 3 de ingestão — 2026-06-20

Foram adicionados testes de paginação por página, fusível de volume, caminho raw sanitizado,
evidência literal de trial/ativo e atualização do estado da fonte. Ruff passou e os 64 testes
unitários passaram. O único aviso foi a limitação local conhecida do `.pytest_cache` em caminho
Windows com caracteres acentuados.

```bash
python -m ruff check app/config.py workers/connectors/clinicaltrials workers/tasks/ingest.py workers/base/job_tracker.py workers/storage tests/unit
python -m pytest tests/unit/test_clinicaltrials_ingestion_resilience.py tests/unit/test_job_tracker.py tests/unit/test_clinicaltrials_asset_linking.py -q
python -m pytest tests/unit -q
```

## Registro fase 2 MCP — 2026-06-20

Adicionados testes unitários de permissão/negação por escopo e do limite do índice de entidades auditadas. Os testes anteriores cobrem autenticação, rate limit local, blocklist e injeção da sessão. Em 2026-06-20, `python -m pytest tests/unit/test_mcp_server.py -q` passou com 11 testes e Ruff passou sem achados nos arquivos MCP/config/teste. O gate final executará contrato `tools/list`/`tools/call` em ambiente isolado instalado com o extra `.[mcp]`.

## Gate de remediação do parecer externo — 2026-06-21

O teste `tests/integration/test_mcp_http_flow.py` atravessa o adaptador HTTP real do MCP desde o
token até autorização, validação do payload, despacho da ferramenta, auditoria e commit. Os testes
de ingestão cobrem INSERT, UPDATE, NOOP e falha sistêmica total; os de segurança cobrem role
inesperado, superuser e `BYPASSRLS`. Resultado local consolidado: 104 aprovados e 1 skip apenas
porque DuckDB não está instalado no Python 3.14 local, versão fora do intervalo suportado pelo
projeto. Ruff, ESLint, TypeScript, build Next e geração SQL Alembic offline também passaram.

Este documento reúne a estratégia de testes automáticos, qualidade de dados, CI/CD e gates mínimos de release.

---

# 14. Estratégia de testes automáticos

## 14.1 Princípio geral

A GennomX AI deve ser construída com uma estratégia de testes automáticos desde o MVP. O objetivo é reduzir risco de:

- quebra de conectores;
- ingestão incorreta;
- dados duplicados;
- resultados clínicos mal extraídos;
- vazamento de dados;
- falhas de permissões;
- regressões no dashboard;
- ferramentas MCP retornando dados errados;
- deploys instáveis.

## 14.2 Pirâmide de testes recomendada

### Base: testes unitários

Cobrem:

- parsers;
- normalizadores;
- deduplicadores;
- validadores;
- formatadores;
- funções de score;
- builders de resposta MCP;
- validação de argumentos;
- regras de segurança.

### Meio: testes de integração

Cobrem:

- conector + raw storage;
- parser + banco;
- API + banco;
- MCP + API/banco;
- auth + permissões;
- jobs + logs;
- upload + quarentena + parsing.

### Meio: testes de contrato

Cobrem:

- schemas de APIs externas;
- schemas internos da API;
- contratos MCP;
- payloads de fontes;
- estrutura de bundles.

### Topo: testes end-to-end

Cobrem fluxos completos:

- usuário faz login;
- pesquisa ativo;
- abre página de ativo;
- visualiza trials;
- consulta evidência;
- executa bundle;
- verifica logs;
- edita dado incorreto;
- reprocessa entidade.

## 14.3 Testes por módulo

### Conectores

- teste de autenticação da fonte;
- teste de endpoint disponível;
- teste de paginação;
- teste de payload mínimo;
- teste de schema esperado;
- teste de timeout;
- teste de retry;
- teste de idempotência;
- teste de transformação.

### Scrapers

- teste de robots/allowlist;
- teste de bloqueio de domínio não aprovado;
- teste de HTML inesperado;
- teste de parser com fixture;
- teste de rate limit;
- teste de redirecionamento;
- teste de bloqueio de arquivo excessivo;
- teste de sanitização.

### Uploads

- teste de tipo de arquivo;
- teste de tamanho máximo;
- teste de arquivo corrompido;
- teste de nome malicioso;
- teste de macro/arquivo arriscado;
- teste de quarentena;
- teste de hash.

### Normalização

- teste de fase clínica;
- teste de status;
- teste de aliases;
- teste de unidades;
- teste de datas;
- teste de nomes de empresas;
- teste de indicações.

### Deduplicação

- teste de match exato;
- teste de match por ID externo;
- teste de match fuzzy;
- teste de falso positivo;
- teste de falso negativo;
- teste de rollback de merge.

### MCP

- teste de cada ferramenta;
- teste de input inválido;
- teste de limite de resultados;
- teste de autorização;
- teste de token inválido;
- teste de rate limit;
- teste de paginação;
- teste de evidências retornadas;
- teste de ausência de dado;
- teste de logs;
- teste de bloqueio de consulta ampla;
- teste de resposta em schema esperado.

### API

- teste de autenticação;
- teste de autorização;
- teste de paginação;
- teste de validação de payload;
- teste de erros seguros;
- teste de CORS;
- teste de rate limit;
- teste de OpenAPI/contrato.

### Dashboard

- teste de login;
- teste de busca;
- teste de páginas de entidade;
- teste de filtros;
- teste de tabelas;
- teste de edição corretiva;
- teste de logs;
- teste de responsividade;
- teste de estados vazios;
- teste de erro.



## 14A. Testes específicos da stack refinada

### Next.js

- testes de componentes críticos;
- testes e2e com Playwright;
- testes de login, filtros, páginas de entidade, logs e edição corretiva;
- teste para impedir exposição acidental de segredos no bundle.

### FastAPI

- testes de contrato OpenAPI;
- testes de autenticação e autorização;
- testes de paginação, validação e erros seguros;
- testes para garantir que rotas longas criem jobs assíncronos em vez de executar processamento síncrono.

### Celery/Redis

- testes de criação de jobs;
- testes de retry, timeout e falha controlada;
- testes de idempotência;
- testes de logging em `IngestionJob`;
- testes de execução concorrente sem duplicação indevida.

### DuckDB

- testes de transformação batch com fixtures;
- testes com arquivos grandes simulados;
- testes de consistência entre resultado DuckDB e persistência PostgreSQL;
- testes de rejeição de arquivos inválidos.

### OPENCODE / LLM interno

- testes de configuração: defaults seguros, produção rejeita LLM habilitado sem chave;
- testes de cliente HTTP mockado: montagem de request, timeout, provider error, sanitização;
- testes de schema: JSON válido aceito, JSON inválido rejeitado;
- testes de serviço: proibição de métodos de escrita direta no banco;
- testes de prompt injection: texto externo malicioso não altera instrução do sistema;
- testes de metadata: hashes sem conteúdo sensível, logs sem segredos;
- handshake LLM com dry-run e mock para CI.


## 14.4 Testes de qualidade de dados

Devem validar:

- campos obrigatórios;
- unicidade de IDs;
- integridade referencial;
- formatos de data;
- ranges plausíveis;
- fases permitidas;
- status permitidos;
- endpoints sem resultado;
- resultados sem evidência;
- evidência sem documento;
- trials sem sponsor;
- ativos sem alias principal;
- entidades duplicadas;
- queda abrupta de volume por fonte;
- aumento anômalo de registros rejeitados.

## 14.5 Testes de segurança

Automatizar:

- SAST;
- dependency scanning;
- secret scanning;
- IaC scanning;
- container scanning;
- testes de headers;
- testes básicos de DAST;
- testes de autorização negativa;
- testes de RLS;
- testes de rate limit;
- testes contra payloads de XSS;
- testes contra SQL injection;
- testes contra SSRF em scrapers;
- testes de upload malicioso;
- testes de exposição de stack trace.

## 14.6 Testes de regressão de conectores

Cada conector deve ter fixtures versionadas com payloads reais ou representativos.

Quando uma fonte externa mudar:

- teste de contrato deve falhar;
- alerta deve ser gerado;
- ingestão deve ser pausada ou marcada como degraded;
- dados antigos devem permanecer disponíveis;
- correção deve ser validada com fixture nova.

## 14.7 Testes de performance

Validar:

- tempo de busca global;
- tempo de página de ativo;
- tempo de ferramentas MCP;
- ingestão por lote;
- consulta com filtros;
- geração de bundles;
- latência de API;
- tempo de indexação;
- comportamento sob concorrência.

Critérios iniciais sugeridos:

- busca global simples abaixo de 2 segundos no MVP;
- ferramenta MCP comum abaixo de 5 segundos para consultas limitadas;
- página de ativo abaixo de 3 segundos para ativos moderados;
- jobs longos assíncronos com progresso/logs;
- nenhuma ferramenta MCP sem limite.

## 14.8 Testes de aceitação

Antes de considerar o MVP funcional:

- carregar ao menos um conjunto representativo por fonte prioritária;
- buscar ativos por nome, indicação e target;
- abrir página de ativo com trials e evidências;
- consultar MCP com ferramenta `search_drugs`;
- consultar MCP com ferramenta `find_trials`;
- gerar bundle externo de asset profile;
- visualizar logs;
- corrigir um dado manualmente;
- verificar versionamento;
- recuperar evidência de um resultado;
- passar testes críticos de segurança.

## 14.9 Ferramentas sugeridas para testes

Recomendação inicial:

- pytest para backend Python;
- Playwright para end-to-end web;
- Schemathesis ou equivalente para testes OpenAPI;
- Great Expectations, Soda ou dbt tests para qualidade de dados;
- Ruff/mypy ou equivalentes para qualidade estática Python;
- Bandit/Semgrep para SAST;
- Trivy ou equivalente para containers/dependências;
- GitHub Actions ou GitLab CI para CI/CD;
- PostgreSQL local/staging para testes de banco;
- fixtures versionadas para conectores.

A escolha final pode variar conforme stack definitiva.

---

# 15. CI/CD, ambientes e gates de release

## 15.1 Ambientes

Recomenda-se:

- **local**: desenvolvimento;
- **test**: execução automática de testes;
- **staging**: ambiente semelhante ao production;
- **production**: ambiente estável;
- **sandbox MCP**: ambiente para testes de ferramentas por modelos host.

## 15.2 Gates mínimos antes de deploy

Nenhum deploy para produção deve ocorrer se falharem:

- testes unitários críticos;
- testes de integração essenciais;
- testes MCP essenciais;
- testes de migração de banco;
- secret scanning;
- dependency scanning crítico;
- lint/type checks mínimos;
- build do frontend;
- testes end-to-end essenciais;
- testes de segurança de autorização.

## 15.2.1 Estado implementado em 2026-06-12

Atualizações aplicadas:

- adicionado teste unitário para garantir que o dispatcher MCP repassa a sessão de banco injetada pelo FastAPI;
- adicionados testes unitários para `SourceService.list_jobs()` e `SourceService.get_job_detail()`;
- adicionados testes unitários para `JobTracker.create_job()` e serialização JSON de `JobTracker.complete_job()`;
- adicionados testes unitários para linking ClinicalTrials.gov→DrugAsset, incluindo filtragem de intervenções terapêuticas, merge de aliases/indicações/sponsors, escolha de fase mais avançada e backfill de `drug_asset_ids`;
- `frontend/package-lock.json` foi gerado e o CI voltou a usar `npm ci`;
- `npm run lint`, `npm run typecheck` e `npm run build` passam no frontend;
- `py -m ruff check .` e `py -m pytest tests -q` passam no backend;
- `pyproject.toml` foi corrigido para usar `setuptools.build_meta:__legacy__`, permitindo instalação editável do backend.

Pendência recomendada:

- `npm audit` ainda reporta 2 vulnerabilidades moderadas relacionadas ao `postcss` embutido em `next@15.5.18`; `npm audit fix --force` recomenda caminho quebrável/major e não foi aplicado.
- Migrar futuramente para Next 16 quando a aplicação estiver pronta para a mudança maior.

Validação adicional em 2026-06-12:

- `py -m ruff format .`
- `py -m ruff check .`
- `py -m pytest tests -q` — 50 testes passando no backend.

## 15.3 Estratégia de migração

- migrações versionadas;
- rollback planejado;
- backup antes de migração crítica;
- testes de migração em staging;
- validação de dados após migração;
- não apagar colunas críticas sem fase de depreciação.

## 15.4 Estratégia de releases

MVP interno:

- releases frequentes;
- changelog simples;
- validação manual final;
- monitoramento pós-deploy.

Futuro comercial:

- versionamento semântico;
- release notes;
- feature flags;
- canary deploy;
- rollback automático;
- SLAs internos.

## 15.5 Gate consolidado da Fase 5 — 2026-06-20

Gates locais aprovados:

- backend: Ruff e 78 testes unitários;
- frontend: ESLint, TypeScript e build de produção Next.js;
- dashboard: 7 cenários Playwright em Chromium (seis telas e busca de empresas);
- dependências frontend: `npm audit --audit-level=moderate` sem vulnerabilidades;
- dependências backend declaradas: `pip-audit .` sem vulnerabilidades conhecidas;
- SAST backend: Bandit sem achados após exclusão documentada apenas de B608;
- tipagem backend: mypy sem erros.

A regra B608 é excluída porque o projeto compõe somente fragmentos internos de predicados e
colunas; todos os valores externos continuam parametrizados. Ruff mantém S608 na allowlist
revisada pelo mesmo motivo. Demais regras do Bandit são bloqueantes.

O CI agora executa E2E com Chromium, npm audit, mypy, pip-audit e Bandit como gates reais,
sem `continue-on-error`. Migração real e testes de integração continuam dependentes dos
serviços PostgreSQL/Redis do GitHub Actions.

---
