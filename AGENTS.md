# AGENTS.md — GennomX AI

Núcleo residente. Tudo que não está aqui é carregado sob demanda por ponteiro.
Este arquivo prevalece sobre convenções genéricas da ferramenta.

## Fronteira desta raiz

A GennomX AI é infraestrutura de dados biomédicos e competitivos (banco, ingestão, MCP,
dashboard, API). **Não** é o gerador final de relatórios. Relatórios saem de modelos host via
MCP. Contrato de produto: `docs/rules/contrato-operacional.md`. Não edite o site nem as
outras aplicações a partir daqui.

## Precedência (em conflito, o número menor vence)

1. Restrições legais e de segurança
2. Instrução explícita do usuário nesta sessão
3. Princípios do protocolo — `docs/ai-ready/protocol.md`
4. Skills prioritárias — `.agents/skills/priority/`
5. Gates e Revisão de Ciclo — `docs/ai-ready/quality-gates.md`, `docs/ai-ready/cycle-review.md`
6. Skills de memória e continuidade — `.agents/skills/memory/`
7. Regras do projeto — `docs/rules/`, decisões ativas em `project_state/DECISIONS.md`
8. Skills de stack e skills externas aprovadas — `.agents/registry/external-skills.yaml`
9. Método VLAEG adaptado — `docs/ai-ready/vlaeg-adapted.md`
10. Preferências globais → defaults do agente

Preferência global nunca sobrescreve regra local. Nível inferior nunca enfraquece superior.

## Ordem de descoberta (uma sessão nova começa aqui)

1. Este arquivo.
2. `project_state/PROJECT.md` — objetivo, comandos, regras críticas.
3. `project_state/WORKSTREAMS.md` — qual workstream está ativa.
4. `project_state/workstreams/<WS>/STATE.md` — tarefa atual, bloqueios, gates pendentes.
5. `project_state/workstreams/<WS>/HANDOFF.md` — só se existir e o commit ainda casar.

Pare aqui. Orçamento de briefing: **6.000 caracteres** (`.agents/policy/context-budget.yaml`).

## Ciclo operacional

`DISCOVER → ORIENT → RECALL → FRAME → EXPLORE → SPECIFY → PLAN → APPROVE → IMPLEMENT
→ VERIFY → REVIEW → DESLOP → REVISÃO DE CICLO → RECORD → PROMOTE → HANDOFF|CLOSE`

## Seleção de skills

Carregue o **conjunto mínimo**. Matriz: `docs/ai-ready/skill-routing.md`.

- Vai escrever ou corrigir código → `no-workarounds`
- Vai declarar tarefa de código concluída, commitar ou abrir PR → `deslop`
- Vai editar `AGENTS.md` ou seus ponteiros → `writing-agents-md`
- Vai criar ou editar uma skill → `writing-skills`
- Risco ≥ 3 → Revisão de Ciclo (`cycle-review`)
- Mudança visível ao usuário em release candidate → `qa-execution`
- Trocou de agente, sessão ou vai encerrar com trabalho aberto → `session-handoff`

Registre as skills no `STATE.md`. Skill externa passa por `external-skill-intake`.

## Limites de autonomia

**Sem aprovação:** ler, pesquisar, rodar testes e validadores, implementar tarefa aprovada no
escopo, atualizar o próprio estado, gerar handoff.

**Exige aprovação humana:** plano ≥ 3, arquitetura/schema, deploy, ingestão real, provisionar
MinIO/R2, acesso a produção.

**Proibido:** chatbot ou relatório final como núcleo; host com acesso SQL ou dado cru; escrita no
banco por modelo host no MVP; scraping indiscriminado ou evasão de bloqueio; apagar rastreabilidade;
copiar marca/base/claims da Gosset AI; declarar teste aprovado sem executá-lo; adotar `ai-jail`
ou YOLO. Isolamento de scraper em container é regra de produto, não sandbox do protocolo.

## Evidência

Conclusão só existe com evidência executada em `project_state/workstreams/<WS>/EVIDENCE.md`.
Divergência: **o código vence**.

## Registro

Alteração → `EVENTS.jsonl`, `STATE.md`, `EVIDENCE.md`. Decisões → `DECISIONS.md` (D-NNN).
Findings → `FINDINGS.md` (F-NNN). IDs nunca reutilizados. Congelado não orienta planejamento.

## Segurança da memória

Infraestrutura com dado biomédico. Nunca capture `.env`, tokens MCP, dumps ou dado pessoal.
Política: `.agents/policy/capture-policy.yaml`. Busca entre projetos: **desativada**.

## Comandos

```bash
python tools/validate.py
cd backend && python -m pytest tests/unit -q
cd frontend && npm run lint && npm run typecheck && npm run build
```

Sessão administrativa não autentica MCP. R2 não integra o runtime nesta fase.
