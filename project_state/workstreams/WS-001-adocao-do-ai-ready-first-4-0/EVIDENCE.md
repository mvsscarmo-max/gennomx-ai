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

**Resumo (1–3 frases):** AGENTS.md residente caiu de ~17.9k para 4.034 caracteres. Contrato de produto permanece em `docs/rules/`. Sem commit nesta sessão.

---


## E-004 — G13 no tip da adoção 4.0

**Tarefa:** T-012 · **Quando:** 2026-08-21T21:01:45Z · **Commit:** `d008aef9ee74938e633d0576331f04649aca088f`
**Gate:** G13
**Worktree:** `C:/Users/marcu/Desktop/Projetos IA/worktrees-t207/gennomx-ai`

```console
$ git rev-parse HEAD
d008aef9ee74938e633d0576331f04649aca088f

$ python -X utf8 -B tools/verify.py --ws WS-001 --exec-criteria
G13 ÔÇö verifica├º├úo diferencial
raiz: C:\Users\marcu\Desktop\Projetos IA\worktrees-t207\gennomx-ai

[OK    ] g13-verify             352 verificacoes, 0 erro(s), 0 aviso(s)
```

**Conclusão sustentada:** G13 verde neste SHA (352 verificações, 0 erros). Não prova RC/G14 desta WS nem validador 100% verde (findings locais).

---

## E-005 — G13 após correção da AUD-001

**Tarefa:** T-012 · **Quando:** 2026-08-21T23:47:30Z · **Commit:** `83fa67bf0f57e3bf413920d50ef19afc2019aa46`
**Gate:** G13

```console
$ git rev-parse HEAD
83fa67bf0f57e3bf413920d50ef19afc2019aa46

$ python -X utf8 -B tools/verify.py --ws WS-001 --exec-criteria
[OK    ] g13-verify             378 verificacoes, 0 erro(s), 0 aviso(s)

$ python -B -m unittest tests.test_ia_ready_adoption
Ran 5 tests in 0.485s
OK

$ python -X utf8 -B tools/validate.py
OK — 1171 verificacoes, 0 erros, 3 aviso(s).
```

**Conclusão sustentada:** G13 verde no tip que contém as correções R-01…R-04. Os avisos de paridade no `validate.py` sem `--exec-criteria` não são erro; o smoke e o validador rodaram nesta passagem do G13.

---

## E-006 — G14 aceite humano (WS-001)

**Tarefa:** T-012 · **Quando:** 2026-08-21T23:48:00Z · **Commit:** `83fa67bf0f57e3bf413920d50ef19afc2019aa46`
**Gate:** G14
**Assinante:** Marcus (fundador)
**RC:** AUD-001
**G13:** E-005
**Decisão:** ACEITO
**Veredito:** ACEITO
**Ressalvas:**
- AUD-001 R-01…R-04 corrigidos nesta WS e verificados por G13 em `83fa67b`.
- Fast-forward de `main` ainda pendente após este fechamento.

**Autorizacao nesta sessao:** "Continue. Invoque gpt SOL para RC. Aceito G14."

```console
$ git rev-parse HEAD
83fa67bf0f57e3bf413920d50ef19afc2019aa46
```

A workstream opera em worktree paralela `ws-t207-ia-ready-4.0`. Merge na destinação (`main`) sugerido por FF após este fechamento.

**Conclusão sustentada:** o fundador leu o resumo do diff da adoção 4.0, o G13 e a RC AUD-001; aceitou. Agente transcreveu o aceite; nao assinou.

## Não provado

- Fast-forward de `main` após este fechamento.
- `python federation/protocol/core/protocol.py verify` — bundle-drift (`tests/test_protocol.py` ausente).

