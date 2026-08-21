---
name: session-handoff
description: Gera e valida o contrato de passagem entre sessões, agentes e harnesses, declarando explicitamente o que não foi validado e amarrando tudo a branch, worktree e commit. Use ao encerrar sessão com trabalho aberto, ao trocar de agente ou ferramenta, e ao receber um handoff antes de confiar nele. Não use como substituto de ledger, de decisão ou de documentação normativa.
metadata:
  protocol: VLAEG AI Ready First
  layer: memory
  version: 2.0.0
  source: "contrato de handoff derivado de akitaonrails.com/2026/07/20"
  adapted: true
  risk: medium
  vlaeg_phases: [cross-cutting]
  triggers:
    - "encerrar sessão com trabalho aberto"
    - "trocar de agente, modelo ou harness"
    - "receber handoff e precisar validá-lo"
  negative_triggers:
    - "substituir ledger, decisão ou documentação normativa"
    - "declarar conclusão sem evidência"
  produces: ["HANDOFF.md", "evento handoff"]
  gates: ["G7", "G8"]
---

# Handoff de sessão

Handoff é compressão deliberadamente com perda. Ele preserva o que parece mais importante **agora**
— e por isso declara o que perdeu, em vez de fingir completude.

Dois ramos: **gerar** e **receber**.

## Gerar

1. Preencha `project_state/workstreams/<WS>/HANDOFF.md` a partir de `.agents/templates/HANDOFF.md`.
2. Amarre a branch, worktree e commit atuais. Sem esses três, o handoff não é verificável.
3. Preencha `completed` **apenas** com o que tem evidência apontada em `EVIDENCE.md`. Item sem evidência vai para `not_validated`.
4. Preencha `failed_attempts` — o que foi tentado e não funcionou vale tanto quanto o que funcionou; é o que impede a próxima sessão de repetir o beco.
5. Preencha `not_validated` sem eufemismo: o que foi escrito e nunca rodou, o teste que não foi executado, a suposição que ficou de pé.
6. Preencha `next_actions` como ações, não como intenções: "rodar X e corrigir Y", não "continuar a tarefa".
7. Liste `pending_gates` e `context_pointers` (caminhos, não conteúdo).
8. Grave o evento `handoff` no ledger.

*Concluído quando:* todo item de `completed` aponta evidência, `not_validated` está preenchido ou explicitamente vazio com motivo, e branch/worktree/commit constam.

## Receber

1. **Verifique o commit primeiro.** O commit do handoff é igual a `current_commit` no `STATE.md` vigente?
   - Sim → o handoff é operacionalmente atual.
   - Não → **histórico**. Ancestralidade só confirma a linha de desenvolvimento; trate todo conteúdo como `historical` e revalide antes de agir. `tools/validate_state.py` detecta isso automaticamente.
2. Nunca aja sobre `completed` sem checar a evidência apontada. Resumo não é evidência.
3. Trate `not_validated` como trabalho a fazer, não como detalhe.
4. Divergência entre o handoff e o código: o **código vence**. Corrija o handoff e registre `F-NNN`.

*Concluído quando:* a validade do commit foi verificada e os itens não validados entraram no plano da sessão.

## O que o handoff não é

| Não é | Porque | Onde está |
|---|---|---|
| Ledger | handoff comprime; ledger preserva | `EVENTS.jsonl` |
| Decisão | decisão precisa de autoridade e status | `DECISIONS.md` |
| Documentação normativa | handoff é volátil | `docs/` |
| Evidência | resumo não prova | `EVIDENCE.md` |
| Declaração de conclusão | conclusão exige gates verdes | `quality-gates.md` |

Um handoff que declara conclusão sem apontar evidência é uma alegação — e o protocolo trata
alegação apresentada como prova como falsificação de evidência.

## Independência de harness

O handoff é texto em arquivo versionado. Ele funciona entre Claude Code, Codex, Gemini CLI, outro
harness ou uma pessoa. Nenhum campo depende de fornecedor, formato proprietário ou ferramenta
específica — é o que permite trocar de motor sem jogar fora a viagem.

Quando um provider de memória estiver disponível, ele **complementa** o arquivo; não o substitui.
O modo de referência do protocolo continua sendo o arquivo versionado.

## Tratamento de falhas

- **Sem Git no projeto:** registre `commit: none` e declare no handoff que a verificação de obsolescência não está disponível. Declarar a limitação é o requisito; escondê-la, não.
- **Trabalho interrompido sem chance de gerar handoff:** a próxima sessão reconstrói a partir de `STATE.md` + ledger e registra `F-NNN` sobre a lacuna.
- **Handoff conflita com outro handoff:** o mais recente com commit válido vence; o outro recebe `superseded by`.

## Anti-patterns

`completed` inflado com o que não foi verificado · `not_validated` vazio por otimismo ·
`next_actions` genérico · handoff sem commit · confiar em handoff obsoleto · usar handoff como
substituto de registrar decisão.
