# PLAN-004 — Onda 2: CI verde após pip-audit

**Status:** em execução
**Criado em:** 2026-09-01 · **Autor:** agente, SIM do fundador (Onda 2)
**Aprovado por:** Marcus em 2026-09-01
**Workstream:** WS-003 · **Nível de risco:** 3
**Decisões relacionadas:** D-008 · **Findings relacionados:** nenhum local

## Objetivo

O `main` no origin tem o job Security Scan verde: `pip-audit -r requirements.lock` sem vulnerabilidades conhecidas em `aiohttp` e `cryptography`.

## Escopo

- **Incluído:** piso em `backend/pyproject.toml` e `backend/_lock_requirements.in`; pinos em `backend/requirements.lock`; lock overlay `federation/protocol/.protocol-lock.json`; eol em `.gitattributes`; `frontend/package.json` e `frontend/package-lock.json`; índice `project_state/WORKSTREAMS.md`; `audits/AUD-002-onda2-ci-pip-audit.md`; `project_state/AUDITS.md`; `project_state/FINDINGS.md`; push; conferência do run GitHub; G13/RC/G14 (T-017).
- **Fora de escopo:** deploy VPS da GennomX AI; ingestão real; ficheiros R2 sujos do checkout paralelo.

## Etapas

| # | Etapa | Vira tarefa |
|---|---|---|
| 1 | Subir aiohttp ≥ 3.14.3 e cryptography ≥ 50.0.0 na origem e no lock | T-014 |
| 3 | Alinhar lock overlay aos bytes LF do git e fixar eol no checkout | T-015 |
| 4 | Fechar npm audit high e mypy/numpy no runner 3.12 | T-016 |
| 5 | G13 verde na janela; RC; G14 humano | T-017 |

## Critérios de validação

- [x] Lock declara aiohttp 3.14.3 → comando: `python -X utf8 -c "print('aiohttp==3.14.3' in open('backend/requirements.lock',encoding='utf-8').read())"`
- [x] Lock declara cryptography 50.0.1 → comando: `python -X utf8 -c "print('cryptography==50.0.1' in open('backend/requirements.lock',encoding='utf-8').read())"`
- [ ] G13 da WS-003 verde no tip → comando: `python -X utf8 -B tools/verify.py --ws WS-003`
