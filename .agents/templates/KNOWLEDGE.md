---
id: K-NNN
title: ""
destination: gotchas      # rules | decisions | procedures | gotchas | experiments | historical
origin: F-NNN             # o finding de onde veio
evidence: ""              # EVIDENCE.md#E-NNN ou comando e saída
workstream: WS-NNN
authority: verified-knowledge   # normative | approved-decision | verified-knowledge | hypothesis
validity: ""              # a que contexto se aplica: stack, versão, ambiente
approved_by: ""           # obrigatório para rules e decisions — sempre humano
verified_at: ""           # AAAA-MM-DD — data em que a evidência foi revalidada
supersession_conditions: ""     # o que faria isto deixar de valer
status: candidate         # candidate | active | superseded
superseded_by: null
---

# K-NNN — <título>

## O que se aprendeu

<enunciado acionável, não narrativa da investigação>

## Por que vale além da tarefa

<o que se repetiria sem este conhecimento registrado>

## Evidência

<comando, saída e commit — ou o ponteiro para EVIDENCE.md>

## Quando deixa de valer

<condição de supersessão explícita>

Conhecimento que não sabe dizer quando deixa de valer vira sedimento. Este campo é obrigatório.

## Aplicação

<como usar isto na prática: o que fazer diferente a partir de agora>

---

<!--
Funil: evento → evidência → finding → candidato → revisão → aprovação → ativo.

Aprovação humana obrigatória para destino `rules` e `decisions`.
Auto-improvement produz proposta; nunca altera automaticamente regra normativa, política de
segurança, decisão arquitetural aprovada, limite de autonomia ou gate.

Supersessão nunca apaga: marca `status: superseded`, preenche `superseded_by` e move para
knowledge/historical/ mantendo o ID.

Candidato não aprovado em 90 dias expira para historical/ com o motivo — a não promoção também
é conhecimento.
-->
