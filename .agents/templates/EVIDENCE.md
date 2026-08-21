# Evidência — WS-NNN

Prova executada. Comando + saída + timestamp + commit. Faltando qualquer um dos quatro, é
hipótese, não evidência.

Resumo não é evidência. Saída capturada antes da última alteração é `historical`.

---

## E-001 — <o que foi provado>

**Tarefa:** T-NNN · **Quando:** AAAA-MM-DDTHH:MM:SSZ · **Commit:** `<sha>`
**Gate:** G<NN>

```console
$ <comando exato>
<saída verbatim, não parafraseada>
```

**Conclusão sustentada:** <o que esta saída prova — e só isso>

---

## E-002 — <regressão: vermelho antes, verde depois>

**Tarefa:** T-NNN · **Quando:** AAAA-MM-DDTHH:MM:SSZ · **Commit:** `<sha depois>`

**Commit antes:** `<sha antes>`

Antes da correção:

```console
$ <comando>
FAILED ... <a falha que o bug causa>
```

Depois da correção:

```console
$ <comando>
PASSED
```

**Conclusão sustentada:** o teste falhava por causa do bug e passa por causa da correção.

---

## E-003 — Gate G5 (deslop)

**Tarefa:** T-NNN · **Quando:** AAAA-MM-DDTHH:MM:SSZ · **Commit:** `<sha>`
**Gate:** G5

```console
$ git diff --check
<saída verbatim>
```

**Resumo (1–3 frases):** <o que foi removido do diff>

---

## Não provado

O que foi feito e **não** tem evidência aqui:

- <item> — <por que não foi possível provar>

Este bloco é obrigatório e não fica vazio por otimismo. Ele alimenta `not_validated` do handoff.
