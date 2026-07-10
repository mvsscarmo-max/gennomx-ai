# project_state / findings.md — GennomX AI

## Achados operacionais da ingestão recorrente — 2026-07-09

| Apontamento | Parecer interno | Tratamento |
|---|---|---|
| `docker compose config` interpolou `.env` local e expôs segredos reais no stdout (tokens MCP, `SUPABASE_SERVICE_ROLE_KEY`, `NCBI_API_KEY`) | Procedente, médio (segurança operacional) | Valores não registrados em arquivo; output do terminal tratado como sensível. Recomendação registrada em `docs/09` e aqui: preferir `docker compose config --no-interpolate` ou validar por teste unitário (`test_postgres_vps_artifacts.py`). Avaliar rotação das chaves expostas no terminal antes de produção |
| Host `gennomx-ai-postgres-ready-postgres-1` resolve na rede `gennomx-ai-postgres-ready-private` (probe efêmero confirmou 172.16.4.2) | Procedente, baixo | Confirma que o app compose pode acessar o Postgres pela rede externa; probe removido |
| VPS tem somente Postgres + Traefik; não há backend/worker/Redis deployados | Procedente, informação | `infra/docker-compose.vps-app.yml` criado para deploy da aplicação; exige copiar o código para a VPS e `.env` staging |
| Banco origem Supabase e alvo VPS estão em paridade funcional de seeds (bootstrap puro, sem ingestão real) | Procedente, baixo | Cutover de dados é trivial; foco é operacionalizar a ingestão contra a VPS |
| 3 tasks de processamento (`link_trials_to_assets`/`deduplicate_assets`/`compute_confidence_scores`) existem mas não estão no `beat_schedule` | Procedente, baixo | Proposta de complemento documentada em `plano_ingestao_fase_operacional.md` fase D; aplicar após primeira ingestão |

---

## Achados operacionais da migração PostgreSQL VPS — 2026-07-09

| Apontamento | Parecer interno | Tratamento |
|---|---|---|
| Projeto Hostinger existente `postgresql-spko` publicava PostgreSQL em `0.0.0.0:32768` e IPv6 | Procedente, alto | Firewall Hostinger `gennomx-ai-vps-public-ingress` criado/ativado/sincronizado permitindo só SSH/HTTP/HTTPS/ICMP; projeto legado removido após aprovação explícita |
| Inventário real Supabase confirma banco bootstrap: apenas `data_sources=8` e `retention_policies=5` têm dados; outras 26 tabelas zero | Procedente, alto impacto na operação | Decisão técnica: `pg_dump --data-only`/`pg_restore` dispensável pois as seeds já são reproduzidas no alvo VPS pelas próprias migrações Alembic 0001/0004 (`ON CONFLICT DO NOTHING`). Nenhuma ingestão real foi executada neste banco. Recomenda-se skipar pg_restore e tratar staging como concluído para dados |
| `alembic_version` divergente: Supabase=0005, VPS=0006 (VPS à frente) | Procedente, baixo | VPS já inclui `llm_call_logs` (0006). Recomendação: opcionalmente aplicar `alembic upgrade head` na origem Supabase antes do cutover para paridade formal; alvo não exige retrabalho |
| `vector` divergente: origem 0.8.0, alvo 0.8.1 | Procedente, baixo | Sem impacto funcional conhecido; alvo usa 0.8.1-pg16 |
| `data_sources` UUIDs aleatórios por migração divergem entre origem e alvo | Procedente, irrelevante | App referencia `data_sources` por `slug`, não por `id`; UUIDs divergentes não afetam o produto |
| Validar aplicação (backend/pytest) contra VPS DB bloqueada nesta sessão | Bloqueio operacional | VPS Postgres em rede Docker interna (`gennomx-ai-postgres-ready-private`) não alcançável desta máquina Windows; exigirá backend em staging on-VPS ou VPN/tunnel |
| Projeto Supabase restaurado para `ACTIVE_HEALTHY` para inventário (estava `INACTIVE`) | Procedente, reversível | Marcus pode repausar o projeto Supabase quando desejar; deixá-lo ativo nesta sessão foi necessário para executar `execute_sql` via MCP |
| Tentativas intermediárias de bootstrap (`gennomx-ai-postgres*`) registraram senhas de tentativa em logs por erro de quoting SQL | Procedente, alto | Senhas tratadas como comprometidas; stack final `gennomx-ai-postgres-ready` usa credenciais novas e bootstrap `Exited (0)`; projetos intermediários removidos após aprovação explícita |
| MCP Supabase não apareceu entre recursos/ferramentas disponíveis nesta sessão | Resolvido na configuração local; pendente nova sessão | Causa isolada: Codex exigia `SUPABASE_ACCESS_TOKEN` apesar de OAuth disponível, e OpenCode usava `mcp-server-supabase` local sem token. Executados `codex mcp login supabase`, remoção de `bearer_token_env_var`, troca do OpenCode para MCP remoto e `opencode mcp auth supabase`. Validação: Codex `auth_status=o_auth`; OpenCode `supabase connected/authenticated`. A sessão atual ainda precisa ser reiniciada para injetar as novas ferramentas. |
| URL direta Supabase local indisponível para inventário/dump | Bloqueio operacional | Host direto `db.qfanrziwepkqkgtvfrdt.supabase.co` falhou DNS; pooler respondeu mas rejeitou role/tenant configurada; não inventar credenciais nem usar `postgres`/`service_role` |
| Aplicar Alembic via Hostinger sem imagem/remote do backend | Resolvido para staging | SQL offline foi compactado/dividido em dois chunks menores que 8192 caracteres e aplicado por projeto temporário na rede interna; alvo validado em `alembic_version=0006` |
| API Hostinger `getProjectContents` retorna variáveis de ambiente sensíveis | Procedente, médio | Valores não foram registrados em docs; tratar respostas/logs dessa API como sensíveis e avaliar rotação antes de produção |

---

## Triagem da revisão técnica sênior — 2026-07-02

| Apontamento | Parecer interno | Tratamento |
|---|---|---|
| `GET /api/v1/overview` inexistente, dashboard sempre com KPIs zerados | Procedente, médio | rota + `OverviewService` implementados (query única) |
| filtro `phase` de ativos ignorado no SQL | Procedente, médio | aplicado em `asset_service.list_assets` (`development_stage`) |
| vocabulário de fase divergente frontend↔backend (`PHASE_1` vs `PHASE1`) | Achado durante A2, procedente | corrigido em `phaseLabel`, dropdown de assets e de trials — também destravou o filtro de fase de trials, que estava igualmente quebrado |
| correções factuais sem segregação de funções (mesmo admin propõe/aprova) | Procedente, médio | `CorrectionService.review` recusa `reviewer == requested_by` (quatro olhos) |
| erros de domínio (`NotFoundError` etc.) sem handler global, viravam 500 | Achado durante A3, procedente, médio | `@app.exception_handler(GennomXError)` em `app/main.py` |
| SSRF por DNS-rebinding no scraper controlado (TOCTOU) | Procedente, baixo/médio (feature inativa) | conexão pinada ao IP validado, `Host`/SNI no hostname original |
| `can_write`/papel `worker` mortos | Procedente, baixo | removidos (nunca usados por rota ou usuário real) |
| `LLMClient` sem ciclo de vida (`httpx.Client` nunca fechado) | Procedente, baixo | `close()` + context manager em `LLMClient`/`LLMService` |
| XXE em `pubmed/connector.py` (`xml.etree.fromstring`) | Procedente, médio (bandit) | `defusedxml.ElementTree.fromstring`; achado colateral: `query_key is None` não checado antes de paginar, corrigido junto |
| 20 erros mypy pré-existentes em 7 arquivos (nunca haviam rodado contra CI real) | Procedente | todos corrigidos na raiz, sem `# type: ignore` |
| repositório sem nenhum commit; CI nunca executado de fato | Procedente, médio (processo) | preparação feita; commit/push adiado por decisão do usuário |

Cobertura de testes desta rodada: `test_overview_service.py`, `test_overview_route.py`,
`test_asset_service.py::test_applies_phase_filter`, `test_correction_service.py`,
`test_corrections_review_route.py`, `test_pin_request_to_address_*` (em
`test_operational_governance.py`), `test_assets_detail_route.py` (mypy — rota sem cobertura
prévia), ajustes em `test_llm_module.py` e `test_auth_dependencies.py`. Suíte completa: 238
testes, 2 skips ambientais (Python 3.14 sem DuckDB/bs4, inalterado desde a rodada anterior).

Pendências desta rodada: primeiro commit/push (A5), validação manual em ambiente rodando.
Detalhe completo em `project_state/task_plan.md` e `docs/11_CHANGELOG_DECISOES.md`
(2026-07-02).

---

## Triagem do parecer técnico externo — 2026-06-21

| Apontamento | Parecer interno | Tratamento |
|---|---|---|
| `_upsert_source_document` sem retorno/escopo inválido | Procedente, crítico | corrigido + teste do fluxo completo |
| job silenciosamente verde com rejeição total | Procedente, crítico | rejeição sistêmica total agora falha a página/job |
| conexão superusuária ignora RLS | Procedente, alto | roles distintos, validação runtime e policies sem papéis privilegiados |
| ausência de teste real de persistência | Procedente, alto | teste `_persist_trials` cobre documento, trial, evidência e assertions |
| `record_limit_reached` fatal | Procedente, médio | limite normal passa a conclusão parcial sem retry |
| SSR com chave admin/cache compartilhado | Procedente, médio | cliente server usa JWT da sessão e `no-store`; chave só em E2E não produtivo |
| auth MCP morta/comparação `==` | Procedente, baixo | código morto removido; `compare_digest`; chave interna virou role `service` |
| event loops duplicados | Procedente, baixo | boundary único `run_coroutine(asyncio.run)` |
| dedup/confidence não implementados | Procedente | tarefas determinísticas implementadas, sem LLM/merge fuzzy automático |
| caches/build presentes | Não é defeito por si | padrões confirmados no `.gitignore`; não versionar artefatos |
| Python 3.14 local | Procedente como ambiente | projeto continua suportando 3.11–3.13; gates oficiais não usam 3.14 |
| ausência de fluxo HTTP MCP integrado | Procedente, médio | contrato percorre auth, dispatch, auditoria e commit no endpoint real |

O passo 11 de seleção de modelos LLM continua adiado. Nenhuma correção desta rodada depende de
modelo generativo.

**Descobertas, limitações, hipóteses e decisões técnicas em aberto.** Extraído de `docs/08_ROADMAP.md` (§20–21) e `docs/11_CHANGELOG_DECISOES.md`.

---

## Decisões técnicas em aberto

| Tema | Recomendação atual | Referência |
|---|---|---|
| Supabase Cloud vs self-host | Cloud para o MVP (velocidade, menor carga operacional) | `docs/08` §20.1 |
| FastAPI vs Next API routes | FastAPI para backend/API/MCP; Next.js só frontend | `docs/08` §20.2 |
| PostgreSQL FTS vs OpenSearch | Começar com PostgreSQL FTS; migrar se busca ficar central/lenta | `docs/08` §20.3 |
| pgvector vs vector DB dedicado | pgvector no MVP; reavaliar se embeddings crescerem | `docs/08` §20.4 |
| Scraping próprio vs serviços | Scrapers próprios controlados para fontes essenciais | `docs/08` §20.5 |
| REST vs GraphQL | REST no MVP | `docs/08` §20.6 |
| Data quality | Checks customizados + Great Expectations/dbt conforme maturidade | `docs/08` §20.7 |
| Framework de segurança | OWASP ASVS / API Top 10 / WSTG adaptados ao MVP interno | `docs/08` §20.9 |

---

## Limitações e riscos conhecidos

- **Conectores futuros:** o contrato VLAEG/healthcheck existe; cada nova fonte ainda exige handshake,
  fixture, política de granularidade e teste de contrato antes da ativação.
- **Dependências locais incompletas:** Python 3.14 está fora do suporte e não possui DuckDB/bs4;
  container/CI Python 3.12 instala as dependências declaradas e é o gate oficial.
- **Retenção produtiva:** requer bucket Supabase configurado e primeiro dry-run revisado. Falha de
  storage é fail-closed e não executa exclusão.
- **Dados conflitantes entre fontes:** preservar múltiplas versões e registrar `conflicts` em vez de sobrescrever (`docs/00` §9.4, `AGENTS.md` §9).
- **Custo/manutenção de conectores:** APIs e HTML de congressos mudam; exige monitoramento e testes de contrato versionados.
- **Hallucination de LLMs host:** mitigada por ferramentas MCP retornando dados estruturados, evidências e limites explícitos.
- **Dependências:** `npm audit` está limpo após override controlado de PostCSS e Playwright
  corrigido. O backend agora fixa pisos seguros para FastAPI/Starlette, multipart, aiohttp,
  LiteLLM e dotenv; `python-jose` foi removido em favor de PyJWT.

---

## Hipóteses adotadas

Lista completa em `docs/08_ROADMAP.md` §21. Destaques: MVP interno primeiro (API/MCP comercial depois); fontes prioritárias abertas/oficiais; banco/taxonomia em inglês; atualização diária quando a fonte permitir; automação 100% com edição corretiva humana; relatórios finais produzidos por modelos host externos.

---

## Observações da ótica VLAEG (gap analysis)

Detalhe completo em `docs/13_PROTOCOLO_VLAEG.md`. Lacunas priorizadas: contrato de dados por conector/tool (3.1), fase Link (handshake), fase Gatilho (agendamento + declarações de automação), runbook de autocorreção (3.5), `tools/` e `architecture/` (POPs).
