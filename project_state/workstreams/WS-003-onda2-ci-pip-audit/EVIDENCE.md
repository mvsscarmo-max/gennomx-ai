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

---

## E-007 — G5: deslop não aplicável (só estado/plano)

**Tarefa:** T-017 · **Quando:** 2026-09-18T16:52:36Z · **Commit:** `3bfbb43dc612ab18e3c659ba7fbde129a918e8a9`
**Gate:** G5
**Resumo (1–3 frases):** Diff só de PLAN-004 e STATE/EVIDENCE. Skill deslop não
aplica a documentação. Nenhum slop de código a remover.

Diff desta passagem: `PLAN-004` (status `em execução`) e `STATE.md` (origem
PLAN-004 em T-017, `pending_gates`, `current_commit`). Sem código de produto.
Skill `deslop` tem gatilho negativo para diff só de documentação: não há
comentário, cast, defesa nem aninhamento a remover.

`validate.py` nesta árvore: 883/0.

```console
$ python -X utf8 -B tools/validate.py
OK — 883 verificacoes, 0 erros, 0 aviso(s).
```

**Conclusão sustentada:** G5 cumprido por inaplicabilidade documentada, não por
limpeza de slop de código.

---

## E-008 — T-017: G13 verde no tip 60eaf62 (33/0/0)

**Tarefa:** T-017 · **Quando:** 2026-09-18T16:56:00Z · **Commit:** `60eaf628746397d977596fe79373197f8e8d8ef0`
**Gate:** G13

Árvore limpa após o commit de PLAN-004 `em execução` e G5.

```console
$ python -X utf8 -B tools/verify.py --ws WS-003 --exec-criteria
G13 — verificação diferencial
raiz: C:\Users\marcu\Desktop\Projetos IA\Criação de sites\New GennonX Claude 2.0\.tmp\gx-ai-onda2

[OK    ] g13-verify             33 verificacoes, 0 erro(s), 0 aviso(s)
```

```console
$ python -X utf8 -B tools/validate.py
OK — 887 verificacoes, 0 erros, 0 aviso(s).
```

**Não validado (neste bloco):** RC e G14.

---

## E-009 — T-017: RC AUD-002 (OpenCode GPT 5.6 SOL)

**Tarefa:** T-017 · **Quando:** 2026-09-18T17:03:53Z · **Commit:** `60eaf628746397d977596fe79373197f8e8d8ef0`
**RC:** AUD-002
**Motor:** opencode/openai/gpt-5.6-sol · effort high · `--pure` · sem `--auto`
**Independência:** cursor/grok-4.6 → opencode/openai/gpt-5.6-sol
**Artefato:** `audits/AUD-002-onda2-ci-pip-audit.md`
**Veredito:** FIX_BEFORE_SHIP
**patch_sha256:** `be53bcf76e31ab89fc7d9592b9a80272dbfc1846a0fa392da1ab2f82436403ef`

Pré-voo: janela completa 12 arquivos / 1527 linhas (teto 1500). Fatia enviada:
11 arquivos / 513 linhas; omitido `frontend/package-lock.json` (listado no
prompt). O revisor leu o lock no disco (cita linhas 1513 e 4857).

```console
$ python -X utf8 -B tools/review/run_engine.py --stdout project_state/workstreams/WS-003-onda2-ci-pip-audit/_inflight/rc/rc.stdout.log --stderr project_state/workstreams/WS-003-onda2-ci-pip-audit/_inflight/rc/rc.stderr.log --meta project_state/workstreams/WS-003-onda2-ci-pip-audit/_inflight/rc/run-engine.json --cwd . -- opencode run --model openai/gpt-5.6-sol --variant high --pure --dir .
classificacao: OK
elapsed:       401.219s
stdout/stderr: 40B / 131093B
exit:          0
```

Achados: R-01 e R-02 classe `contrato` (não crítico / não prova-obrigatória).
Triagem: F-007 e F-008. Destino (corrigir nesta WS ou D-NNN+prazo) pendente de
Marcus. Agente não assina G14.

**Não validado:** G14.

---

## E-010 — T-017: AUD-002 R-01/R-02 corrigidos no lock

**Tarefa:** T-017 · **Quando:** 2026-09-18T17:22:14Z · **Commit:** `dbd127ccca3ce099d805e15f9a645c6fc78dc32a`
**Gate:** G2 / G4 / G5
**Resumo (1–3 frases):** Override de `brace-expansion` passou a `brace-expansion@1` →
`1.1.18`, e o lock guarda `5.0.12` sob `minimatch@10.2.5`. `sharp` subiu a
`0.35.4` na faixa do Next. `js-yaml` 4.3.2 fecha GHSA-2883 no mesmo pin.
JSON sem comentário nem defesa extra.

Causa raiz (R-01/R-02): override global forçava versão fora da faixa do
consumidor. Correção: restringir o 1.x e pinos compatíveis, não calar o audit.

```console
$ npm ci
added 399 packages, and audited 400 packages in 1m
found 0 vulnerabilities
```

```console
$ npm audit --audit-level=moderate
found 0 vulnerabilities
```

```console
$ npm run lint
lint_exit=0
```

```console
$ npm run typecheck
typecheck_exit=0
```

```console
$ npm run build
▲ Next.js 15.5.25
✓ Compiled successfully in 11.8s
✓ Generating static pages (13/13)
build_exit=0
```

```console
$ npm run test:e2e
Running 7 tests using 6 workers
  7 passed (21.6s)
e2e_exit=0
```

Lock: `node_modules/brace-expansion` 1.1.18;
`node_modules/@typescript-eslint/typescript-estree/node_modules/brace-expansion` 5.0.12;
`node_modules/sharp` 0.35.4.

**Conclusão sustentada:** contratos de minimatch e Next restaurados; audit 0.
F-007 e F-008 resolvidos neste SHA.

