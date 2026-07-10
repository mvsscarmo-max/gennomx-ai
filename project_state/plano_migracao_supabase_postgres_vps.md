# Plano de migracao - Supabase PostgreSQL para PostgreSQL na VPS

**Data:** 2026-07-09  
**Solicitante:** Marcus  
**Status:** proposto/aprovado para planejamento; execucao exige janela operacional explicita  
**Escopo:** GennomX AI - banco PostgreSQL principal  
**Fora de escopo imediato:** migrar Auth e Storage no mesmo corte, salvo nova decisao explicita

## 1. Decisao operacional

A GennomX AI deixara de usar o PostgreSQL hospedado da Supabase como banco principal e passara a usar PostgreSQL/pgvector hospedado diretamente na VPS da GennomX.

A migracao deve ser faseada:

1. **Banco primeiro:** mover schema e dados do PostgreSQL Supabase para PostgreSQL na VPS.
2. **Auth depois:** manter Supabase Auth/JWKS temporariamente ou substituir por Auth proprio/OIDC em uma fase separada.
3. **Storage depois:** manter Supabase Storage temporariamente ou substituir por S3-compatible/MinIO/volume versionado em uma fase separada.

Motivo: hoje o projeto usa Supabase em tres papeis distintos: banco, Auth/JWKS e Storage de raw payload. Migrar tudo de uma vez aumenta o risco de quebrar login, ingestao, raw auditavel, MCP e dashboard simultaneamente.

## 2. Estado atual impactado

### 2.1 Banco

O projeto ja usa PostgreSQL como banco relacional principal, com:

- Alembic migrations;
- roles `gennomx_app`, `gennomx_worker`, `gennomx_migrator`, `gennomx_readonly`;
- RLS/policies;
- extensoes `pgcrypto`, `uuid-ossp`, `pg_trgm`, `vector`;
- validacao de role em runtime;
- URLs separadas:
  - `DATABASE_URL` para FastAPI/MCP;
  - `WORKER_DATABASE_URL` para Celery;
  - `DATABASE_URL_SYNC` para Alembic.

### 2.2 Auth

Ainda ha acoplamento com Supabase Auth:

- `SUPABASE_URL`;
- `SUPABASE_ANON_KEY`;
- `SUPABASE_JWKS_URL`;
- `SUPABASE_JWT_AUDIENCE`;
- `SUPABASE_JWT_ISSUER`;
- frontend com `NEXT_PUBLIC_SUPABASE_URL` e `NEXT_PUBLIC_SUPABASE_ANON_KEY`.

Na primeira fase, manter Supabase Auth e JWKS e trocar apenas o banco.

### 2.3 Storage

`backend/workers/storage/raw_payload.py` atualmente so envia raw payload para Supabase Storage quando `STORAGE_BACKEND=supabase`. O adapter S3 existe como configuracao, mas o codigo falha explicitamente para S3.

Na primeira fase, manter Supabase Storage para raw payload. Em fase posterior, implementar adapter S3-compatible/MinIO/local object storage antes de abandonar Supabase Storage.

## 3. Arquitetura alvo da fase banco

### 3.1 PostgreSQL na VPS

Recomendado:

- PostgreSQL 16 com pgvector, preferencialmente imagem `pgvector/pgvector:0.8.1-pg16` ou pacote equivalente;
- container ou servico dedicado na VPS, sem porta publica aberta;
- acesso apenas pela rede Docker interna/Traefik app network ou loopback/VPN;
- TLS obrigatorio para conexoes de producao, se cruzarem boundary de container/host/rede;
- volume persistente dedicado;
- backups automatizados para fora do volume local;
- restore testado antes do cutover;
- roles dedicados com `NOSUPERUSER NOBYPASSRLS`;
- usuario admin/migrador de emergencia guardado fora do repo.

### 3.2 Conexoes alvo

Exemplo conceitual, sem senhas reais:

```env
DATABASE_URL=postgresql+asyncpg://gennomx_app:<senha>@gennomx-postgres:5432/gennomx?ssl=require
WORKER_DATABASE_URL=postgresql+asyncpg://gennomx_worker:<senha>@gennomx-postgres:5432/gennomx?ssl=require
DATABASE_URL_SYNC=postgresql://gennomx_migrator:<senha>@gennomx-postgres:5432/gennomx?sslmode=require
```

Se as conexoes forem estritamente dentro da mesma rede Docker privada e sem TLS na fase inicial, sera necessario alterar a validacao de producao em `backend/app/config.py`, pois hoje producao exige `ssl=require`/`sslmode=require`. Recomendacao: manter TLS e nao relaxar a validacao em producao.

## 4. Plano de migracao por fases

### Fase 0 - Decisao e congelamento de escopo

Objetivo: confirmar que a primeira migracao e somente do banco.

Tarefas:

- registrar decisao em `docs/11_CHANGELOG_DECISOES.md`;
- atualizar `project_state/task_plan.md`;
- declarar que Supabase Auth e Supabase Storage permanecem temporariamente;
- definir janela de cutover;
- definir RPO/RTO desejado;
- confirmar se o banco Supabase atual e fonte de verdade ate o cutover.

Criterios de aceite:

- plano aprovado;
- janela operacional definida;
- rollback definido;
- nenhum dado migrado ainda.

### Fase 1 - Inventario do banco Supabase atual

Objetivo: saber exatamente o que sera migrado.

Tarefas:

- confirmar versao PostgreSQL, extensoes e `alembic_version` no Supabase;
- medir tamanho do banco;
- listar tabelas, indices, sequences, policies e grants;
- contar registros por tabela critica;
- identificar objetos Supabase-specific que nao devem migrar;
- confirmar se ha dados em auth/storage que nao fazem parte do banco da aplicacao.

Comandos conceituais:

```bash
pg_dump --schema-only --no-owner --no-privileges <SUPABASE_DIRECT_URL> > supabase_schema.sql
pg_dump --data-only --format=custom --no-owner --no-privileges <SUPABASE_DIRECT_URL> -f supabase_data.dump
psql <SUPABASE_DIRECT_URL> -c "select version();"
psql <SUPABASE_DIRECT_URL> -c "select * from alembic_version;"
```

Criterios de aceite:

- inventario registrado em `project_state/progress.md`;
- contagens base salvas para comparacao pos-migracao;
- extensoes confirmadas no alvo.

### Fase 2 - Provisionar PostgreSQL/pgvector na VPS

Objetivo: criar o alvo sem tocar no Supabase.

Tarefas:

- criar servico PostgreSQL/pgvector na stack da VPS;
- criar volume persistente;
- configurar rede privada;
- configurar TLS se exigido pela topologia;
- configurar backup diario e retencao;
- criar job de restore testado em staging;
- criar healthcheck;
- nao expor porta 5432 publicamente;
- gerar senhas fortes fora do repo.

Criterios de aceite:

- `pg_isready` verde;
- extensoes instaladas;
- backup e restore de teste funcionando;
- porta nao publica;
- credenciais fora do Git.

### Fase 3 - Bootstrap de roles e schema no PostgreSQL da VPS

Objetivo: reproduzir permissao e schema com governanca.

Tarefas:

- criar script novo ou adaptar `infra/supabase/bootstrap_roles.sql` para PostgreSQL VPS, por exemplo `infra/postgres/bootstrap_roles_vps.sql`;
- criar login roles reais:
  - `gennomx_migrator`;
  - `gennomx_worker`;
  - `gennomx_app`;
  - `gennomx_readonly`;
- garantir `NOSUPERUSER NOBYPASSRLS`;
- rodar Alembic `upgrade head` no banco vazio;
- reaplicar grants pos-migracao;
- validar RLS/policies.

Criterios de aceite:

- `alembic_version` no alvo esta em `head`;
- API consegue conectar com `gennomx_app`;
- worker consegue conectar com `gennomx_worker`;
- migrator consegue DDL;
- roles nao tem superuser nem bypassrls.

### Fase 4 - Migracao de dados Supabase -> VPS em staging

Objetivo: restaurar dados em ambiente alvo de ensaio antes do cutover real.

Abordagem recomendada:

1. Criar schema alvo via Alembic.
2. Exportar dados Supabase com `pg_dump --data-only --format=custom --no-owner --no-privileges`.
3. Restaurar no alvo com usuario administrativo/migrator controlado.
4. Ajustar sequences.
5. Reaplicar grants.
6. Rodar validacoes.

Comandos conceituais:

```bash
pg_dump --data-only --format=custom --no-owner --no-privileges "$SUPABASE_DIRECT_URL" -f supabase_data.dump
pg_restore --data-only --no-owner --no-privileges --dbname "$VPS_DATABASE_URL_SYNC" supabase_data.dump
psql "$VPS_DATABASE_URL_SYNC" -c "select setval(pg_get_serial_sequence(...), ...);"
```

Observacao: se houver problemas de ordem/FKs/RLS, usar restore com usuario owner/admin local em janela controlada, nunca com role de app/worker.

Criterios de aceite:

- contagens batem com Supabase;
- checksums/amostras batem para tabelas criticas;
- MCP tools retornam dados equivalentes;
- dashboard abre com dados;
- jobs de ingestao em dry-run nao duplicam nem corrompem;
- `/ready` verde.

### Fase 5 - Testes de aplicacao contra PostgreSQL VPS

Objetivo: validar comportamento real antes do corte.

Tarefas:

- apontar ambiente staging para banco VPS;
- manter Supabase Auth e Storage temporariamente;
- rodar gates:

```bash
make release-check
make handshake
cd backend && python -m alembic -c migrations/alembic.ini current
cd backend && pytest tests/unit tests/integration -v --tb=short
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm run build
```

- validar manualmente:
  - login;
  - overview;
  - assets;
  - trials;
  - sources/jobs;
  - MCP autenticado;
  - um job de ingestao limitado;
  - raw payload ainda indo para Supabase Storage.

Criterios de aceite:

- gates verdes ou bloqueios documentados;
- zero regressao funcional critica;
- plano de rollback testado.

### Fase 6 - Cutover controlado

Objetivo: trocar a fonte de verdade do banco para VPS.

Passos recomendados:

1. Pausar Celery beat e qualquer ingestao recorrente.
2. Colocar app em modo manutencao ou janela sem escrita.
3. Fazer backup final Supabase.
4. Fazer dump final de dados.
5. Restaurar no PostgreSQL VPS.
6. Rodar comparacao de contagens/checksums.
7. Atualizar secrets/env de API, worker e Alembic para banco VPS.
8. Subir API/worker/beat apontando para VPS.
9. Validar `/ready`, dashboard e MCP.
10. Reativar ingestao recorrente com limites conservadores.
11. Monitorar por 24-72h.

Criterios de aceite:

- aplicacao usa PostgreSQL VPS;
- Supabase DB fica read-only/backup temporario;
- nenhum job pendente aponta para Supabase DB;
- rollback ainda possivel durante janela definida.

### Fase 7 - Pos-cutover e descomissionamento parcial

Objetivo: reduzir dependencias da Supabase sem pressa perigosa.

Tarefas:

- manter backup Supabase por periodo definido;
- documentar novo runbook de backup/restore da VPS;
- atualizar `.env.example`, `docs/05`, `docs/09`, `docs/01`, `docs/08` e `project_state` para PostgreSQL VPS como banco principal;
- revisar validacoes de producao em `backend/app/config.py` para distinguir:
  - banco PostgreSQL VPS;
  - Supabase Auth temporario;
  - Supabase Storage temporario.
- planejar migracao posterior de Storage para S3-compatible/MinIO;
- planejar migracao posterior de Auth para auth proprio/OIDC, se desejado.

Criterios de aceite:

- docs nao chamam mais Supabase DB de banco principal;
- Supabase permanece apenas como Auth/Storage temporario, se ainda usado;
- backups e restore da VPS testados.

## 5. Pontos tecnicos que exigem alteracao de codigo/config

### 5.1 `backend/app/config.py`

Hoje producao exige:

- `SUPABASE_URL`;
- `SUPABASE_SERVICE_ROLE_KEY`;
- `SUPABASE_JWKS_URL`;
- banco com TLS;
- roles `gennomx_app`, `gennomx_worker`, `gennomx_migrator`.

Na fase banco-only, manter Supabase Auth/Storage permite preservar essas exigencias. Em fase posterior, separar nomes e validacoes:

- `AUTH_PROVIDER=supabase|internal|oidc`;
- `STORAGE_BACKEND=supabase|s3|minio`;
- `DATABASE_PROVIDER=vps_postgres|supabase_postgres` se util para clareza operacional.

### 5.2 `backend/workers/storage/raw_payload.py`

Hoje S3 nao esta implementado. Para abandonar Supabase Storage, sera necessario:

- implementar adapter S3-compatible;
- validar upload idempotente por hash;
- suportar MinIO ou outro S3-compatible na VPS;
- atualizar testes;
- atualizar retention/archive.

### 5.3 Frontend/Auth

Enquanto Supabase Auth for mantido, frontend continua usando:

- `NEXT_PUBLIC_SUPABASE_URL`;
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`.

Migrar Auth depois exige projeto proprio: sessao, JWT/JWKS ou OIDC, RBAC, middleware Next, testes e rotacao.

## 6. Backup, restore e rollback

### 6.1 Backups obrigatorios

- Backup final Supabase antes do cutover.
- Backup inicial PostgreSQL VPS apos restore.
- Backup diario automatizado da VPS.
- Retencao minima recomendada: 7 diarios, 4 semanais, 3 mensais para MVP interno.
- Copia fora da VPS, preferencialmente storage externo.

### 6.2 Rollback

Rollback durante janela:

1. Pausar API/worker/beat.
2. Reapontar env para Supabase DB.
3. Subir API/worker sem processar ingestao atrasada automaticamente.
4. Validar `/ready` e MCP.
5. Registrar divergencia e descartar dados escritos na VPS ou reconciliar manualmente.

Rollback depois de escrita no novo banco exige reconciliacao de deltas. Por isso o periodo inicial deve ter ingestao limitada e monitorada.

## 7. Riscos

| Risco | Impacto | Mitigacao |
|---|---|---|
| Confundir Supabase DB com Supabase Auth/Storage | quebrar login ou raw payload | migracao faseada; banco primeiro |
| Porta PostgreSQL exposta publicamente | risco critico de seguranca | rede privada/VPN/firewall; sem 0.0.0.0:5432 |
| Relaxar TLS em producao | credenciais/dados em risco | manter TLS ou justificar excecao temporaria nao produtiva |
| Roles sem RLS correto | vazamento ou falha de escrita | validar `rolsuper=false`, `rolbypassrls=false`, tests |
| Dump/restore incompleto | perda de dados | contagens, checksums, amostras e backup final |
| Ingestao escrevendo durante dump | inconsistencias | pausa de beat/worker e janela de manutencao |
| Raw payload ainda no Supabase Storage | dependencia residual | aceitavel temporariamente; planejar S3/MinIO depois |
| Auth ainda no Supabase | dependencia residual | aceitavel temporariamente; planejar auth depois |
| VPS compartilhada saturar | indisponibilidade | limites de conexao, pool, monitoramento, backups fora da VPS |

## 8. Ordem recomendada antes das etapas 1-4 do data warehouse

A migracao de banco deve preceder a ativacao produtiva pesada da ingestao recorrente. Ordem recomendada:

1. Planejar/provisionar PostgreSQL VPS.
2. Migrar banco em staging.
3. Fazer cutover controlado.
4. So entao executar DW-1/DW-2 contra a nova fonte de verdade.
5. DW-3/DW-4 podem ser desenvolvidas localmente em paralelo, mas validacao produtiva deve usar PostgreSQL VPS.

## 9. Prompt curto para agente executor

Use este resumo se outro agente for executar a migracao:

> Planeje e implemente em fases a migracao do banco principal da GennomX AI do PostgreSQL Supabase para PostgreSQL/pgvector hospedado na VPS. Leia `AGENTS.md`, `project_state/task_plan.md`, `project_state/plano_migracao_supabase_postgres_vps.md`, `docs/05_SEGURANCA_E_GOVERNANCA.md`, `docs/09_DEPLOY_E_OPERACAO.md`, `.env.example`, `backend/app/config.py`, `infra/docker-compose.yml`, `infra/postgres/init.sql` e `infra/supabase/bootstrap_roles.sql`. Migre primeiro somente o banco, mantendo Supabase Auth/JWKS e Supabase Storage temporariamente. Nao exponha porta 5432 publicamente, nao versionar segredos, nao relaxar RLS/roles, nao executar cutover sem backup/restore testado e aprovacao explicita. Entregue provisioning, bootstrap de roles, dump/restore em staging, validacao de contagens/checksums, ajuste de env/docs, plano de rollback e registro em `project_state/progress.md`/`docs/11_CHANGELOG_DECISOES.md`.
