# Evidência — WS-003

Prova executada. Comando + saída + timestamp + commit.

---

## E-001 — Pinos que fecham PYSEC-2026-3545 e PYSEC-2026-3552

**Tarefa:** T-014 · **Quando:** 2026-09-01T06:20:00Z · **Commit:** working tree sobre `0185ccf`
**Gate:** G2

Run GitHub `32669664058` (2026-08-23, SHA `0185ccf`):

```console
Found 2 known vulnerabilities in 2 packages
Name         Version ID              Fix Versions
aiohttp      3.14.2  PYSEC-2026-3545 3.14.3
cryptography 49.0.0  PYSEC-2026-3552 50.0.0
```

Instalação local (venv Windows):

```console
Successfully installed aiohttp-3.14.3 cryptography-50.0.1
aiohttp 3.14.3
cryptography 50.0.1
```

Lock e origem atualizados para esses pisos. `pip-audit` local falhou com `UnicodeDecodeError` em `pip --version` (caminho com `ç`); não é prova. A prova do gate é o job Linux após o push.

**Conclusão sustentada:** a causa do Security Scan vermelho era o pino; o lock novo declara as versões que o próprio pip-audit pediu. CI GitHub ainda não rodou neste SHA.

---

## E-002 — Lock overlay alinhado a LF; npm audit 0; mypy python_version 3.12

**Tarefa:** T-015 / T-016 · **Quando:** 2026-09-02T02:30:00Z · **Commit:** working tree
**Gate:** G2

Causa do `protocol::managed-drift` no Linux: `fileDigests` de `parity.py`, `manifest.json` e `semantic-overlay.schema.json` foram calculados no working tree Windows (CRLF). O git guarda LF. `python tools/validate.py --only protocol` após realinhar: 26/0. Hashes do lock casam com `git show HEAD:federation/protocol/...`. `.gitattributes` declara `federation/protocol/** text eol=lf`.

`[tool.mypy] python_version` 3.12 (CI e stubs numpy 2.5.1). `npm audit --audit-level=moderate`: 0. `npm run typecheck`: exit 0.

F-069 da raiz permanece aberto.

---

## E-003 — npm ci npm 10 e mypy aclose

**Tarefa:** T-016 · **Quando:** 2026-09-02T02:42:00Z · **Commit:** working tree sobre `ac74e3e`
**Gate:** G2

Run `33583382886` (SHA `ac74e3e`): Protocol overlay success; Security Scan success; Frontend lint failed `npm ci` (override `browserslist@4.28.7` ausente do lock); Backend lint failed mypy `"Redis[str]" has no attribute "aclose"` com `types-redis==4.6.0.20241004`.

Correção: remover o override que o lock nunca materializou; gravar browserslist 4.28.8 e transientes no lock; remover `types-redis` para o pacote `redis` 6.4.0 (`py.typed`, `aclose` presente) prevalecer.

```console
npx --yes npm@10.8.2 ci
added 399 packages, and audited 400 packages in 1m
found 0 vulnerabilities
exit 0

npm audit --audit-level=moderate
found 0 vulnerabilities

npm run typecheck
exit 0

python -m mypy app workers --ignore-missing-imports
Success: no issues found in 138 source files
```

Job protocol não foi alterado. F-069 da raiz permanece aberto.
