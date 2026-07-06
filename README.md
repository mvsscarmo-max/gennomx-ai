# GennomX AI

A **GennomX AI** é uma aplicação empresarial para estruturar, governar e disponibilizar inteligência biomédica e competitiva por meio de banco de dados proprietário, pipelines de ingestão, dashboard, API e servidor MCP.

A aplicação **não** deve ser tratada como um chatbot ou gerador final de relatórios. Ela fornece dados estruturados, evidências e ferramentas para que modelos host externos — como ChatGPT, Claude e agentes privados — produzam análises e relatórios fora da aplicação.

---

## Visão geral

A GennomX AI resolve a fragmentação de informações críticas em life sciences, integrando fontes como registros de ensaios clínicos, bases regulatórias, literatura científica, bulas, congressos, press releases, investor decks e pipelines corporativos.

O objetivo é formar uma infraestrutura proprietária com:

- ingestão contínua de dados;
- normalização e deduplicação de entidades;
- rastreabilidade entre dado, fonte e evidência;
- banco relacional estruturado;
- dashboard operacional;
- API interna;
- servidor MCP para modelos de IA host;
- segurança, logs, testes e governança desde o MVP.

---

## Estrutura da documentação

```txt
/
├─ AGENTS.md
├─ README.md
├─ CLAUDE.md
├─ GEMINI.md
└─ docs/
   ├─ 00_CONTEXTO_ESTRATEGICO.md
   ├─ 01_ARQUITETURA.md
   ├─ 02_MODELO_DE_DADOS.md
   ├─ 03_FONTES_E_INGESTAO.md
   ├─ 04_MCP_TOOLS.md
   ├─ 05_SEGURANCA_E_GOVERNANCA.md
   ├─ 06_TESTES_E_QUALIDADE.md
   ├─ 07_DASHBOARD_UX.md
   ├─ 08_ROADMAP.md
   ├─ 09_DEPLOY_E_OPERACAO.md
   ├─ 10_GLOSSARIO.md
   ├─ 11_CHANGELOG_DECISOES.md
   └─ 12_STACK_TECNOLOGICA_REFINADA.md
```

---

## Stack aprovada para MVP

- **Next.js** para dashboard web analítico;
- **Vercel ou Netlify** para hospedagem inicial do frontend;
- **FastAPI** para API interna, endpoints administrativos e servidor MCP;
- **Celery + Redis** para jobs assíncronos no MVP;
- **DuckDB nos workers** para processamento local/batch e validações pesadas;
- **Supabase/PostgreSQL** como banco principal;
- **Supabase Auth** para autenticação inicial;
- **Supabase Storage ou S3-compatible storage** para arquivos brutos, PDFs e snapshots;
- **PostgreSQL full-text search** para busca textual inicial;
- **pgvector** em MVP avançado/fase 2;
- **LiteLLM** como gateway de modelos de IA, com roteamento por criticidade, custo e validação por schema;
- **Servidor MCP interno read-only** no MVP.

A decisão completa está em `docs/12_STACK_TECNOLOGICA_REFINADA.md`.

---

## Banco Supabase

O backend usa SQLAlchemy/Alembic diretamente contra o PostgreSQL da Supabase. Para ambiente
hospedado, configure no `.env`:

- `DATABASE_URL`: runtime FastAPI com role `gennomx_app`, preferencialmente via pooler Supabase.
- `WORKER_DATABASE_URL`: Celery/workers com role `gennomx_worker`, também via pooler.
- `DATABASE_URL_SYNC`: Alembic com role `gennomx_migrator`, preferencialmente via direct
  connection.

Antes das migrações, execute `infra/supabase/bootstrap_roles.sql` no SQL Editor da Supabase após
trocar os placeholders de senha. Depois rode as migrações a partir de `backend`:

```bash
alembic upgrade head
```

As URLs Supabase com `sslmode=require` são aceitas no `.env`; o backend converte automaticamente
para o formato esperado pelo driver asyncpg.

---

## Leitura obrigatória antes de desenvolver

1. `AGENTS.md`
2. `docs/00_CONTEXTO_ESTRATEGICO.md`
3. `docs/01_ARQUITETURA.md`
4. Documentação específica da área a ser alterada.

---

## Status

Documentação reorganizada a partir dos documentos originais de contexto e plano de implementação da GennomX AI.

Os arquivos originais foram preservados em:

```txt
docs/_fontes_originais/
```
