<!-- validate-links: illustrative-paths -->

# Modelo de contexto

Contexto residente é caro: cada linha sempre carregada tributa toda tarefa e dilui as outras
regras. Este documento separa o que é sempre carregado do que é buscado.

## 1. Os seis tipos

| # | Tipo | Pergunta que responde | Arquivo | Carregamento |
|---|---|---|---|---|
| 1 | **Residente** | Como se trabalha aqui? | `AGENTS.md` | sempre, integral |
| 2 | **Normativo** | O que o sistema é? O que é proibido? | `docs/` | por ponteiro, sob demanda |
| 3 | **Operacional** | O que está acontecendo agora? | `STATE.md` da workstream | no ORIENT |
| 4 | **Delta** | O que mudou desde a última participação **deste** agente? | ledger filtrado | no RECALL |
| 5 | **Pesquisável** | O que já foi tentado? | ledger, evidência, findings | por busca explícita |
| 6 | **Consolidado** | O que aprendemos que vale adiante? | conhecimento, regras | por ponteiro |

Misturar tipos no mesmo arquivo é o defeito que este modelo existe para evitar. `STATE.md` não
guarda histórico; o ledger não guarda regra; `docs/` não guarda estado.

## 2. Briefing inicial

**Contém** — objetivo do projeto · regras críticas · workstream ativa · tarefa atual · decisões
relacionadas à tarefa · bloqueios · riscos · gates pendentes · referência ao último handoff ·
ponteiros de busca.

**Não contém** — transcrição · ledger inteiro · todos os planos · todas as decisões · todas as
skills · workstreams encerradas · decisões substituídas · conhecimento irrelevante à tarefa.

**Orçamento:** declarado em `.agents/policy/context-budget.yaml`. Referência: 6.000 caracteres.
Estourou? Corte pela ordem: ponteiros extras → riscos → decisões relacionadas.
**Nunca corte:** objetivo, regras críticas, tarefa atual, bloqueios.

## 3. Delta

O delta é o que aconteceu **desde a última participação deste agente nesta workstream** — não desde
o começo:

```text
eventos com timestamp > last_seen[agente] AND workstream == WS
```

`last_seen` vive no `STATE.md`. O delta tem teto próprio (referência: 4.000 caracteres); acima
disso, entrega os N mais recentes + **a contagem do que ficou de fora** + ponteiro de busca. Truncar
sem declarar a omissão é pior que truncar.

Nunca injete a sessão inteira no próximo prompt: isso recria exatamente o problema de contexto
bruto, caro e ruidoso que o protocolo resolve.

## 4. Busca em vez de carga

Quando a tarefa exige mais do que o briefing traz, o agente **busca**:

```text
memory.search(query, scope=workstream|project, limit=N)
```

Implementação degradada aceitável: `grep`/`rg` sobre o ledger, findings, decisões e conhecimento. O
protocolo **não exige ferramenta** — exige que a busca seja possível e que os arquivos sejam
pesquisáveis: uma linha por evento, JSON válido, identificadores estáveis.

## 5. Escopos

| Escopo | Conteúdo | Padrão |
|---|---|---|
| Projeto | tudo em `project_state/` e `docs/` deste repositório | ativo |
| Global | preferências pessoais que valem em todo projeto | ativo apenas para preferências |
| Entre projetos | memória de outros repositórios | **desativado** |

Ativar busca entre projetos exige decisão registrada, justificativa, escopo limitado e data de
revisão. Busca global à toa traz ruído, não sinal.

Preferência global nunca sobrescreve regra do projeto, decisão ativa, requisito, segurança, padrão
técnico local ou política de privacidade. O escopo legítimo de preferência global é estreito:
idioma, estilo de comunicação, formato de mensagem de commit, verbosidade.

## 6. O teste do aluguel

Toda linha residente paga aluguel. Ela fica **apenas** se as três valerem:

1. **Delta** — muda o que o agente faria de outro jeito. Repetir boa prática geral falha aqui.
2. **Frequência** — vale para a maioria das sessões naquele escopo. Regra de nicho desce um degrau.
3. **Economia** — mantê-la residente é mais barato que derivá-la sob demanda. O que a ferramenta já anuncia sozinha falha aqui.

Escada de escopo, do mais caro ao mais barato:

```text
global → raiz do repositório → subdiretório → skill → documento linkado
```

Linha que falha o teste é **removida ou realocada**, nunca suavizada. Suavizar mantém o custo e
perde a força.
