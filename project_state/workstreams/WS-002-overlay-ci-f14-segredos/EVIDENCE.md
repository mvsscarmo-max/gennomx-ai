# Evidência — WS-002

Prova executada. Comando + saída + timestamp. Resumo não é evidência.

---

## E-001 — Overlay 1.1.0 e sourceCommit

**Tarefa:** T-013 · **Quando:** 2026-08-23T16:42:52Z · **Base:** `8c96715e9efaca04c4754674d5851fdc60250e27`

Lock: `federation/protocol/.protocol-lock.json`
- protocolVersion: 1.1.0
- source: federation/protocol
- sourceCommit: `966f159683f4586f0b937d45f694dac5983fdd73` (40 hex da raiz)

Campos proibidos do overlay (autoridade humana / privacidade) não foram escritos.

---

## E-002 — Validadores e testes

**Quando:** 2026-08-23T16:46:13Z

\\console
\$ python tools/validate.py --only protocol
[OK    ] protocol               26 verificacoes, 0 erro(s), 0 aviso(s)

\$ backend/.venv/Scripts/python.exe -m pytest tests/unit/test_postgres_vps_artifacts.py -q
...  (exit 0)
\
Deslop: action composta so encapsula setup-python + pip lock; jobs continuam paralelos.


## E-003 — F1.x (sem valores de segredo)

### GennomX AI F1.4 (caminho / categoria / acao)

| Caminho | Categoria | Acao |
|---|---|---|
| backend/app/auth/dependencies.py | falso positivo | le settings; nao ha segredo literal |
| backend/app/services/llm/service.py | falso positivo | le env em runtime; nao ha valor versionado |
| backend/tests/unit/test_postgres_vps_artifacts.py | fixture | assere placeholder psql |
| infra/postgres/bootstrap_roles_vps.sql | fixture | senha so via variavel psql |
| tres arquivos de ambiente ignorados | nao lidos | se fossem reais: parar e rotacionar com humano |

