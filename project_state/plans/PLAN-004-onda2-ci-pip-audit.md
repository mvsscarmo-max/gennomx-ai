# PLAN-004 — Onda 2: CI verde após pip-audit

**Status:** aprovado · **Criado em:** 2026-09-01 · **Autor:** agente, SIM do fundador (Onda 2)
**Aprovado por:** Marcus em 2026-09-01
**Workstream:** WS-003 · **Nível de risco:** 3
**Decisões relacionadas:** D-008 · **Findings relacionados:** nenhum local

## Objetivo

O `main` no origin tem o job Security Scan verde: `pip-audit -r requirements.lock` sem vulnerabilidades conhecidas em `aiohttp` e `cryptography`.

## Escopo

- **Incluído:** piso de versão em `pyproject.toml` / `_lock_requirements.in`; pinos em `requirements.lock`; push; conferência do run GitHub.
- **Fora de escopo:** deploy VPS da GennomX AI; RC de julgamento (escape INFRA D-008 permanece); ingestão real.

## Etapas

| # | Etapa | Vira tarefa |
|---|---|---|
| 1 | Subir aiohttp ≥ 3.14.3 e cryptography ≥ 50.0.0 na origem e no lock | T-014 |
| 3 | Alinhar lock overlay aos bytes LF do git e fixar eol no checkout | T-015 |
| 4 | Fechar npm audit high e mypy/numpy no runner 3.12 | T-016 |

## Critérios de validação

- Lock declara `aiohttp==3.14.3` e `cryptography==50.0.1` (ou superior que feche PYSEC-2026-3545 e PYSEC-2026-3552).
- Run `CI` no GitHub no SHA empurrado: job Security Scan sucesso.
