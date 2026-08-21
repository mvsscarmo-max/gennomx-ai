# Evidência — WS-001

Prova executada. Comando + saída + timestamp + commit.

---

## E-001 — Kit 4.0.2 instalado e bundle federado 1.0.0 presente

**Tarefa:** T-012 · **Quando:** 2026-08-21T20:16:31Z · **Commit:** `f4cd794f2e92bb96f2ab33c38825c57b396aa936` (base; tip sujo)
**Gate:** G1

```console
$ python -B scripts/vlaeg_init.py --root <worktree> --name "GennomX AI"
86 a criar, 3 ja existentes (preservados).

$ python federation/protocol/core/protocol.py install --target federation/protocol --source-commit d2cd2941686748dc1752e6bdabd70bfdb4c73e64
{"bundleDigest": "sha256:5703c899a6dac0f44dedf69b29558f58a63eceacf0e2ac0b45c1fa02cff95898", "status": "installed", "protocolVersion": "1.0.0"}
```

**Conclusão sustentada:** núcleo 4.0.2 e lock federado instalados. AGENTS.md longo foi relocado para `docs/rules/contrato-operacional.md`.

---

## E-002 — `python tools/validate.py` após marcar arquivo histórico

**Tarefa:** T-012 · **Quando:** 2026-08-21T20:33:00Z · **Commit:** `f4cd794f2e92bb96f2ab33c38825c57b396aa936`
**Gate:** G1

```console
$ python tools/validate.py --root <worktree>
[OK    ] estado
[FALHOU] ai-ready  13 erro(s)
[FALHOU] links     9 erro(s)
FALHOU — 22 erro(s), 1 aviso(s) em 789 verificacoes.
```

Antes de `validate-links: illustrative-paths` no arquivo: 237 erros (224 de links). Triagem: F-006.

---

## E-003 — Gate G5 (deslop)

**Tarefa:** T-012 · **Quando:** 2026-08-21T20:40:00Z · **Commit:** `none`
**Gate:** G5

**Resumo:** AGENTS.md residente caiu de ~17.9k para 4.034 caracteres. Contrato de produto permanece em `docs/rules/`. Sem commit nesta sessão.

---

## Não provado

- Commit da branch. G13 no tip. Pytest/frontend. RC e G14.
