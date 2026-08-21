---
name: knowledge-promotion
description: Conduz o aprendizado verificado de finding a conhecimento ativo, com destino, autoridade e condição de supersessão declarados, e faz a curadoria do que envelheceu. Use quando um finding vale além da tarefa atual, ao propor regra, procedimento ou armadilha reutilizável, e ao revisar conhecimento obsoleto. Não use para transformar transcrição, resumo ou saída de agente em regra sem revisão humana.
metadata:
  protocol: VLAEG AI Ready First
  layer: memory
  version: 1.0.0
  source: "pipeline de promoção derivado de akitaonrails.com/2026/07/20, sem sandbox"
  adapted: true
  risk: high
  vlaeg_phases: [cross-cutting]
  triggers:
    - "finding verificado que vale além da tarefa"
    - "propor regra, procedimento ou gotcha reutilizável"
    - "revisar conhecimento envelhecido ou substituído"
  negative_triggers:
    - "transformar transcrição ou resumo em regra"
    - "alterar automaticamente regra normativa, política de segurança, decisão aprovada, limite de autonomia ou gate"
  produces: ["candidato em knowledge/candidates/", "conhecimento ativo no destino", "marcação de supersessão"]
  gates: ["G10"]
---

# Promoção de conhecimento

Nem tudo que um agente descobre merece sobreviver, e nada vira regra automaticamente. Este é o
funil que separa uma observação de uma restrição vinculante.

```
evento → evidência → finding → candidato → revisão → aprovação
→ conhecimento ativo → regra | decisão | procedimento | gotcha
```

## Pré-condição

Só entra no funil o que já é `evidence`: comando executado, saída observada, commit conhecido.
Hipótese não promove. Resumo não promove. "O agente disse" não promove.

## Propor

1. Identifique o finding (`F-NNN`) e a evidência que o sustenta.
2. Escolha o destino:

| Destino | Quando | Aprovação |
|---|---|---|
| `docs/rules/` | vira restrição vinculante do projeto | **humano** |
| `project_state/DECISIONS.md` | escolha estrutural entre alternativas | **humano** |
| `docs/procedures/` | passo a passo reutilizável | humano ou responsável designado |
| `docs/gotchas/` | armadilha específica, verificada | agente, com evidência |
| `project_state/knowledge/experiments/` | hipótese ainda em teste | agente |
| `project_state/knowledge/historical/` | valeu, não vale mais | agente |

3. Escreva o candidato em `project_state/knowledge/candidates/K-NNN-<slug>.md` a partir de `.agents/templates/KNOWLEDGE.md`, declarando obrigatoriamente: **origem · evidência · workstream · validade · autoridade · quem aprova · data de verificação · condições de supersessão**.
4. Grave o evento `knowledge_proposed`.

*Concluído quando:* o candidato existe com os oito campos preenchidos e o evento gravado.

Candidato sem condição de supersessão é candidato incompleto: conhecimento que não sabe dizer
quando deixa de valer vira sedimento.

## Aprovar

1. Confirme que a evidência ainda vale: o commit citado ainda é ancestral do `HEAD`? O comando ainda produz a mesma saída?
2. Confirme que o conhecimento não duplica nem contradiz regra, decisão ou gotcha existente. Contradiz? A promoção vira **supersessão**, não acréscimo.
3. Registre o aprovador e a data.
4. Mova para o destino, com nível de autoridade `verified-knowledge` (ou `normative` / `approved-decision` conforme o destino).
5. Grave o evento `knowledge_approved`.

*Concluído quando:* a evidência foi revalidada, o destino não tem duplicata e o aprovador está registrado.

## O que um agente nunca altera sozinho

- regra normativa (`docs/rules/`, `AGENTS.md`);
- política de segurança ou privacidade;
- decisão arquitetural aprovada;
- limites de autonomia;
- gates de qualidade.

Auto-improvement produz **proposta**. A alteração é do humano. Esta fronteira é o que impede o
sistema de reescrever as próprias restrições — e é a razão de o funil existir.

## Curadoria e supersessão

Conhecimento envelhece. Revise quando: a condição de supersessão declarada ocorreu, a evidência
não reproduz mais, ou surge conhecimento que o contradiz.

1. **Nunca apague.** Marque `Status: superseded by K-NNN` e faça o novo referenciar o antigo.
2. Mova o obsoleto para `knowledge/historical/` mantendo o ID.
3. Grave o evento.

Apagar histórico auditável é proibido. Um conhecimento errado que foi seguido por meses é
informação valiosa sobre o projeto.

## Retenção

| Registro | Retenção | Purga |
|---|---|---|
| conhecimento ativo | vida do projeto | nunca automática |
| `historical/` | vida do projeto | nunca automática |
| `candidates/` não aprovado por 90 dias | expira | move para `historical/` com motivo |

## Tratamento de falhas

- **Evidência não reproduz na aprovação:** o candidato não é promovido. Vai para `historical/` com o motivo — e a não promoção também é conhecimento.
- **Dois candidatos contraditórios:** ambos vão para revisão humana juntos. Não escolha um lado em silêncio.
- **Aprovador indisponível:** o candidato fica em `candidates/` e a workstream registra `pending_gates: [G10]`. Não promova por decurso de prazo.

## Anti-patterns

Promover resumo de sessão · promover sem condição de supersessão · promover para `docs/rules/` sem
humano · apagar conhecimento superado · acumular candidatos sem revisão · promover a mesma coisa em
dois destinos.
