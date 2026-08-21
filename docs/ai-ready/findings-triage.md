<!-- validate-links: illustrative-paths -->

# Triagem de achados — critério de entrada no ledger de findings

Define o que vira finding formal (`F-NNN`) e o que permanece apenas no documento de origem.

## Princípio

`FINDINGS.md` é um **ledger de conhecimento reutilizável**, não um depósito de auditoria. O texto
integral de um parecer, auditoria ou plano macro vive no documento de origem; o ledger guarda o que
o projeto precisa para **não reinvestigar, não repetir erro e não perder rastreabilidade**.

Ledger inchado deixa de ser lido — e um ledger que ninguém lê não previne nada.

## Eixo 1 — tipo do achado

| Tipo | Exemplos |
|---|---|
| **Defeito** | bug, vulnerabilidade, dívida técnica, falha de processo com correção pendente |
| **Estrutural** | descoberta de arquitetura, limitação de ambiente, falso positivo de validador, esclarecimento que evita reinvestigação |

## Eixo 2 — severidade (só para defeitos)

| Severidade | Critério |
|---|---|
| Crítica | compromete segurança, dados, integridade de gate/evidência ou produção **agora** |
| Alta | quebra funcional real, ou risco concreto com raio de explosão amplo |
| Média | defeito real com impacto contido ou exploração não confirmada |
| Baixa | cosmético, dívida localizada, custo de manutenção |
| Informativa | observação sem ação exigida |

## Regra de entrada

1. **Defeito Crítico ou Alto** → promovido a `F-NNN`, com referência ao documento de origem. O detalhamento fica na origem; o finding carrega resumo, causa raiz, resolução e consequência.
2. **Defeito Médio, Baixo ou Informativo** → **não** recebe `F-NNN`. Permanece no documento de origem, identificado pelo identificador local daquele documento. Só é citado no ledger quando uma tarefa ativa depender dele — e nesse caso como **ponteiro de uma linha**, nunca como cópia.
3. **Estrutural** → entra no ledger **independentemente de severidade**, desde que tenha valor de reuso: impede reinvestigação, registra limitação permanente ou explica comportamento que parece defeito e não é. Se não passa nesse teste, não entra em lugar nenhum além da origem.

O eixo estrutural é o mais valioso e o mais esquecido: é o que impede o quinto agente de investigar
pela quinta vez o mesmo falso positivo.

## Requisitos do documento de origem

Para a triagem ser **mecânica**, todo parecer, auditoria ou plano macro que lista achados deve
declarar, por item: **identificador local estável**, **severidade** e **tipo**.

Item sem esses três campos **não pode ser triado** — complete o documento antes de promover
qualquer achado.

## Promoção tardia

Um defeito Médio/Baixo vira `F-NNN` quando: recorre depois de registrado; seu raio de explosão
cresce (código novo passa a depender do caminho afetado); ou passa a bloquear gate ou entrega. O
finding novo referencia o identificador local e o documento de origem.

**O inverso não existe:** um finding nunca é rebaixado nem removido. Identificadores não são
reutilizados, e findings resolvidos permanecem como registro.

## Não retroatividade

A regra não reescreve o passado. Findings já registrados permanecem como estão — apagar histórico
auditável é proibido. A triagem vale para todo achado registrado a partir da sua adoção.
