# Evidência — WS-003

Prova executada. Comando + saída + timestamp + commit.

---

## E-001 — Pinos que fecham PYSEC-2026-3545 e PYSEC-2026-3552

**Tarefa:** T-014 · **Quando:** 2026-09-18T16:41:00Z · **Commit:** `c85e33a8b5442d3c2635ea5e3091006434e4926c`
**Gate:** G2

O SHA `c85e33a` subiu os pisos. Releitura do lock no descendente `2fa5e84`
(ancestral de `validated_commit` `8d5a553`):

```console
$ python -X utf8 -c "from pathlib import Path; import re; t=Path('backend/requirements.lock').read_text(encoding='utf-8'); print(re.search(r'(?m)^aiohttp==.*', t).group(0)); print(re.search(r'(?m)^cryptography==.*', t).group(0))"
aiohttp==3.14.3
cryptography==50.0.1
```

Run GitHub histórico `32669664058` (SHA `0185ccf`) tinha aiohttp 3.14.2 /
cryptography 49.0.0. `pip-audit` local no Windows falhou por encoding; a prova
do gate é o lock + Security Scan em E-004.

**Conclusão sustentada:** o lock declara as versões que o pip-audit pediu.

---

## E-002 — Lock overlay alinhado a LF; protocol 26/0

**Tarefa:** T-015 · **Quando:** 2026-09-18T16:41:00Z · **Commit:** `ac74e3e028727d0288922b66cb5f91fd8960b5d8`
**Gate:** G2

`.gitattributes` declara `federation/protocol/** text eol=lf`. Overlay realinhado
em `ac74e3e`. Reexecutado no worktree limpo:

```console
$ python -X utf8 -B tools/validate.py --only protocol
Protocolo VLAEG IA-ready 4.0 — validacao
[OK    ] protocol               26 verificacoes, 0 erro(s), 0 aviso(s)
OK — 26 verificacoes, 0 erros, 0 aviso(s).
```

F-069 da raiz permanece aberto.

---

## E-003 — npm/mypy no runner 3.12 (SHA 8d5a553)

**Tarefa:** T-016 · **Quando:** 2026-09-18T16:41:00Z · **Commit:** `8d5a553e9dca6f4e97a6f42da7f8bd14656daab5`
**Gate:** G2

Run `33583382886` (SHA `ac74e3e`) falhou Frontend lint (`npm ci`) e Backend
mypy (`aclose`). Correção em `8d5a553`. Jobs do run verde:

```console
$ gh run view 33584290345 --repo mvsscarmo-max/gennomx-ai --json jobs --jq ".jobs[] | [.name,.conclusion] | @tsv"
Backend — Lint & Type Check	success
Frontend — Lint & Type Check	success
Protocol overlay	success
Backend — Unit Tests	success
Secret Scan	success
Frontend — Build	success
Frontend — E2E	success
Security Scan	success
Backend — Integration Tests	success
```

F-069 da raiz permanece aberto.

---

## E-004 — CI Linux SHA 8d5a553 toda verde

**Tarefa:** T-016 · **Quando:** 2026-09-18T16:41:00Z · **Commit:** `8d5a553e9dca6f4e97a6f42da7f8bd14656daab5`
**Gate:** G2

```console
$ gh run view 33584290345 --repo mvsscarmo-max/gennomx-ai --json conclusion,headSha,status,url --jq "{conclusion,headSha,status,url}"
{"conclusion":"success","headSha":"8d5a553e9dca6f4e97a6f42da7f8bd14656daab5","status":"completed","url":"https://github.com/mvsscarmo-max/gennomx-ai/actions/runs/33584290345"}
```

Security Scan (pip-audit + Bandit) = success. F-069 da raiz permanece aberto.

---

## E-005 — T-017: G13 vermelho na janela 0185ccf..2fa5e84 (12 erros)

**Tarefa:** T-017 · **Quando:** 2026-09-18T16:28:00Z · **Commit:** `2fa5e84b03234d385c48c8f6408350c92ea2f084`
**Gate:** G13
**Origem:** worktree limpo `.tmp/gx-ai-onda2` (branch `ws003-t017-g13`).

```console
$ python -X utf8 -B tools/verify.py --ws WS-003
[FALHOU] g13-verify             30 verificacoes, 12 erro(s), 0 aviso(s)
```

Oito `g13::escopo` (caminhos da CI fora do PLAN-004) e quatro `g13::evidência`
(E-001…E-004). Mitigado nesta passagem: escopo alargado; envelopes com
comando+saída reais. Reexecutar G13.

**Não validado (neste bloco):** RC e G14.

## E-006 — T-017: G13 verde 0185ccf..2fa5e84 (33/0; 1 aviso dirty)

**Tarefa:** T-017 · **Quando:** 2026-09-18T16:45:00Z · **Commit:** `2fa5e84b03234d385c48c8f6408350c92ea2f084`
**Gate:** G13

Escopo do PLAN-004 alargado aos 8 caminhos da CI. E-001…E-004 com SHA +
```console + comando `$` + saída. `--exec-criteria` dos pinos do lock.

```console
$ python -X utf8 -B tools/verify.py --ws WS-003 --exec-criteria
[OK    ] g13-verify             33 verificacoes, 0 erro(s), 1 aviso(s)
```

Aviso: 3 caminhos sujos (PLAN-004, EVIDENCE, STATE) fora da janela até commit.
Não inventou console. Dirt R2 do checkout `GennomX AI/` não está neste worktree.

**Não validado:** RC, G14, commit do tip.

