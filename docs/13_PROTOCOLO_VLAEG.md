# 13 — Protocolo VLAEG 2.0 aplicado à GennomX AI

Este documento adota formalmente o **Protocolo VLAEG 2.0** (`../../protocolo_vlaeg_2.0.md`) como framework operacional padrão da GennomX AI.

> **Fonte normativa do protocolo:** `../protocolo_vlaeg_2.0.md` (workspace raiz).
> **Fonte normativa operacional do projeto:** `AGENTS.md` (raiz).
> Em caso de conflito, a premissa central do `AGENTS.md` (§1) prevalece: a GennomX AI é infraestrutura de dados + MCP, não geradora final de relatórios.

---

## 1. Por que adotar o VLAEG

A GennomX AI já é um sistema maduro e já satisfaz, intrinsecamente, vários princípios do VLAEG (dados primeiro, lógica determinística, fonte única da verdade, documentação como arquitetura, segurança desde o início). A adoção do VLAEG **não reinicia o projeto**: ela adiciona uma camada explícita de rastreabilidade de processo (fases V‑L‑A‑E‑G), formaliza contratos de dados e declarações de automação, e expõe lacunas concretas de engenharia que são corrigidas de forma incremental.

O VLAEG passa a ser o protocolo de referência **antes de iniciar qualquer novo módulo, conector, ferramenta MCP, automação ou agente**.

---

## 2. Mapeamento de fases V‑L‑A‑E‑G → artefatos da GennomX AI

| Fase | Finalidade VLAEG | Onde vive na GennomX AI | Status |
|---|---|---|---|
| **V — Visão** | Problema, objetivo, usuários, fonte da verdade, entrada/saída, critério de sucesso | `docs/00_CONTEXTO_ESTRATEGICO.md`, `docs/08_ROADMAP.md` (§22 critérios de sucesso) | ✅ Consolidado |
| **L — Link** | Validar conectividade, APIs, credenciais, webhooks antes da lógica | `docs/03_FONTES_E_INGESTAO.md` (matriz Link), `tools/handshake.py`, `BaseConnector.healthcheck()` | 🟡 Em adoção |
| **A — Arquitetura** | Módulos, responsabilidades, modelo de dados, fluxos, regras determinísticas | `docs/01_ARQUITETURA.md`, `docs/02_MODELO_DE_DADOS.md`, `architecture/POP_*.md`, código `backend/` | ✅ Consolidado |
| **E — Estilo** | UX, interface, apresentação dos dados, qualidade da entrega | `docs/07_DASHBOARD_UX.md`, `frontend/src/**` | ✅ Consolidado |
| **G — Gatilho** | Automações, agendamentos, webhooks, monitoramento, operação contínua | `docs/09_DEPLOY_E_OPERACAO.md` (declarações de automação), `backend/workers/celery_app.py` (`beat_schedule`) | 🟡 Em adoção |

### Princípios fundamentais (seção 3 do VLAEG)

| Princípio VLAEG | Onde é atendido | Observação |
|---|---|---|
| 3.1 Dados primeiro / contrato de dados | `docs/03` (por conector) e `docs/04` (por ferramenta MCP) | Contratos `{input, processamento, output}` formalizados |
| 3.2 Lógica de negócio determinística | `AGENTS.md` §9; workers/parsers/normalizers; validação por schema | LLM sugere, schema valida, pipeline persiste |
| 3.3 Fonte única da verdade | `AGENTS.md` §10 (ordem de ingestão); `docs/03` | Precedência: API oficial → export → upload → MCP externo → scraping |
| 3.4 Documentação como arquitetura | `docs/**`, `AGENTS.md`, `project_state/` | Documentação viva e versionada |
| 3.5 Autocorreção estruturada | `docs/09_DEPLOY_E_OPERACAO.md` (runbook) | Ciclo analisar→isolar→corrigir→testar→documentar→prevenir |

---

## 3. Mapeamento de documentação: estrutura VLAEG → docs GennomX

O VLAEG sugere `docs/00–08`. A GennomX AI mantém uma estrutura **mais granular** (`docs/00–13`), que é um superset do esquema VLAEG. Esta tabela preserva a equivalência sem renumerar.

| Doc VLAEG (Etapa 0) | Documento equivalente na GennomX AI |
|---|---|
| `docs/00_CONTEXTO_ESTRATEGICO.md` | `docs/00_CONTEXTO_ESTRATEGICO.md` |
| `docs/01_ARQUITETURA.md` | `docs/01_ARQUITETURA.md` (+ `docs/02_MODELO_DE_DADOS.md`, `docs/12_STACK_TECNOLOGICA_REFINADA.md`) |
| `docs/02_SEGURANCA_E_GOVERNANCA.md` | `docs/05_SEGURANCA_E_GOVERNANCA.md` |
| `docs/03_TESTES_E_QUALIDADE.md` | `docs/06_TESTES_E_QUALIDADE.md` |
| `docs/04_DASHBOARD_UX.md` | `docs/07_DASHBOARD_UX.md` |
| `docs/05_ROADMAP.md` | `docs/08_ROADMAP.md` |
| `docs/06_DEPLOY_E_OPERACAO.md` | `docs/09_DEPLOY_E_OPERACAO.md` |
| `docs/07_GLOSSARIO.md` | `docs/10_GLOSSARIO.md` |
| `docs/08_CHANGELOG_DECISOES.md` | `docs/11_CHANGELOG_DECISOES.md` |
| — (sem equivalente VLAEG) | `docs/03_FONTES_E_INGESTAO.md`, `docs/04_MCP_TOOLS.md` (específicos do domínio) |
| `architecture/` | `architecture/POP_ingestao.md`, `architecture/POP_mcp_tool.md` |
| `tools/` | `tools/` (scripts determinísticos: handshake, checagens) |
| Estado VLAEG 2.0 | `project_state/{CONTEXT,DECISIONS,TASKS,FINDINGS,PROGRESS}.md` + `project_state/plans/` |

---

## 4. Como aplicar o VLAEG em novas mudanças

Antes de iniciar qualquer novo conector, ferramenta MCP, automação ou módulo:

1. **V — Visão:** registrar problema, fonte da verdade, entrada/saída e critério de sucesso em um plano de `project_state/plans/` e em `TASKS.md`.
2. **L — Link:** validar conectividade com `tools/handshake.py` (ou um novo healthcheck) **antes** de construir a lógica. Não desenvolver lógica final sobre integração não testada.
3. **A — Arquitetura:** seguir o POP aplicável em `architecture/` e atualizar `docs/01`/`docs/02`/`docs/03`/`docs/04`.
4. **E — Estilo:** quando houver interface, seguir `docs/07_DASHBOARD_UX.md`.
5. **G — Gatilho:** declarar a automação (template em `docs/09`) e, se agendada, registrar no `beat_schedule` do Celery.

Toda mudança relevante deve: ser pequena e reversível (`AGENTS.md` §14), atualizar documentação e testes junto ao código, e registrar decisão em `docs/11_CHANGELOG_DECISOES.md`.

---

## 5. Estado de execução (project_state)

O rastreamento de execução do projeto vive em `project_state/`:

- `project_state/CONTEXT.md` — snapshot oficial e plano ativo.
- `project_state/DECISIONS.md` — decisões vigentes identificadas.
- `project_state/TASKS.md` — tarefas vivas e seus critérios.
- `project_state/plans/` — planos propostos, aprovados, ativos ou concluídos.
- `project_state/FINDINGS.md` — achados e bloqueios vigentes.
- `project_state/PROGRESS.md` — histórico de execução VLAEG 2.0.
- `project_state/archive/v1/` — estado e planos v1 preservados, sem edição.
