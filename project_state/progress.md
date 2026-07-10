## Operacionalizacao da ingestao — cutover VPS autorizado + plano + compose de deploy da aplicacao — 2026-07-09

Marcus autorizou o cutover para fins de ingestao/operacionalizacao do data warehouse: a ingestao deve acontecer contra o PostgreSQL da VPS (`gennomx-ai-postgres-ready`), nao mais contra a Supabase. Supabase Auth/JWKS e Supabase Storage permanecem ativos nesta fase.

Executado nesta rodada:

- Lida a ordem obrigatoria: `AGENTS.md`, `task_plan.md`, `findings.md`, `progress.md`, `docs/00/01/02/03/04/08/09`, `fontes_priorizacao.xlsx` (nao localizada nesta maquina — segui `docs/03` §4 como premissa viva), `backend/workers/celery_app.py`, `backend/workers/tasks/ingest.py`, `backend/workers/tasks/process.py`, `backend/workers/storage/raw_payload.py`, `tools/handshake.py`, `infra/`, `Makefile`, `backend/Dockerfile`.
- Diagnostico do estado real do codigo confirmado (nao suposicao):
  - 6 conectores implementados, registrados em `tools/handshake.py` e com `healthcheck()`: `clinicaltrials_gov`, `pubmed`, `openfda`, `dailymed`, `open_targets`, `ema`.
  - 6 tasks Celery em `workers/tasks/ingest.py` (um por conector), cada uma com `max_retries=3`, backoff exponencial, `JobTracker`, validacao de role `gennomx_worker` em producao, falha sistêmica total faz o job falhar (nao verde com zero inserts).
  - `beat_schedule` em `celery_app.py` ja agenda 6 jobs de ingestao (4 diarios + 2 semanais) + `governance-freshness-daily` + `governance-retention-weekly`. Tasks de processamento `link_trials_to_assets`/`deduplicate_assets`/`compute_confidence_scores` existem mas nao estao agendadas (candidatas a complemento pos-dados).
  - `store_raw_payload` (Supabase Storage, imutavel por hash) esta wired nos 6 conectores via modulos de persistencia; S3 falha fechado por design.
  - Banco origem Supabase: bootstrap puro (8 `data_sources` inactive, 5 `retention_policies`, demais 26 tabelas zero) — nenhuma ingestao real foi executada neste banco em nenhum momento. Alvo VPS em `alembic_version=0006` com seeds equivalentes.
  - Entidades com ingestao funcional hoje: `DrugAsset` (CT.gov), `ClinicalTrial`, `clinical_trial_assets`, `Target`, `RegulatoryApproval`, `Publication`, `SourceDocument`, `EvidenceSnippet`, `FieldAssertion`, `DataConflict`, `IngestionJob`. Lacunas P1: `endpoints`, `trial_results`, `adverse_events` (parser granular CT.gov resultsSection nao implementado); `companies` (sponsors sao strings); `indications` (conditions sao strings); `MechanismOfAction` (sem conector); ANVISA (nao implementado).
- Plano operacional produzido em `project_state/plano_ingestao_fase_operacional.md`: diagnostico detalhado, ordem racional de ingestao (Onda 1 = ativar 6 conectores; Onda 2 = lacunas P1; Onda 3 = fontes complexas), camadas raw/processado/curado/current/history sobre o modelo existente, agenda Celery/beat por fonte, pre-requisitos operacionais, backlog priorizado, riscos, criterios de aceite e plano por fases pequenas com comandos e rollback.
- Confirmada a topologia VPS: `1817951` (4 CPU, 16 GB RAM, 200 GB disk) com Postgres healthy em rede interna `gennomx-ai-postgres-ready-private` e Traefik ativo; nao ha backend/worker/Redis deployados.
- Probe de DNS efemero (`gennomx-ai-net-probe`) confirmou que o host `gennomx-ai-postgres-ready-postgres-1` resolve na rede `gennomx-ai-postgres-ready-private` (172.16.4.2); probe removido em seguida.
- Criado `infra/docker-compose.vps-app.yml`: deploy da aplicacao (Redis + worker + beat + API sob profile `api`) na VPS, conectado a `gennomx-ai-postgres-ready-private` (external) para acessar o Postgres e a rede interna `gennomx-ai-app` para Redis/app. Nenhum servico publica portas no host. Worker com `--concurrency=1` (VPS compartilhada). API expoe `8000` apenas internamente (Traefik roteia depois). Build via `backend/Dockerfile` (contexto `../backend`).
- Teste unitario estendido em `backend/tests/unit/test_postgres_vps_artifacts.py`: trava contratos do novo compose (sem `ports`, rede externa do Postgres, rede interna app, `--concurrency=1` no worker, `beat` command, API sob profile `api`). Validado.
- `.env.example` complementado com as URLs VPS de DB (host `gennomx-ai-postgres-ready-postgres-1:5432`) e Redis interno (sem TLS em staging; com TLS exigido em production) e nota de que a primeira rodada deve usar `ENVIRONMENT=staging`.
- `docs/09_DEPLOY_E_OPERACAO.md` atualizado com runbook completo de deploy da aplicacao na VPS: artefatos, pre-requisitos, comandos passo a passo (env, alembic current, handshake, up redis+worker+beat, smoke-run incremental controlado, validar, opcional API), concorrencia/limites, rollback e nota de seguranca sobre `docker compose config` expondo segredos.

Nao executado nesta sessao (exige ambiente com rede de saida + VPS acessivel por SSH + Redis/Supabase validados on-VPS):

- Deploy efetivo do compose na VPS (precisa do codigo copiado para a VPS + `.env` real).
- Handshake real contra as 6 fontes (gate de pre-ativacao).
- Smoke-run incremental controlado por conector.
- Ativacao do beat recorrente.
- Validacao de `/ready`, MCP e dashboard contra a VPS.
- Cutover produtivo com `ENVIRONMENT=production` (exige `rediss://` e demais validacoes de `config.py`).
- Complementos ao `beat_schedule` (link_trials/dedup/confidence) — pos-primeira-ingestao.

Risco operacional registrado:

- `docker compose config` interpolou o `.env` local desta maquina e expôs segredos reais (tokens MCP, `SUPABASE_SERVICE_ROLE_KEY`, `NCBI_API_KEY`) no stdout do comando de validacao de sintaxe. Esses valores NAO foram registrados em nenhum arquivo; o output do terminal foi tratado como sensivel. registrado em `findings.md` e `docs/09` como alerta operacional: preferir `docker compose config --no-interpolate` ou validacao por teste unitario.

Estado final desta rodada:

- Plano operacional documentado e合约 dos artefatos de deploy travados por teste.
- Pronto para o Marcus executar o runbook na VPS (copiar codigo, preencher `.env` staging, handshake, smoke-run, up beat).
- Nenhuma ingestao foi executada; nenhum cutover produtivo sem validacao on-VPS.

---

## Migracao banco-only Supabase PostgreSQL -> PostgreSQL VPS - inventario real via MCP Supabase - 2026-07-09

Executado nesta rodada:

- Verificada a disponibilidade do MCP Supabase nesta sessao: `supabase_list_projects` respondeu e listou o projeto GennomX AI (`qfanrziwepkqkgtvfrdt`, regiao `us-west-2`) inicialmente em status `INACTIVE` (pausado por decisao anterior do Marcus).
- Restaurado o projeto Supabase (`supabase_restore_project`) e aguardada a transicao -> status `ACTIVE_HEALTHY`. Esta e uma acao reversivel; o projeto permanece ativo nesta sessao para permitir inventario/consulta. Marcus pode pausa-lo novamente quando desejar.
- Coletado inventario real do Supabase via MCP `execute_sql` (read-only). Resumo seguro (sem credenciais, sem valores sensiveis):

  - PostgreSQL `17.6` (x86_64-pc-linux-gnu, gcc 15.2.0).
  - Banco: 12 MB.
  - `alembic_version = 0005` na origem (alvo VPS staging ja em `0006`).
  - Extensao `vector=0.8.0` na origem (alvo VPS staging em `0.8.1`); demais extensoes compativeis (`pg_trgm=1.6`, `pgcrypto=1.3`, `uuid-ossp=1.1`) + adicionais Supabase (`pg_stat_statements=1.11`, `supabase_vault=0.3.1`, `plpgsql=1.0`).
  - Schemas Supabase-specific a NAO migrar: `auth`, `graphql`, `graphql_public`, `realtime`, `storage`, `vault`, `extensions`. Apenas `public` pertence a aplicacao.
  - Roles Supabase-specific a NAO migrar: `anon`, `authenticated`, `service_role` (bypassrls), `supabase_admin` (superuser/bypassrls), `supabase_auth_admin`, `supabase_storage_admin`. A migracao usa apenas `gennomx_app`, `gennomx_worker`, `gennomx_migrator`, `gennomx_readonly` (todas com `rolsuper=false`, `rolbypassrls=false`, credenciais proprias na VPS).
  - 28 tabelas publicas na origem: `adverse_events`, `alembic_version`, `archive_items`, `archive_manifests`, `clinical_trial_asset_history`, `clinical_trial_assets`, `clinical_trials`, `companies`, `data_conflicts`, `data_sources`, `drug_assets`, `endpoints`, `evidence_snippets`, `field_assertions`, `indications`, `ingestion_jobs`, `legal_holds`, `manual_corrections`, `mcp_query_logs`, `publications`, `regulatory_approvals`, `retention_policies`, `scraper_access_events`, `scraper_domain_policies`, `security_events`, `source_documents`, `targets`, `trial_results`. Alvo VPS em `0006`tem 29 (adiciona `llm_call_logs` da migracao `0006`).
  - RLS/policies: 27 tabelas com RLS, 60 policies — identicas em numero ao alvo VPS staging.
  - Contagens criticas (origem Supabase):
    - `data_sources = 8` (clinicaltrials_gov, pubmed_pmc, openfda, dailymed, ema, open_targets, anvisa, pubmed) — todas com `connector_status=inactive`, `is_enabled=false`, `last_successful_run=NULL`, `last_failed_run=NULL`. Nenhuma ingestao real foi executada neste banco.
    - `retention_policies = 5` (field_assertions, source_documents, ingestion_jobs, mcp_query_logs, security_events).
    - Todas as demais 26 tabelas de entidades/eventos = 0 registros (incluindo `drug_assets`, `companies`, `clinical_trials`, `clinical_trial_assets`, `indications`, `targets`, `endpoints`, `trial_results`, `adverse_events`, `regulatory_approvals`, `publications`, `source_documents`, `evidence_snippets`, `field_assertions`, `data_conflicts`, `manual_corrections`, `ingestion_jobs`, `mcp_query_logs`, `security_events`, `legal_holds`, `archive_items`, `archive_manifests`, `clinical_trial_asset_history`, `scraper_domain_policies`, `scraper_access_events`).
  - Divergencias relevantes: `alembic_version` (origem 0005 < alvo 0006), `vector` (0.8.0 < 0.8.1), `llm_call_logs` ausente na origem (criada por `0006`) — todas em favor do alvo, nenhuma exige retrabalho no sentido contrario.

- Achado critico: o banco Supabase contem apenas dados de seed/config — `data_sources` (8) e `retention_policies` (5), sendo ambos ja semeados pelas proprias migracoes Alembic `0001` e `0004` (com `ON CONFLICT DO NOTHING`). As migracoes `0005` e `0006` nao adicionam dados. Nenhuma ingestao real foi executada neste banco em nenhum momento (todos `last_successful_run`/`last_failed_run` sao NULL). Em consequencia, o alvo VPS staging em `alembic_version=0006` ja contem funcionalmente o mesmo estado de dados que a origem, pois as seeds de data_sources/retention_policies sao deterministas em `slug`/`resource_type` (apenas os UUIDs gerados por `gen_random_uuid()` diferem em cada execucao da migracao, o que e irrelevante operacionalmente porque data_sources sao referenciados por `slug`).

Observacoes:

- Nao houve gravacao de `supabase-inventory.json` em arquivo; o inventario foi coletado em memoria para registro sumarizado em `progress.md`. Nenhum valor sensivel foi persistido.
- O projeto Supabase permanece `ACTIVE_HEALTHY` ao final desta sessao (poderia ser pausado novamente; decisao do Marcus).
- VPS Hostinger `1817951` continuou valida nesta rodada: `gennomx-ai-postgres-ready` em `running`/healthy (postgres Up 2h), bootstrap e certs `Exited (0)`, porta `5432` apenas `exposed` (sem `host_port`); firewall `gennomx-ai-vps-public-ingress` (`325948`) `is_synced=true` concedendo apenas SSH/22, HTTP/80, HTTPS/443 e ICMP. Traefik segue como segundo projeto ativo.

Decisao tecnica decorrente — dump/restore staging dispensavel:

- O caminho `pg_dump --data-only`/`pg_restore` descrito em `plano_migracao_supabase_postgres_vps.md` fica dispensavel na fase staging porque o volumen de dados a migrar e trivial e correspondente a seeds ja replicados no alvo pelas proprias migracoes. Persistir em `pg_dump --data-only` acrescentaria risco operacional (manipular URLs direta Supabase com DNS falho localmente e expor credenciais) sem beneficio.
- Recomenda-se, no cutover produtivo, validar apenas: (a) VPS staging com as seeds de `data_sources`/`retention_policies` confirmadas; (b) `alembic_version=0006` no alvo; (c) nenhuma ingestao iniciada antes do cutover. Em paralelo, antes do cutover, aplicar `alembic upgrade head` na origem Supabase (`0006`) para paridade formal e optionally pausar Supabase DB apos backup final.
- Como nao houve restore de dados nesta sessao, `tools/compare_postgres_migration.py` nao foi executado; a comparacao e conceitual: origem e alvo tem as mesmas seeds funcionais (via migracoes), demais tabelas vazias em ambos, e o alvo ja esta a frente em schema (0006 com `llm_call_logs`). Limitacao: UUIDs de `data_sources` diferem entre origem e alvo (aleatorio por execucao da migracao); nao impacta o produto porque o app referencia por `slug`.

Bloqueio remanescente / limitacoes:

- Validacao de aplicacao (`backend` apontando para VPS DB, `alembic current`, pytest): nao executada nesta sessao porque o PostgreSQL da VPS esta em rede Docker interna (`gennomx-ai-postgres-ready-private`) e nao e alcancavel a partir desta maquina Windows sem tunnel/VPN nem credenciais locais. Para validar a aplicacao contra o VPS DB sera necessario subir backend/worker em staging na propria VPS (ou estabelecer tunnel/VPN) — etapa que dependera de deploy adicional.
- Cutover produtivo permanece nao executado por restricao do Marcus (aprovar explicitamente).
- Inspecionar `VPS_getProjectContentsV1` para obter credenciais do postgres e evitado por seguranca; para validacao independente do alvo recomenda-se aplicar-se posteriormente on-VPS via `gennomx_migrator`/`gennomx_readonly` em janela controlada.

Plano de cutover (apenas documentado, nao executar nesta sessao):

1. Pausar Celery beat e qualquer ingestao recorrente.
2. Fazer backup final Supabase (snapshot do projeto).
3. Confirmar alvo VPS em `alembic_version=0006`, seeds de `data_sources`/`retention_policies` presentes, `llm_call_logs` existente (vazio).
4. (Opcional, recomendado) Aplicar `alembic upgrade head` na origem Supabase (`0006`) para paridade formal antes do corte definitivo; snapshot/backup apos.
5. Trocar secrets/env de API/worker/Alembic para `DATABASE_PROVIDER=vps_postgres`, `DATABASE_URL`/`WORKER_DATABASE_URL`/`DATABASE_URL_SYNC` apontando para `gennomx-ai-postgres:5432` na rede Docker privada, mantendo `SUPABASE_URL`/JWKS/Storage e `NEXT_PUBLIC_SUPABASE_URL`/`NEXT_PUBLIC_SUPABASE_ANON_KEY` inalterados.
6. Subir API/worker/beat.
7. Validar `/ready`, login Supabase, dashboard e MCP autenticado; confirmar raw payload ainda indo para Supabase Storage.
8. Reativar ingestao recorrente com limites conservadores.
9. Monitorar por 24-72h.

Plano de rollback (apenas documentado, nao executar):

1. Pausar API/worker/beat.
2. Reapontar `DATABASE_PROVIDER=supabase_postgres` e `DATABASE_URL`/`WORKER_DATABASE_URL`/`DATABASE_URL_SYNC` para Supabase (DB Supabase permanece intacto; se foi aplicado `0006` na origem, o rollback e trivial porque ambas as bases estao em head).
3. Subir sem processar backlog automaticamente.
4. Validar `/ready`, dashboard e MCP.
5. Registrar divergencias; reconciliar ou descartar deltas escritos na VPS (provavelmente nenhum).

Proximo passo seguro:

- Antes de cutover produtivo, validar aplicacao contra VPS DB em ambiente staging on-VPS (backend na VPS ou tunnel). Ate la, a migracao de dados esta conceitualmente concluida para staging; o cutover e majoritariamente um switch de env/secrets.

---

## Migracao banco-only Supabase PostgreSQL -> PostgreSQL VPS - bloqueio de namespace Supabase - 2026-07-09

Executado nesta rodada:

- Lida a ordem obrigatoria de continuidade da migracao banco-only: `AGENTS.md`, `project_state/task_plan.md`, `project_state/progress.md`, `project_state/findings.md`, `project_state/plano_migracao_supabase_postgres_vps.md`, docs de arquitetura/seguranca/operacao/changelog, `.env.example`, `backend/app/config.py`, artefatos PostgreSQL VPS e scripts de inventario/comparacao.
- Verificada a descoberta de ferramentas MCP da sessao: `tool_search` expos `mcp__hostinger_vps`, `mcp__gennomx_ai` e `mcp__gennomx_studio`, mas nao expos nenhum namespace/ferramenta Supabase para SQL, banco, projetos ou docs.
- Confirmado por CLI local que a configuracao Supabase existe e esta autenticada: `codex mcp list --json` mostra `supabase` habilitado, `transport=streamable_http`, URL remota oficial com `read_only=true&features=database,docs`, sem `bearer_token_env_var`, e `auth_status=o_auth`.
- Como o namespace Supabase nao foi injetado nas ferramentas desta sessao, nao houve caminho seguro para executar inventario real por MCP, nem para consultar versao PostgreSQL, extensoes, schemas, tabelas, policies/RLS, roles/grants, `alembic_version`, contagens ou objetos Supabase-specific.
- Verificada a VPS Hostinger sem chamar `getProjectContents` para evitar exposicao de variaveis sensiveis: `VPS_getProjectListV1` mostra `gennomx-ai-postgres-ready` em execucao, Postgres `Up ... (healthy)`, porta `5432` apenas `exposed` sem `host_port`, e `traefik` como outro projeto ativo.

Nao executado:

- Inventario real Supabase, porque o MCP Supabase ainda nao aparece como ferramenta desta sessao apesar de estar autenticado no CLI.
- `pg_dump`/`pg_restore`, porque nao ha `SUPABASE_DIRECT_URL` funcional/segura disponivel por ferramenta desta sessao e nao se deve contornar com credenciais inadequadas.
- Comparacao origem/alvo, porque nao houve restore.
- Testes de aplicacao contra banco VPS com dados restaurados, porque o restore nao aconteceu.
- Cutover produtivo.

Bloqueio atual:

- Bloqueio de injecao/disponibilidade de ferramentas Supabase na sessao do agente. A configuracao OAuth local parece correta, mas a ferramenta MCP Supabase nao esta disponivel para chamada. Proximo passo seguro e abrir/reiniciar uma nova sessao Codex ja com o MCP Supabase carregado, ou fornecer por canal seguro uma `SUPABASE_DIRECT_URL` funcional para uso com `tools/postgres_inventory.py`.

Plano documentado sem executar:

- Cutover produtivo continua dependente de aprovacao explicita: pausar Celery beat/ingestoes, backup final Supabase, dump final, restore final na VPS, comparacao de contagens/checksums, troca de env/secrets para `DATABASE_PROVIDER=vps_postgres`, subida de API/worker/beat, validacao de `/ready`, dashboard e MCP, reativacao conservadora de ingestao e monitoramento por 24-72h.
- Rollback continua: pausar API/worker/beat, reapontar `DATABASE_PROVIDER=supabase_postgres` e as tres URLs de banco para Supabase, subir sem processar backlog automaticamente, validar `/ready`, dashboard e MCP, registrar divergencias e reconciliar ou descartar deltas escritos na VPS.

---
## MCP Supabase — OAuth corrigido para Codex/OpenCode — 2026-07-09

Investigacao e correcao executadas:

- Confirmado que o MCP Supabase ja estava configurado no Codex, mas preso a `bearer_token_env_var = "SUPABASE_ACCESS_TOKEN"`; a sessao atual nao tinha essa variavel e por isso o namespace Supabase nao aparecia.
- Validado que a chave `sb_secret_...` fornecida nao autentica na Supabase Management API (`401`); ela foi tratada como segredo de projeto, nao como PAT/credencial de MCP, e nao foi registrada em arquivo.
- Confirmado que o host direto `db.qfanrziwepkqkgtvfrdt.supabase.co` continua sem resolver DNS nesta maquina; tambem nao ha `psql` local instalado. Isso segue bloqueando o caminho direto por `SUPABASE_DIRECT_URL` local.
- Executado `codex mcp login supabase` com sucesso via OAuth.
- Removida a exigencia de `SUPABASE_ACCESS_TOKEN` de `C:\Users\marcu\.codex\config.toml`; `codex mcp list --json` agora mostra `supabase` como `auth_status: "o_auth"`, sem `bearer_token_env_var`.
- Corrigido `C:\Users\marcu\.config\opencode\opencode.jsonc`: o MCP Supabase ativo deixou de usar `mcp-server-supabase` local sem token e passou a usar o MCP remoto `https://mcp.supabase.com/mcp?...`.
- Executado `opencode mcp auth supabase` com sucesso via OAuth.
- Validacao final: `opencode mcp auth list` mostra `supabase authenticated`; `opencode mcp list` mostra `supabase connected`; `codex mcp list --json` mostra `supabase` configurado como OAuth.

Limite operacional remanescente:

- A sessao atual do agente nao injeta novas ferramentas MCP dinamicamente apos a autenticacao/configuracao. Para executar o inventario real por namespace Supabase nesta conversa, e necessario reiniciar/abrir uma nova sessao Codex/OpenCode ja com o MCP Supabase carregado. A configuracao local esta corrigida.

Proximo passo seguro:

1. Reiniciar a sessao Codex/OpenCode.
2. Confirmar que a descoberta de ferramentas mostra o namespace Supabase.
3. Executar o inventario real do projeto Supabase via MCP read-only antes de qualquer dump/restore.

---

## Migração banco-only Supabase PostgreSQL -> PostgreSQL VPS — Alembic staging aplicado — 2026-07-09

Executado nesta rodada:

- Confirmada ausência de MCP Supabase nas ferramentas/recursos descobertos; a descoberta mostrou Hostinger VPS/GennomX AI, mas nenhuma ferramenta Supabase para SQL/inventário.
- Tentado inventário Supabase com `.env` local sem imprimir segredos:
  - `DATABASE_URL_SYNC`/host direto `db.qfanrziwepkqkgtvfrdt.supabase.co` falhou DNS (`could not translate host name`);
  - `DATABASE_URL` via pooler respondeu, mas rejeitou a role/tenant configurada (`tenant/user ... not found`);
  - `supabase-inventory.json` não foi mantido, pois não houve inventário válido.
- Inspecionada a stack Hostinger `gennomx-ai-postgres-ready`: Postgres segue `healthy`, `5432` apenas `exposed`, rede interna `gennomx-ai-postgres-ready-private`.
- Gerado Alembic offline local (`upgrade head --sql`), compactado e dividido em dois chunks para caber no limite de 8192 caracteres do `content` da API Hostinger.
- Aplicados os dois chunks por projeto temporário `gennomx-ai-alembic-staging` conectado apenas à rede privada da stack. Resultado: container `Exited (0)` e `alembic_version=0006`.
- Reaplicados grants pós-migration. O bloco geral concluiu antes de uma falha de interpolação no `DO $$`; em seguida foram aplicados diretamente os `GRANT INSERT` de `mcp_query_logs`, `security_events` e `manual_corrections` para `gennomx_app`.
- Validação mínima no alvo VPS staging:
  - `alembic_version=0006`;
  - extensões: `pg_trgm=1.6`, `pgcrypto=1.3`, `uuid-ossp=1.1`, `vector=0.8.1`;
  - roles `gennomx_app`, `gennomx_migrator`, `gennomx_readonly`, `gennomx_worker` com `rolsuper=false` e `rolbypassrls=false`;
  - 27 tabelas com RLS habilitado;
  - 60 policies;
  - 29 tabelas públicas;
  - `data_sources=8`.
- Projetos temporários de migration/grants foram solicitados para remoção. `gennomx-ai-validate-staging` ainda aparecia parado imediatamente após a solicitação da Hostinger e deve ser rechecado/removido se persistir.

Não executado:

- Inventário real Supabase por MCP, porque o MCP Supabase não está disponível.
- Dump/restore Supabase -> VPS, porque não há URL direta Supabase funcional/segura nesta sessão.
- Comparação origem/alvo, porque não houve restore de dados.
- Testes de aplicação contra o VPS DB, porque ainda não há restore de dados nem ambiente backend staging apontado ao alvo.
- Cutover produtivo.

Observação de segurança:

- `VPS_getProjectContentsV1` retorna o bloco `environment` do projeto Hostinger, incluindo valores sensíveis. Nenhum valor foi registrado em docs/progress, mas respostas dessa API e logs/transcrições operacionais que as contenham devem ser tratados como sensíveis. Recomenda-se avaliar rotação antes de produção.

Estado final:

- VPS staging com schema em Alembic `head` (`0006`) e validações mínimas de roles/extensões/RLS aprovadas.
- Migração de dados permanece bloqueada por acesso Supabase.

---

## Migração banco-only Supabase PostgreSQL -> PostgreSQL VPS — limpeza e tentativa de Alembic — 2026-07-09

Execução aprovada dos próximos passos via MCP Hostinger VPS.

Executado:

- Removidos da VPS os projetos intermediários criados durante a correção de bootstrap: `gennomx-ai-postgres`, `gennomx-ai-postgres-secure` e `gennomx-ai-postgres-final`.
- Removido o projeto legado `postgresql-spko`, que publicava PostgreSQL em porta host dinâmica. A listagem final de projetos mostra apenas `gennomx-ai-postgres-ready` e `traefik`.
- Confirmado que `gennomx-ai-postgres-ready` segue `running`, Postgres `healthy`, bootstrap `Exited (0)` e sem porta publicada no host (`5432` apenas `exposed` na rede interna).
- Confirmado que o firewall Hostinger `gennomx-ai-vps-public-ingress` continua sincronizado e associado à VPS.
- Gerado SQL Alembic offline localmente para avaliar aplicação em staging; tamanho aproximado 67 KB, removido ao final da tentativa.

Bloqueios encontrados:

- Supabase MCP ainda não apareceu na sessão atual após a alteração global de configuração. A lista de recursos MCP continuou mostrando apenas Higgsfield; é necessário reiniciar o processo OpenCode para carregar as novas ferramentas Supabase.
- A aplicação de Alembic via job temporário Hostinger não foi concluída: a API Hostinger limita o campo `environment` a 8192 caracteres, impedindo transportar o SQL Alembic compactado como variável de ambiente. Como não há remoto Git configurado nem imagem publicada do backend, não há neste momento um caminho limpo/reprodutível para rodar `alembic upgrade head` dentro da rede Docker interna usando o código do app.

Estado final desta rodada:

- VPS limpa dos projetos indevidos/intermediários.
- Banco staging final vivo e seguro: `gennomx-ai-postgres-ready`.
- Alembic, inventário Supabase, dump/restore e comparação permanecem pendentes.

Próximo caminho recomendado:

1. Reiniciar OpenCode para disponibilizar o MCP Supabase global recém-configurado.
2. Publicar uma imagem temporária do backend/migrations ou disponibilizar um repositório remoto privado para a VPS executar `alembic upgrade head` em container na rede `gennomx-ai-postgres-ready-private`.
3. Alternativamente, criar no Hostinger um mecanismo de arquivo/volume para injetar o SQL Alembic sem depender de variável de ambiente >8192 caracteres.

---

## Migração banco-only Supabase PostgreSQL -> PostgreSQL VPS — provisionamento Hostinger staging — 2026-07-09

Execução real via MCP Hostinger VPS, ainda sem cutover produtivo e sem migração de dados Supabase.

Executado na VPS Hostinger:

- VPS ativa identificada: `1817951` (`srv1817951.hstgr.cloud`, KVM 4, Ubuntu 24.04 com Docker/Traefik).
- Criado e ativado o firewall Hostinger `gennomx-ai-vps-public-ingress` (`325948`) com entrada pública restrita a SSH/22, HTTP/80, HTTPS/443 e ICMP. O firewall ficou associado à VPS e `is_synced=true` após sincronização explícita.
- Achado de segurança durante inspeção: já existia um projeto `postgresql-spko` com `postgres:17` e porta PostgreSQL publicada em `0.0.0.0:32768`/IPv6. O firewall aplicado bloqueia esse acesso público, mas o projeto legado continua rodando e deve ser removido/rotacionado com confirmação operacional.
- Provisionada stack segura `gennomx-ai-postgres-ready` com `pgvector/pgvector:0.8.1-pg16`, TLS interno por certificados gerados em volume Docker, rede Docker interna `gennomx-ai-postgres-ready-private`, sem `ports:` e com apenas `expose` interno em `5432`.
- Bootstrap da stack `gennomx-ai-postgres-ready` concluiu com `Exited (0)`: extensões `pgcrypto`, `uuid-ossp`, `pg_trgm`, `vector` e roles `gennomx_migrator`, `gennomx_worker`, `gennomx_app`, `gennomx_readonly` criadas com `NOSUPERUSER`/`NOBYPASSRLS` conforme contrato.
- O container Postgres final está `Up` e `healthy`, sem publicação de porta no host.

Incidente/limpeza:

- Durante tentativas intermediárias (`gennomx-ai-postgres`, `gennomx-ai-postgres-secure`, `gennomx-ai-postgres-final`), erros de quoting no bootstrap fizeram senhas de tentativa aparecerem nos logs do container. Essas senhas foram tratadas como comprometidas e **não são as credenciais da stack final `gennomx-ai-postgres-ready`**.
- As stacks intermediárias ficaram com Postgres healthy e bootstrap falho; após aprovação explícita, foram removidas na rodada seguinte. O projeto legado `postgresql-spko` também foi removido.

Não executado:

- MCP Supabase não estava exposto nesta sessão (`list_mcp_resources` não listou servidor Supabase); portanto não foi possível executar inventário real Supabase via MCP.
- Não foi executado Alembic no alvo, porque a stack Postgres está em rede Docker interna e a aplicação/migrations ainda não estão em container conectado a essa rede.
- Não foi executado dump/restore Supabase -> VPS, comparação pós-restore, testes de API/dashboard/MCP contra banco VPS ou cutover produtivo.

Próximo passo técnico seguro:

1. Parar/remover os projetos intermediários criados durante tentativa (`gennomx-ai-postgres`, `gennomx-ai-postgres-secure`, `gennomx-ai-postgres-final`) após confirmação.
2. Remover/rotacionar o projeto legado `postgresql-spko` após confirmar que não é usado por outro serviço.
3. Conectar um job/container de migrations à rede `gennomx-ai-postgres-ready-private` para rodar Alembic `head` usando `gennomx_migrator`.
4. Obter `SUPABASE_DIRECT_URL` por canal seguro ou disponibilizar o MCP Supabase nesta sessão para inventário/dump.

---

## Migração banco-only Supabase PostgreSQL -> PostgreSQL VPS — hardening de staging — 2026-07-09

Continuação segura da preparação banco-only, sem credenciais reais e sem executar inventário, provisionamento, restore ou cutover.

Implementado nesta sessão:

- `infra/postgres/bootstrap_roles_vps.sql`: bootstrap ficou mais reaplicável para staging/producao, atualizando senhas das roles a cada execução com variáveis `psql`, sem hardcode; `GRANT CONNECT` deixou de fixar o nome `gennomx` e passa a usar `current_database()`, permitindo `POSTGRES_DB` diferente em ensaios; `gennomx_readonly` passou a receber `USAGE, SELECT` em sequences, inclusive via default privileges, para suportar backup/inspeção sem role privilegiada.
- `infra/docker-compose.postgres-vps.yml`: serviço `backup` agora usa `PGSSLMODE=require` e `PGSSLROOTCERT=/run/secrets/postgres/ca.crt`, mantendo TLS também nas rotinas internas de backup.
- `backend/tests/unit/test_postgres_vps_artifacts.py`: testes unitários adicionados para travar contratos de segurança/operação dos artefatos: sem `ports:` para PostgreSQL, rede Docker interna, backup com TLS, bootstrap sem banco hardcoded, senha reaplicável e grants de sequences para `gennomx_readonly`.

Validações executadas:

```bash
python -m py_compile tools\postgres_inventory.py tools\compare_postgres_migration.py backend\app\config.py backend\tests\unit\test_postgres_vps_artifacts.py
```

Resultado: passou.

```bash
$env:POSTGRES_ADMIN_PASSWORD='dummy-postgres-admin-password'; $env:GENNOMX_BACKUP_PASSWORD='dummy-backup-password'; docker compose -f infra\docker-compose.postgres-vps.yml config
```

Resultado: passou com valores dummy apenas no processo; confirmou ausência de publicação de `5432`.

```bash
python -m pytest backend\tests\unit\test_secure_config.py backend\tests\unit\test_postgres_vps_artifacts.py -v --tb=short
```

Resultado: 14 passed.

```bash
cd backend && python -m ruff check app\config.py tests\unit\test_secure_config.py tests\unit\test_postgres_vps_artifacts.py ..\tools\postgres_inventory.py ..\tools\compare_postgres_migration.py
```

Resultado: passou após `ruff --fix` apenas ordenar imports no teste novo.

Não executado: inventário real do Supabase (`SUPABASE_DIRECT_URL` indisponível), provisionamento na Hostinger, bootstrap em banco real, Alembic no alvo, dump/restore, comparação pós-restore, testes de API/dashboard/MCP contra banco VPS e qualquer cutover produtivo.

Bloqueios permanecem: URL direta do banco Supabase, URL/credenciais do PostgreSQL VPS/staging, senhas fortes das quatro roles, certificados TLS reais fora do repo, storage externo para backups e janela operacional aprovada.

---

## Migração banco-only Supabase PostgreSQL -> PostgreSQL VPS — preparação técnica — 2026-07-09

Escopo confirmado: a primeira migração troca somente o banco principal para PostgreSQL/pgvector na VPS Hostinger. Supabase Auth/JWKS e Supabase Storage permanecem temporariamente e continuam exigidos por `SUPABASE_URL`, `SUPABASE_JWKS_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` e `STORAGE_BACKEND=supabase`.

Implementado/preparado nesta sessão:

- `backend/app/config.py`: nova variável `DATABASE_PROVIDER=supabase_postgres|vps_postgres`; em produção, `vps_postgres` falha fechado se `DATABASE_URL`, `WORKER_DATABASE_URL` ou `DATABASE_URL_SYNC` ainda apontarem para Supabase (`supabase.co`/`pooler.supabase.com`). Mantidas as validações existentes de TLS, roles `gennomx_app`/`gennomx_worker`/`gennomx_migrator`, `ROOT_PATH=/api/ai`, Redis TLS, Supabase JWKS e Storage Supabase.
- `infra/docker-compose.postgres-vps.yml`: compose preparado para PostgreSQL 16 + pgvector na VPS, sem publicar `5432`, usando rede Docker interna, volume persistente, healthcheck, volume de backups e TLS por certificados montados fora do Git em `infra/secrets/postgres/`.
- `infra/postgres/bootstrap_roles_vps.sql`: bootstrap idempotente de extensões e roles login `gennomx_migrator`, `gennomx_worker`, `gennomx_app`, `gennomx_readonly` com `NOSUPERUSER` e `NOBYPASSRLS`, grants e default privileges para Alembic/restores.
- `infra/postgres/backup.sh` e `infra/postgres/restore_check.sh`: backup custom-format com checksum e retenção simples; restore-check em banco temporário.
- `tools/postgres_inventory.py`: inventário seguro de versão, extensões, schemas, tabelas, índices, sequences, policies, grants, roles, `alembic_version`, contagens críticas e objetos Supabase-specific, lendo URL por env var sem imprimir segredos.
- `tools/compare_postgres_migration.py`: comparação pós-restore por contagem e checksum amostral em tabelas críticas.
- `.env.example`, `docs/05_SEGURANCA_E_GOVERNANCA.md`, `docs/09_DEPLOY_E_OPERACAO.md`, `docs/11_CHANGELOG_DECISOES.md` e `project_state/task_plan.md` atualizados para refletir banco VPS como alvo banco-only e Supabase Auth/Storage como dependências temporárias.
- Teste unitário adicionado para impedir `DATABASE_PROVIDER=vps_postgres` com URLs Supabase.

Não executado por segurança/ambiente: inventário real do Supabase, provisionamento na Hostinger, dump/restore, Alembic em staging/VPS, `make release-check`, `make handshake`, testes de API/dashboard/MCP contra banco VPS e qualquer cutover produtivo. Esses passos exigem credenciais/URLs reais, certificados TLS do Postgres e aprovação operacional explícita.

Bloqueios atuais: acesso direto ao banco Supabase atual (`SUPABASE_DIRECT_URL` ou equivalente), URL/credenciais do PostgreSQL VPS/staging, senhas fortes das quatro roles, certificados TLS do Postgres fora do repo e janela operacional para pausar ingestões.

---
# project_state / progress.md — GennomX AI

## Plano aprovado: migracao Supabase PostgreSQL para PostgreSQL na VPS - 2026-07-09

Marcus decidiu alterar a stack de dados: o PostgreSQL hospedado da Supabase deixara de ser o banco principal da GennomX AI e sera substituido por PostgreSQL/pgvector hospedado diretamente na VPS.

Registro criado:

- `project_state/plano_migracao_supabase_postgres_vps.md`: plano faseado para migrar primeiro o banco, mantendo Supabase Auth/JWKS e Supabase Storage temporariamente.

Decisao operacional: a migracao deve separar tres responsabilidades que hoje estavam agrupadas na Supabase: banco, Auth e Storage. A primeira fase migra somente o banco. Auth e Storage ficam como dependencias temporarias ate planos proprios, porque `backend/app/config.py`, frontend auth e `workers/storage/raw_payload.py` ainda dependem de variaveis e APIs Supabase.

Impacto no plano de data warehouse: ativacao recorrente pesada da ingestao deve esperar o PostgreSQL VPS virar fonte de verdade. Desenvolvimento de cobertura/qualidade e granularidade clinica pode seguir localmente/staging, mas validacao produtiva deve ocorrer no banco novo.

Validacao: alteracao documental/planejamento; nenhuma suite de codigo executada.

---

## Plano aprovado: data warehouse e ingestao recorrente - 2026-07-09

Marcus aprovou a construcao operacional do banco/data warehouse da GennomX AI e a implementacao das primeiras quatro etapas por outro agente de IA.

Registros criados:

- `project_state/plano_data_warehouse_ingestao.md`: plano detalhado de implementacao por ondas, cobrindo estado atual, entidades consultaveis por IA Host, cadencia de ingestao, qualidade, riscos, backlog e criterios de aceite.
- `project_state/prompt_implementacao_dw_etapas_1_4.md`: prompt de continuidade para iniciar as etapas 1-4 com foco em diagnostico, ativacao controlada dos conectores existentes, cobertura/qualidade do warehouse e granularidade clinica inicial.
- `project_state/task_plan.md`: nova secao "Data warehouse e ingestao recorrente" com escopo aprovado, etapas DW-1 a DW-4 e fora de escopo da primeira rodada.
- `docs/11_CHANGELOG_DECISOES.md`: decisao operacional registrada.

Decisao central: nao recriar a arquitetura nem tratar ingestao como greenfield. O projeto ja possui conectores P1, schema Supabase/PostgreSQL, Celery/Redis, MCP, dashboard, raw storage e evidencias. A implementacao deve operacionalizar, medir e expandir por ondas, mantendo o backbone estruturado antes de fontes ruidosas.

Validacao: alteracao documental/planejamento; nenhuma suite de codigo executada.

---

## F4 — basePath `/ai` e `API_ALLOWED_HOSTS`/`ROOT_PATH` alinhados — 2026-07-08

- `frontend/next.config.ts` agora recebe `NEXT_PUBLIC_BASE_PATH` e exporta o valor para o client.
- Adicionados `frontend/src/lib/base-path.ts` e `frontend/src/lib/api-base.ts`.
- `frontend/src/lib/api.ts` e `frontend/src/lib/api-server.ts` passaram a montar URLs via paths
  relativos (`api/v1/...`, `health`) com `apiUrl(...)`.
- `frontend/src/middleware.ts`, `frontend/src/app/login/page.tsx` e
  `frontend/src/components/layout/header.tsx` passaram a respeitar o basePath no fluxo de login e
  na busca.
- `frontend/scripts/check-base-path.mjs` foi adicionado e ligado ao `npm run check:base-path`.
- `backend/app/config.py` ganhou `ROOT_PATH=/api/ai` e `API_ALLOWED_HOSTS` refletindo a topologia
  ativa; `backend/app/main.py` passou a registrar `root_path=settings.root_path`.
- `.env.example`, `docs/05_SEGURANCA_E_GOVERNANCA.md`, `docs/09_DEPLOY_E_OPERACAO.md`,
  `docs/11_CHANGELOG_DECISOES.md` e o `project_state/` da raiz foram atualizados para a nova
  topologia `admin.gennomx.com/ai` / `admin.gennomx.com/api/ai` / `mcp.gennomx.com`.

**Validações:** `npm run lint`, `npm run typecheck`, `npm run check:base-path`, `npm run build` e
`npm run test:e2e` verdes. `backend/.venv/Scripts/python.exe -m pytest` nao rodou porque o venv nao
tem `pytest`; em seguida, `backend/.venv/Scripts/python.exe -m py_compile app\\config.py
app\\main.py` passou.

**Pendente:** edge/Traefik/hub real e redirects Supabase no projeto hospedado.

---

## PLAN-003 (raiz): bloqueio do compose legado + documentação da topologia atual — 2026-07-06

Trabalho executado a partir do PLAN-003 do workspace raiz
(`project_state/plans/PLAN-003-correcao-issues-revisao-tecnica.md`). Achado: `infra/docker-compose.prod.yml`
ainda publica Caddy em `80:80`/`443:443` para um domínio próprio (`api.gennomx.ai`), topologia
substituída em 2026-07-04 pela decisão D-011 do workspace raiz (GennomX AI passa a viver sob
`gennomx.com`: hub `admin.gennomx.com/ai`, API `admin.gennomx.com/api/ai`, MCP `mcp.gennomx.com`,
atrás do Traefik já compartilhado com outro projeto na VPS — F-006 da raiz). A F4 (migração real
para essa topologia: `basePath=/ai`, `API_ALLOWED_HOSTS`/CORS de `gennomx.com`) **continua pendente**
— por decisão explícita de não fazer uma migração grande sem necessidade confirmada, esta rodada
tratou apenas do mínimo aceitável: impedir uso acidental do compose legado.

- `infra/docker-compose.prod.yml`: adicionado cabeçalho de aviso explicando que o arquivo é legado
  nessa topologia e por quê (disputaria portas 80/443 do Traefik compartilhado).
- `Makefile`: `prod-up` agora recusa subir `docker-compose.prod.yml` sem a variável de ambiente
  `ACKNOWLEDGE_LEGACY_TOPOLOGY=yes`, imprimindo a topologia atual esperada e onde ler mais
  (`docs/09_DEPLOY_E_OPERACAO.md`). Uso legítimo (ambiente isolado, sem Traefik/gennomx.com
  compartilhado) permanece possível com o ack explícito.
- `docs/09_DEPLOY_E_OPERACAO.md`: nota datada de 2026-07-06 na seção "Stack produtiva mínima"
  marcando-a como registro histórico da topologia `api.gennomx.ai` (aprovada em 2026-07-02), não
  como plano ativo, e apontando para a F4 do PLAN-002 da raiz como o caminho de migração real.

**Auditoria de `.env`/segredos (sem expor valores):** confirmado via `git status --ignored` que
`.env`, `backend/.env` e `frontend/.env.local` estão corretamente listados como ignorados pelo
`.gitignore` local; `.env.example` (raiz do app) não está coberto por regra de ignore. Este
repositório segue **sem nenhum commit** (decisão do fundador em 2026-07-02, ver A5 em
"Preparação do deploy do MVP" abaixo) — o achado relevante é que, quando o primeiro commit for
feito, os `.env` reais não serão incluídos por acidente.

**Validação:** `npm audit --audit-level=moderate` em `frontend/` → 0 vulnerabilidades. Guard do
`make prod-up` testado simulando a lógica do shell fora do `make` (não havia `make` disponível no
ambiente desta sessão): bloqueia sem `ACKNOWLEDGE_LEGACY_TOPOLOGY=yes`, prossegue com ele.
`pip-audit` não verificado (não instalado; nenhum arquivo Python foi alterado nesta rodada).

**Pendente:** F4 real (migração de `next.config.ts`/`config.py`/CORS/hosts para a topologia
`gennomx.com`) segue não implementada — este registro cobre apenas o bloqueio operacional do
caminho legado, não a migração.

---

## Prontidão de deploy MVP — 2026-07-02

- Retry manual (`POST /api/v1/jobs/{id}/retry`) agora cobre todos os conectores P1 implementados:
  `clinicaltrials_gov`, `pubmed`, `openfda`, `dailymed`, `open_targets` e `ema`.
- Produção deixou de depender de domínio hardcoded: `API_ALLOWED_HOSTS` alimenta o
  `TrustedHostMiddleware` e rejeita wildcard global/localhost em `ENVIRONMENT=production`.
- Adicionada base produtiva para Hostinger VPS: `infra/docker-compose.prod.yml` (API, worker,
  beat, Redis TLS, Caddy) e `infra/Caddyfile`; `Makefile` ganhou `prod-up`, `prod-down`,
  `prod-logs` e `release-check`.
- `.env.example`, `docs/05`, `docs/09` e `docs/11` atualizados com Redis `rediss://`, domínio API,
  checklist de pré-deploy, migração `0006`, gates e handshake.
- `.gitignore` corrigido para não ignorar `frontend/src/lib/` no primeiro commit; `.env`, caches,
  builds, `node_modules` e `secrets/` seguem ignorados.
- `project_state/fontes_priorizacao.xlsx` atualizado para marcar ClinicalTrials.gov, PubMed,
  openFDA, DailyMed, Open Targets e EMA como implementados, mantendo ANVISA e PMC full-text fora
  desta rodada por decisão explícita.
- Pendente de ambiente externo: executar `make release-check`, `make handshake` com rede liberada,
  aplicar Alembic `0006` no Supabase real, provisionar frontend Vercel/Netlify e realizar primeiro
  commit/push com secret scan.

## Reorganização documental e higiene de estrutura — 2026-07-02

- Históricos sucedidos consolidados em `project_state/archive/`: `TASKFLOW.md` (da raiz) e
  `MEMORY_FASE_2/5/6.md` (de `docs/`), sem alteração de conteúdo.
- `Referências de Design/` (raiz) movida para `docs/_referencias_design/` (nome sem espaços/acentos);
  diretório vazio `.agents/` removido.
- `docs/README.md` reescrito como índice completo (docs de área ↔ fases VLAEG + diretórios
  complementares); referências atualizadas em `AGENTS.md` §14A, `docs/13` §3/§5, `task_plan.md` e este arquivo.
- Higiene verificada: `.gitignore` cobre `.env*`, `secrets/`, caches, builds e logs; nenhuma
  referência quebrada restante (busca global por `TASKFLOW`, `MEMORY_FASE` e nomes movidos).
- Decisão registrada em `docs/11_CHANGELOG_DECISOES.md` (2026-07-02).

## Conectores P1 — openFDA, DailyMed, Open Targets, EMA — 2026-07-02

- Implementados os quatro conectores regulatórios/target P1 restantes, seguindo o padrão VLAEG
  do conector `pubmed` (Link via `healthcheck()` → persistência → task Celery → beat schedule →
  testes → docs).
- Persistência compartilhada nova: `workers/persistence/regulatory.py` (openFDA/DailyMed/EMA →
  `regulatory_approvals`, resolvendo `DrugAsset` por nome/alias) e `workers/persistence/targets.py`
  (Open Targets → `targets`, merge não destrutivo de aliases/indicações).
- Nenhuma migração de schema foi necessária — `regulatory_approvals`, `targets` e as linhas de
  `data_sources` para as quatro fontes já existiam desde `0001_initial_schema.py`.
- `get_regulatory_status` (MCP) passa a retornar dados reais de aprovação FDA/EMA em vez de tabela
  vazia; `search_drugs`/`compare_assets` ganham `special_designations`/`pathway` quando presentes.
- Nova dependência `openpyxl` para parsing do export oficial EMA (`.xlsx`).
- Bug real corrigido durante os testes: consulta de aprovação existente em `regulatory.py` não
  recuperava `source_updated_at`, fazendo o motor de decisão cair sempre em `CONFLICT` em vez de
  `REPLACE` ao reingerir a mesma fonte com dado mais recente.
- Validação: Ruff aprovado (`app workers tests migrations`), 39 testes novos, suíte completa
  223 passed / 2 skipped (skips ambientais pré-existentes de DuckDB no Python 3.14 local).
  `mypy` não pôde ser executado localmente (dependências dev não instaladas no Python 3.14 local);
  gate oficial permanece o CI (Python 3.12).
- Documentação: `docs/03` §0.2C–0.2F (contratos) e §6.8C (estado implementado + limitações),
  matriz Link atualizada, `docs/04` (`get_regulatory_status`), `docs/09` §0.1B (automação),
  `docs/11` (changelog), `.env.example` com as novas variáveis de configuração.
- Pendente (Onda B, prontidão de deploy): atualizar `project_state/fontes_priorizacao.xlsx`
  (status das quatro fontes de "Não implementado" para "Implementado").

## Conector PubMed — 2026-06-23

- Implementado o conector PubMed conforme `project_state/plano_conector_pubmed.md` (P1, ordem 2).
- Slug `pubmed` separado de `pubmed_pmc` (legado, permanece inativo). PMC full-text adiado para ordem 3.
- Connector: E-utilities NCBI (ESearch com history → EFetch via WebEnv/query_key → parsing XML),
  rate limit `PUBMED_RATE_LIMIT_REQUESTS_PER_SECOND`, retry com `tenacity`, batch de 100 registros.
- Parser: `xml.etree.ElementTree` (stdlib) — PMID, DOI, PMCID, title, abstract estruturado (Label),
  journal, authors (LastName+ForeName/CollectiveName), keywords (MeSH), NCT (DataBank).
- Normalizer: `publication_type` controlado (`article|preprint|review|abstract|letter`),
  `evidence_maturity=peer_reviewed_primary`, `registry_source=pubmed`, `source_url` com link PMID.
- Persistência: `_persist_publications` com stage/dedup por PMID, quality gate (PMID+title),
  `PersistenceDecisionEngine`, `SourceDocument` (`source_type=scientific_publication`),
  `EvidenceSnippet` (`entity_type=publication`), NCT linking contra `clinical_trials.nct_id`.
- Task Celery `run_pubmed_ingest` com `JobTracker`, invarianes de savepoint/falha sistêmica/limite de lote.
- Migração `0005` adiciona `data_sources.pubmed`. Alembic upgrade/downgrade testado offline.
- Handshake `tools/handshake.py` inclui `PubMedConnector`; beat schedule diário (`pubmed-daily-incremental`).
- Testes unitários: healthcheck (ok/unreachable/error/config_error), parser (XML completo/mínimo/review),
  normalizer (completo/mínimo/null), persistence flow (insert/update/noop/falha/quality gate).
- Documentação: contrato `pubmed` em `docs/03` §0.2B, matriz Link atualizada, §6.8B (estado implementado),
  `docs/04` (§search_publications) com nota de fonte real, changelog `docs/11` com decisão de slug.

## Integração Supabase como banco — 2026-06-23

- Backend, workers e Alembic agora normalizam URLs Supabase/PostgreSQL para o driver correto
  (`asyncpg` no runtime, `psycopg2` nas migrações).
- `.env.example` documenta conexão hospedada Supabase com pooler para app/worker e direct
  connection para migrações.
- `infra/supabase/bootstrap_roles.sql` cria extensões, roles dedicadas e grants mínimos para
  `gennomx_app`, `gennomx_worker`, `gennomx_migrator` e `gennomx_readonly`.
- README, segurança e changelog registram o fluxo de ativação: bootstrap, `.env`, Alembic e
  readiness.
- Projeto Supabase `qfanrziwepkqkgtvfrdt` recebeu bootstrap real, Alembic `upgrade head` até
  `0005` e grants pós-migração. Verificação confirmou `gennomx_app`, `gennomx_worker` e
  `gennomx_migrator` sem superuser/BYPASSRLS, todas enxergando `alembic_version=0005`.
- Service role legado foi removido dos `.env` locais e marcado para substituição pelo valor
  rotacionado. FastAPI agora valida JWT Supabase via JWKS (`ES256`/`RS256`) com fallback HS256
  apenas para transição.

## Conclusão operacional da governança — 2026-06-21

- Migração `0004` operacionaliza temporalidade granular, metadados, correções, retenção e scraping.
- Registry de políticas falha fechado e o serviço genérico decide insert/replace/enrich/noop/
  reject/archive/conflict/quarantine com evidência e granularidade.
- DuckDB está ligado ao lote quando existe chave natural repetida; quality gates precedem escrita.
- Correções humanas exigem evidência e revisão; não há edição factual destrutiva.
- Freshness diário sinaliza revalidação e MCP/API retornam somente projeções correntes.
- Retenção semanal arquiva com checksum/manifesto, respeita legal hold e só depois expurga.
- Scraping é fail-closed e dispõe de kill switch administrativo no dashboard.
- O passo 11 permanece adiado e nenhum modelo foi selecionado ou acoplado.

Gate final: 115 testes aprovados, 2 skips ambientais (DuckDB e BeautifulSoup ausentes no
Python 3.14 local), Ruff/ESLint/TypeScript aprovados e Alembic upgrade/rollback offline aprovados.
Build Next de produção aprovado, incluindo `/governance`.

## Remediação de revisão externa — 2026-06-21

- Corrigido bug crítico do INSERT de `SourceDocument` e escopo da evidência granular.
- Persistência de página falha quando todos os registros sofrem exceção sistêmica.
- Teste do fluxo completo exige documento, trial, evidência, assertions e contador inserido.
- Limite de lote deixou de acionar retry fatal.
- Roles de API/worker/migrator foram separados e validados por nome, superuser e bypass RLS.
- SSR passou a usar JWT individual + `no-store`; build comprovou rotas dinâmicas protegidas.
- Chave interna virou service sem admin; auth MCP morta removida; compare constante aplicado.
- Runner assíncrono Celery foi unificado.
- Dedup exato abre conflito sem merge; confidence/completeness são calculados por regra versionada.
- `.gitignore` já cobre `.pyc`, caches, `.next` e builds. Python 3.14 local não é gate oficial.

Validações finais desta rodada: 104 testes unitários/de integração aprovados (1 skip por DuckDB
ausente no Python local), incluindo contrato HTTP completo do MCP; Ruff, ESLint, TypeScript e
build Next aprovados; Alembic `upgrade head --sql` aprovado. O warning de cache do pytest é uma
limitação do caminho/sandbox no Windows e não altera o resultado dos testes.

## Governança temporal e persistência — 2026-06-20

- ADR-001 formalizou current state como projeção e assertions como histórico bitemporal.
- Migração `0003` adicionou assertions, conflitos, correções, current/supersession, RLS e índices.
- Motor puro de decisão implementou insert/replace/enrich/noop/reject/archive/conflict/quarantine.
- CT.gov passou a comparar `source_updated_at` e hash antes de atualizar o canônico.
- Relações trial↔ativo são encerradas temporalmente; estágio de ativo foi separado em corrente,
  máximo histórico e status de desenvolvimento.
- Evidências críticas passaram a ser produzidas por campo; staging DuckDB e quality gates foram
  adicionados antes da gravação.
- Retenção, arquivamento, edição corretiva e scraping controlado foram documentados.
- Testes foram adicionados para decisões, versão atrasada, idempotência, conflito, ausência de
  evidência, hashing, quality gates, DuckDB e contrato da migração.
- A escolha de modelos LLM permaneceu fora desta entrega por decisão explícita do usuário.

## Programa de correção — Fase 5 (2026-06-20)

- Stubs de empresas, indicações, targets, jobs, logs MCP e segurança substituídos por telas reais.
- API ganhou catálogos de indicações/targets e auditoria administrativa sanitizada.
- Logs do dashboard omitem argumentos MCP, IDs de ator, hashes de IP e metadados brutos.
- Playwright cobre sete fluxos essenciais do dashboard; build Next de produção aprovado.
- CI ganhou E2E, `npm audit`, mypy, pip-audit e Bandit bloqueantes.
- Dependências vulneráveis foram elevadas; `python-jose` foi substituído por PyJWT e
  LiteLLM vulnerável foi colocado em quarentena fora do runtime principal.
- Validação: Ruff/format, 78 testes unitários, mypy, ESLint, TypeScript, build,
  7 E2E, npm audit, pip-audit e Bandit aprovados.

## Programa de correção — Fase 4 (2026-06-20)

- Migração `0002` converte referências escalares para UUID, cria 19 FKs e quatro checks.
- Relação canônica `clinical_trial_assets` criada e sincronizada pelo worker.
- RLS deny-by-default e políticas por papel habilitadas no domínio e auditoria.
- Senhas fixas removidas do init SQL; papéis locais passaram a grupos `NOLOGIN`.
- Readiness verifica PostgreSQL e Redis; Compose e imagem backend foram endurecidos.
- Comandos Alembic do Makefile/CI corrigidos; Python suportado limitado a `<3.14`.
- Validação: Ruff, 73 testes, SQL offline de upgrade/rollback e Compose config aprovados.

## Programa de correção — Fase 3 (2026-06-20)

- CT.gov usa `data_sources.last_successful_run` como cursor, com sobreposição configurável.
- Paginação é persistida por página; o limite de volume não avança o cursor.
- Retry Celery cobre falhas sistêmicas e cada registro usa savepoint.
- Raw JSON canônico é comprimido, endereçado por hash e registrado em `SourceDocument`.
- Evidências são fragmentos JSON literais da fonte e são idempotentes.
- Validação: Ruff aprovado e 64 testes unitários aprovados.

**Histórico consolidado de execução.** Consolida `MEMORY_FASE_2.md`, `MEMORY_FASE_5.md` e `MEMORY_FASE_6.md` (preservados como histórico em `project_state/archive/`).

## Programa de correção — Fase 1 (2026-06-20)

- Removidos defaults administrativos exploráveis e adicionada validação fail-closed de produção.
- JWT Supabase reforçado com issuer/audience e papel de aplicação em `app_metadata.gennomx_role`.
- Frontend ganhou login Supabase, proteção por middleware e propagação de bearer token.
- Health foi separado em liveness (`/health`) e readiness de banco (`/ready`).
- Documentação de segurança e estado atualizada na mesma fase.

## Programa de correção — Fase 2 (2026-06-20)

- FastMCP/stdio adicionado como transporte padrão; adaptador HTTP legado preservado.
- Escopos por cliente, comparação de token em tempo constante e rate limit Redis aplicados.
- Request limitado, JSON validado, erro 500 sanitizado e entidades acessadas auditadas com limite.
- Testes unitários adicionados para escopos e auditoria bounded.
- Validação: 11 testes MCP aprovados e Ruff aprovado; apenas warning local de cache pytest por caminho sandbox foi emitido.


---

## Fase 2 — Serviços FastAPI, Schemas, Workers (2026-06-09)

- Camada de serviços: `AssetService`, `CompanyService`, `TrialService`, `SourceService` (recebem `AsyncSession`, `list_*` retorna `tuple[list[dict], int]`, `get_*_detail` lança `NotFoundError`).
- Schemas Pydantic v2: `DrugAssetList`, `DrugAssetDetail` (demais endpoints retornam `dict`).
- Workers Celery: `run_clinicaltrials_ingest` (com JobTracker), `link_trials_to_assets` (com
  backfill), deduplicação exata conservadora e cálculo determinístico de confiança/completude.
- Conector ClinicalTrials.gov: paginação, rate limit, retry (tenacity), parser e normalizer.
- `Dockerfile` backend multi-stage (Python 3.12-slim, non-root).

## Fase 5 — Frontend Next.js (2026-06-09)

- Next.js (App Router) + TypeScript + Tailwind; Design System GennomX (rose `#F2829B`, Montserrat/Inter).
- Registro histórico de 2026-06-09: Overview, Assets, Asset detail, Trials e Sources
  funcionais; os stubs então existentes foram substituídos na correção Fase 5 de 2026-06-20.
- API client centralizado em `src/lib/api.ts`; componentes UI base em `src/components/ui`.
- Auth Supabase prevista, ainda não implementada.

## Fase 6 — Testes + CI/CD (2026-06-09)

- pytest com markers (`unit`, `integration`, `mcp`, `connector`, `slow`); fixtures `mock_db`/`FakeRow`/`FakeResult`/`override_settings`.
- CI GitHub Actions: backend-lint, backend-unit, backend-integration, frontend-lint, frontend-build, security.

## Atualização 2026-06-12 — Correções de integração MCP, jobs e rastreabilidade

- MCP `_dispatch_tool()` recebe sessão real do banco; persiste `mcp_query_logs` inclusive em chamadas inválidas/bloqueadas.
- `GET /api/v1/jobs` usa `SourceService.list_jobs()`; `POST /api/v1/jobs/{id}/retry` reenfileira Celery (CT.gov).
- `JobTracker` resolve `data_source_id` e serializa `error_detail`/`metadata` como JSON válido.
- CT.gov cria/reusa `SourceDocument`, cria `EvidenceSnippet` por trial e por ativo; cria/atualiza `DrugAsset` a partir de intervenções (`DRUG`/`BIOLOGICAL`/`GENETIC`) e preenche `clinical_trials.drug_asset_ids`.
- `pyproject.toml` com `setuptools.build_meta:__legacy__`; `structlog.stdlib.LoggerFactory()`; atributos ORM `metadata` renomeados.
- Backend: Ruff + 50 testes passando. Frontend: Next 15.5.18, `npm ci`, lint/typecheck/build ok. Pendem 2 vulnerabilidades moderadas (`postcss` transitivo do Next).

---

## Pendências abertas (rastreadas)

- Executar o teste de staging DuckDB também no ambiente oficial Python 3.11–3.13 com o extra de
  dependências instalado; a implementação existe, mas o Python 3.14 local não possui DuckDB.
- Schemas Pydantic tipados para `Company`, `Trial`, `Indication`.
- Conectores: PMC full-text (ordem 3, adiado do PubMed) e ANVISA seguem pendentes; PubMed,
  openFDA, DailyMed, Open Targets e EMA implementados (2026-06-23 e 2026-07-02).
- Testes ainda desejáveis: services legados restantes, ferramentas MCP individuais,
  conectores futuros com `httpx.MockTransport` e meta formal de cobertura.
- Rodar `make handshake` contra as APIs reais de openFDA/DailyMed/Open Targets/EMA em ambiente com
  rede liberada (handshake não foi executado ao vivo nesta sessão, apenas smoke-tests offline com
  fixtures e a suíte de testes unitários com mocks).

> Registro de decisões formais permanece em `docs/11_CHANGELOG_DECISOES.md`.


