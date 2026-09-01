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
