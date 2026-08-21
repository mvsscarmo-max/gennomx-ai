---
name: deslop
description: Remove o sotaque de IA do diff — comentário em excesso, defesa desnecessária, cast para calar tipo e aninhamento evitável. Use antes de declarar qualquer tarefa de código concluída, antes de commit ou PR, e quando o usuário pedir limpeza de slop. Não use para diff só de documentação, só de formatação, nem para refatoração ampla de arquitetura.
metadata:
  protocol: VLAEG AI Ready First
  layer: priority
  version: 1.0.0
  source: pedronauck/skills@ffc7c18540fd41b3030b29c0b61a494de3d20d49/skills/mine/deslop
  video_evidence: "ohzc4p7-QHQ 09:05 — grupo GUARDRAILS"
  adapted: true
  risk: low
  vlaeg_phases: [A, E]
  triggers:
    - "vai declarar tarefa de código concluída"
    - "vai commitar ou abrir PR"
    - "pedido explícito de limpeza de slop"
  negative_triggers:
    - "diff só de documentação"
    - "diff só de formatação"
    - "refatoração arquitetural (use refactoring-analysis externa após intake)"
  produces: ["diff limpo", "resumo de 1-3 frases no EVIDENCE.md"]
  gates: ["G5"]
---

# Remover slop de IA

Confira o diff contra a base e remova o que a IA introduziu e um autor humano do repositório não
teria escrito. O objetivo é que o diff **passe por código do repositório**, não por código gerado.

## Escopo

O diff da branch contra a base (`git diff <base>...HEAD`), ou o conjunto que a tarefa alterou.
Código pré-existente fora do diff não é escopo — mexer nele é ampliação silenciosa.

## O que remover

- **Comentário desnecessário ou fora do estilo local** — comentário que repete o que a linha diz (`// incrementa i`), cabeçalho de seção decorativo, docstring genérica em função óbvia. Compare com a densidade de comentário dos arquivos vizinhos: o alvo é o padrão do repositório, não um padrão abstrato.
- **Defesa desnecessária** — `try/catch` em caminho confiável, checagem de nulo em valor que o tipo garante, validação repetida de dado já validado na fronteira.
- **Cast para calar o tipo** — `as any`, `as unknown as`, `!` usados só para compilar. Encontrou um? Este é território de `no-workarounds`: a correção é na origem, não a remoção do cast.
- **Aninhamento evitável** — três níveis de `if` que viram um early return.
- **Abstração prematura** — interface com uma implementação, factory para um caso, camada que só repassa.
- **Nomes cerimoniosos** — `dataProcessorManagerService` onde o repositório usa `parser`.
- **Qualquer padrão inconsistente com o arquivo e o código ao redor.**

## Guardrails

- **Comportamento inalterado**, salvo correção de bug evidente — e aí o bug vira `F-NNN`.
- **Edições mínimas e focadas** em vez de reescrita ampla. Se a limpeza começar a virar refatoração, pare: isso é outra tarefa, com outro nível de risco.
- **Não invente estilo.** O padrão de referência é o dos arquivos vizinhos, verificado, não presumido.
- **Não remova comentário que carrega informação não óbvia** — motivo de uma escolha, link para registro, alerta de armadilha. Esses são exatamente os que sobrevivem.

## Procedimento

1. Obtenha o diff e liste os arquivos alterados.
2. Para cada arquivo, abra um vizinho não alterado do mesmo diretório como referência de estilo.
3. Percorra o diff aplicando a lista acima, arquivo por arquivo.
4. Rode o comando de verificação declarado em `PROJECT.md` — a limpeza não pode quebrar nada.
5. Escreva o resumo em 1–3 frases e registre em `EVIDENCE.md`.

*Concluído quando:* todo arquivo do diff foi percorrido, a verificação passou e o resumo está registrado.

## Ordem em relação às outras skills

`no-workarounds` durante a implementação → **`deslop`** → `cycle-review`. Rodar `deslop` antes
da revisão externa evita gastar crédito de revisão apontando ruído que o guardrail local remove.

## Gate

**G5** exige: `deslop` executado sobre o diff e resumo de 1–3 frases em `EVIDENCE.md`. Declarar
tarefa de código concluída sem isso é gate pulado sem registro.

## Anti-patterns

Reescrever arquivo inteiro "para ficar consistente" · remover comentário que explica o porquê ·
mudar comportamento a pretexto de limpeza · rodar em diff de documentação · usar como substituto
de revisão · deixar o resumo de fora do registro.
