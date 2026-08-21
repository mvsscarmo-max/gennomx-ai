<!-- validate-links: illustrative-paths -->

# Anti-patterns proibidos

Cada item desta lista é o resumo de um problema real, com um custo que já foi pago. Aparecem aqui
com o sintoma, a causa e a contramedida — porque uma lista de proibições sem o "por quê" não
sobrevive à primeira pressão de prazo.

| # | Anti-pattern | Como se manifesta | Contramedida |
|---|---|---|---|
| 1 | **Núcleo residente gigante** | o arquivo sempre carregado vira manual; regra importante se dilui no meio de boa prática genérica | teto verificado de tamanho + teste do aluguel por linha |
| 2 | **Duplicação entre protocolo e skill** | a mesma regra em dois lugares; um é editado, o outro não | um arquivo é a fonte; o outro aponta |
| 3 | **Duplicação entre workstream e estado global** | lista global de tarefas concorrendo com o `STATE.md` | a workstream é a única dona da tarefa |
| 4 | **Carregar todas as skills** | contexto cheio, nenhuma skill efetiva | conjunto mínimo + orçamento + anti-gatilhos |
| 5 | **Memória tratada como verdade** | "o ledger diz que funciona" | o ledger prova o que aconteceu **naquele commit** |
| 6 | **Resumo tratado como evidência** | "testes passaram", sem saída | evidência = comando + saída + timestamp + commit |
| 7 | **Promoção automática a regra** | saída de agente vira norma | promoção exige autoridade humana |
| 8 | **Atualização silenciosa de skill externa** | o comportamento muda sem ninguém decidir | commit de origem fixado; mudança é decisão |
| 9 | **Busca global entre projetos por padrão** | ruído de outro repositório entra como contexto | desativada por padrão; ativar exige quatro requisitos |
| 10 | **Histórico sem retenção** | o registro cresce até ninguém abrir | política de retenção declarada por tipo |
| 11 | **Captura indiscriminada** | segredo no ledger | política de captura em camadas, aplicada antes de persistir |
| 12 | **Documentação que não corresponde ao código** | o agente age pelo papel, e o papel está velho | o código vence; divergência vira finding |
| 13 | **Plano sem critério de validação** | "concluído" é opinião | todo critério tem comando exato |
| 14 | **Tarefa sem origem** | ninguém sabe por que aquilo está sendo feito | origem obrigatória: plano ou `ad-hoc` declarado |
| 15 | **Decisão sem autoridade** | escolha estrutural feita por quem não podia | campo de autoridade obrigatório e validado |
| 16 | **Gate opinativo** | "revisado" sem artefato | gate é condição observável por terceiro |
| 17 | **VLAEG rígido para toda mudança** | typo percorre cinco fases; a equipe abandona o rito | aplicabilidade declarada + rito por risco |
| 18 | **Remover a identidade VLAEG sem necessidade** | perde-se a lente que classifica a tarefa | fases permanecem como lente |
| 19 | **Preservar VLAEG contra prioridade superior** | fidelidade histórica bloqueando melhoria | prioridade inferior nunca enfraquece superior |
| 20 | **Autonomia comprada por isolamento externo** | "pode fazer qualquer coisa, roda contido" | excluído por norma; segurança vem de limites, gates, captura e evidência |
| 21 | **Índice e corpo divergindo** | o índice diz `endereçada`, o documento diz `vigente` | espelhamento verificado; divergência é erro |
| 22 | **Registro órfão** | diretório sem linha no índice, ou o inverso | criação atômica; reconciliação antes de qualquer trabalho |
| 23 | **Ledger reescrito** | linha corrigida "para ficar consistente" | append-only; correção entra como evento novo |
| 24 | **Silenciar o validador para ficar verde** | exclusão criada para esconder erro real | fronteira **declarada** e revisável; caminho central nunca excluído |
| 25 | **Gate selado preso a um SHA** | provar move o alvo da prova; re-verificação em cascata | verificação **recomputável** em vez de selo |
| 26 | **Rodada de revisão gasta com notação** | orçamento consumido por travessão e seta ASCII | liberal na notação, estrito no julgamento |
| 27 | **Autor revisando a si mesmo** | subagente do próprio autor "aprova" o trabalho | revisor independente; agente nunca assina o aceite |
| 28 | **Ledger de findings inchado** | tudo vira finding; ninguém lê mais | triagem por tipo e severidade |
| 29 | **Histórico tratado como vigente** | plano congelado que se declara ativo orienta decisão | banner de congelamento + exclusão do briefing |
| 30 | **Escrita paralela sem isolamento** | dois agentes no mesmo diretório de trabalho | claim + worktree própria por escritor |

## Como usar esta lista

Ela **não** é um checklist de fim de tarefa. É um catálogo de diagnóstico: quando algo no processo
parece estar custando caro sem entregar garantia, procure aqui o padrão antes de inventar uma regra
nova. A maior parte dos problemas de processo em projeto assistido por IA já está nesta tabela.
