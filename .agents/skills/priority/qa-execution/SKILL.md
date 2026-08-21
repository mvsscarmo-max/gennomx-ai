---
name: qa-execution
description: Roda sessões de dogfooding em persona pelas interfaces públicas do produto — uma persona percorre a jornada, sonda bordas, caça atritos e relata o que um usuário real viveria. Use ao validar candidato a release, diff de branch, migração ou mudança visível ao usuário contra comportamento de produção. Não use para mudança sem superfície visível, para substituir a suíte automatizada, nem para auditar implementação de agente.
metadata:
  protocol: VLAEG AI Ready First
  layer: priority
  version: 1.0.0
  source: pedronauck/skills@ffc7c18540fd41b3030b29c0b61a494de3d20d49/skills/mine/qa-execution
  video_evidence: "ohzc4p7-QHQ 13:53 — grupo SENSORES"
  adapted: true
  adaptation_note: "Árvore de QA passa a viver sob project_state/workstreams/<WS>/qa/ e a dependência da skill qa-report virou bootstrap embutido; driver de navegador é opcional com degradação declarada."
  risk: medium
  vlaeg_phases: [E, G]
  triggers:
    - "candidato a release"
    - "mudança visível ao usuário em nível de risco >= 2"
    - "migração que altera experiência"
  negative_triggers:
    - "mudança sem superfície visível ao usuário"
    - "substituir suíte automatizada"
    - "auditar conformidade de implementação (use cycle-review)"
  produces: ["relatório datado da rodada", "registro de bugs", "decisões para humano"]
  gates: ["G2", "G12"]
---

# QA de usuário real

Teste o produto como uma pessoa o encontra: uma **persona** percorre uma jornada pelas interfaces
públicas, sente o atrito, bate nas bordas e relata o que aconteceu. Isto é **dogfooding**, não
passada de teste roteirizado — a sessão é o trabalho, e a árvore de QA lembra dela.

Três inegociáveis seguram toda sessão:

1. **Em persona.** Toda interação e toda verificação passam por uma superfície que um usuário real alcança — sem atalho de ferramenta de desenvolvedor, sem ler código para decidir o que deveria acontecer, sem empurrar por cima de um travamento.
2. **Prova, não otimismo.** `Passa` é o observável esperado **visto**, confirmado por um caminho de leitura independente, sobrevivendo a um recarregamento, com evidência capturada. UI otimista não é confirmação.
3. **Escreveu ou não aconteceu.** Toda sessão atualiza a árvore: veredito por cenário, registro de bugs e o relatório datado com o debrief.

## Árvore de QA

Raiz padrão: `project_state/workstreams/<WS>/qa/`. É a memória desta skill e sua única saída —
nunca um diretório temporário.

```
qa/
├── README.md          # pontos de entrada, comando do servidor, códigos de área
├── personas/          # quem percorre
├── journeys/          # o que se percorre
├── scenarios/         # veredito por cenário
├── bugs/              # BUG-<AAAAMMDD>-<slug>
├── charters/          # persona × jornada × tour × caixa de tempo
└── reports/           # <AAAA-MM-DD>-<escopo>.md
```

Árvore inexistente → rode o bootstrap: crie a estrutura, escreva o `README.md` com os pontos de
entrada reais do produto e redija ao menos uma persona e uma jornada antes de percorrer. Percorrer
sem plano recria a duplicação que este desenho elimina.

## Passos

**Passo 1 — Resolver árvore, escopo e pré-condições**

- Leia, nesta ordem: `qa/README.md`, os arquivos de `scenarios/` no escopo, os `bugs/` abertos e os charters do ciclo.
- Escopo: rodada de **branch** cobre as jornadas que o diff visível toca, mais uma jornada adjacente de canário. Sem mudança visível ao usuário → relate isso e pare. Rodada de **release** cobre o que o plano do ciclo marcou.
- Pré-condições: a suíte automatizada está verde (pré-condição, não etapa de QA) e o produto está alcançável numa build com paridade de produção — servidor real, autenticação real, sem mock. Não alcançável → nomeie a lacuna exata e pare.

*Concluído quando:* o escopo está fixado e toda pré-condição foi atendida ou sua lacuna foi exposta.

**Passo 2 — Montar a matriz e criar o relatório agora**

- Monte a matriz da sessão a partir dos charters: persona × jornada × tour × caixa de tempo, ordenada por risco. Jornada no escopo sem charter recebe um antes de percorrer.
- Crie `qa/reports/<AAAA-MM-DD>-<escopo>.md` a partir de `assets/report-template.md` **antes da primeira sessão**, com toda linha `Pendente`. O relatório em disco é a fonte de verdade da retomada — atualize após cada sessão e cada correção, nunca só no fim.

*Concluído quando:* o relatório existe em disco com a matriz completa, toda linha `Pendente`.

**Passo 3 — Percorrer cada jornada em persona**

- Leia `references/session-protocol.md` (o laço entrar → agir → verificar → capturar e o padrão de evidência).
- Para cada charter, na ordem da matriz: adote a persona (dispositivo, rede, idioma), entre pelo ponto de entrada real e percorra a jornada verbo a verbo até o **estado final verdadeiro**.
- Cace **atritos** o tempo todo — incômodo que a persona sente e que nenhuma verificação funcional reprova. Os afiados viram findings.
- Trecho que só um humano completa (pagamento real, e-mail/SMS externo, OAuth real) é marcado `Bloqueado (precisa verificação humana)` com instruções exatas — nunca simulado.

*Concluído quando:* todo charter foi percorrido até um veredito registrado, com evidência nos checkpoints e divergências, debrief escrito e linha da matriz atualizada.

**Passo 4 — Tours e sondagem de bordas**

- Leia `references/tours-and-edges.md`.
- Rode o **tour** de cada charter contra sua superfície, em persona, dentro da caixa de tempo, perguntando a cada ação: *isso importaria para o tema deste tour?*
- Escolha de 5 a 10 casos de borda compatíveis com a superfície e a persona e tente-os. Tentado-e-limpo também é evidência.

*Concluído quando:* todo tour foi rodado e os casos escolhidos foram tentados e registrados.

**Passo 5 — Passada de lentes**

- Leia `references/lenses.md` — as seis lentes e suas severidades padrão.
- Escolha as 2 jornadas que cobrem a maior superfície alterada e refaça-as segurando as seis lentes, numa caixa de 45 minutos, registrando `passa` / `atrito` / `falha` por lente.

*Concluído quando:* as duas jornadas foram refeitas e todo veredito de lente está registrado.

**Passo 6 — Registrar findings**

- Deduplique primeiro: busque em `bugs/` e nos `bug_ids` dos cenários afetados. Reencontrado → acrescente `## Reencontrado`; regrediu → reabra com `## Regrediu`; só um sintoma genuinamente novo ganha id novo.
- Registre pelo lado do usuário: nível de impacto, persona, passo da jornada, reprodução a partir do ponto de entrada da persona, caminhos de evidência. Depois ligue o id aos cenários afetados.

*Concluído quando:* todo finding está deduplicado, registrado e ligado às suas linhas.

**Passo 7 — Laço de correção governado**

- Leia `references/fix-loop.md` — o governador, a regra de teste de regressão por correção e as Decisões para um Humano.
- Julgue cada correção contra o governador **antes de editar**. Só o que passa em todos os limites é corrigido automaticamente, e cada correção automática embarca teste de regressão e refaz as jornadas impactadas e adjacentes em persona. O resto vai para Decisões para um Humano, com opções e recomendação.

*Concluído quando:* todo finding está corrigido-e-retestado ou escalado com recomendação, e nenhuma correção ficou pela metade.

**Passo 8 — Fechar a rodada**

- Portão de saída: rode a suíte automatizada completa uma vez e registre o resultado **verbatim**. Matriz verde sobre suíte vermelha não está pronta, e o Status Final tem que dizer isso.

*Concluído quando:* zero linhas `Pendente`, vereditos e bugs atualizados, debriefs no relatório, e o Status Final declara prontidão com totais por nível de impacto, sustentado por evidência da build atual.

## Tratamento de falhas

- **Sem servidor ou driver de navegador:** marque os trechos de navegador `Bloqueado (precisa verificação humana)` com o pré-requisito exato e siga com as jornadas de CLI/HTTP ainda percorríveis em persona. A degradação vai declarada no relatório.
- **Um fluxo trava:** encerre a sessão, registre, tente uma vez a partir de sessão limpa e marque bloqueado. Travamento é finding a registrar, nunca algo a empurrar.
- **Credencial ou dado de teste ausente:** marque essas sessões como bloqueadas com o pré-requisito exato e siga com as demais.
- **Matriz maior que a janela:** corte por risco, marque as linhas cortadas como `Pulado` com o motivo e exponha isso no Status Final — a cobertura encolhe visivelmente ou não encolhe.

## Anti-patterns

Corrigir dentro da sessão · aprovar por UI otimista · retestar só a jornada corrigida · decidir
questão de produto para fechar uma linha · requeuear em silêncio item bloqueado · relatório escrito
só no fim · usar esta skill onde a suíte automatizada é o instrumento certo.
