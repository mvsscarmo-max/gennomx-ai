# PLAN-002 — Adoção do AI Ready First 4.0.0

**Status:** concluído
**Criado em:** 2026-08-21 · **Autor:** Cursor
**Aprovado por:** Marcus em 2026-08-21 (T-207 / PLAN-024 da raiz)
**Workstream:** WS-001 · **Nível de risco:** 3
**Decisões relacionadas:** D-007 · **Findings relacionados:** —

## Objetivo

A GennomX AI opera sob AI Ready First 4.0.0, com `AGENTS.md` residente enxuto, contrato de produto em `docs/rules/` e validadores verdes.

## Escopo

- **Incluído:** protocolo, estado, bundle federado, realocação do AGENTS.md longo
- **Fora de escopo:** ingestão real, deploy VPS, DRY-6 / INGEST-5


Arquivos previstos (G13/G6): `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `CHANGELOG.md`, `README.md`, `.agents/`, `docs/`, `docs/ai-ready/`, `docs/legacy/`, `tools/`, `federation/`, `project_state/`, `audits/`, `tests/`, `architecture/`, `backend/`, `protocolo_vlaeg_otimizado.md`.

## Abordagem técnica

Brownfield pelo Kit 4.0.2; produto permanece em `docs/rules/contrato-operacional.md`.

## Etapas

| # | Etapa | Arquivos previstos | Vira tarefa |
|---|---|---|---|
| 1 | Instalar 4.0 e registrar estado | AGENTS.md, docs/rules/, federation/protocol/ | T-012 |

## Skills previstas

| Skill | Etapa | Por quê |
|---|---|---|
| writing-agents-md | 1 | cortar AGENTS.md residente |

## Critérios de validação

- [x] Validador local verde → comando: `python tools/validate.py` → evidência esperada: 0 erros
- [x] Smoke da adoção 4.0 → comando: `python -B -m unittest tests.test_ia_ready_adoption` → evidência esperada: OK
- [ ] Bundle federado instalado → comando: `python federation/protocol/core/protocol.py verify --root federation/protocol` → evidência esperada: status verified

## Gates aplicáveis

G1, G5, G7, G8, G9, G10, G13, RC, G14.

## Riscos e mitigação

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Perder tripwire de produto no corte do AGENTS | média | alto | contrato operacional preservado em docs/rules/ |

## Fases VLAEG

| Fase | Estado | Entregável |
|---|---|---|
| V — Visão | aplicável | T-207 |
| A — Arquitetura | aplicável | núcleo 4.0 |
| G — Gatilho | obrigatória por risco | RC/G14 locais |
