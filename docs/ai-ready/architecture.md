<!-- validate-links: illustrative-paths -->
<!-- Os caminhos citados em prosa descrevem a estrutura de destino num projeto que adota o
     protocolo, não o layout do repositório de origem. Links markdown continuam verificados. -->

# Arquitetura do VLAEG IA-ready 4.0

Como as peças se encaixam, o que cada uma faz — e, sobretudo, **o que cada uma não faz**. Um
componente sem fronteira declarada acaba absorvendo os vizinhos.

## 1. Árvore de diretórios

```text
/
├── AGENTS.md                    Camada 1 — núcleo residente (a única coisa sempre carregada)
├── CLAUDE.md · GEMINI.md · …    ponteiros puros para AGENTS.md, sem regra própria
├── README.md                    porta de entrada humana
├── CHANGELOG.md                 consolidação por ciclo das decisões implementadas
│
├── docs/                        contexto NORMATIVO — o que o sistema é e o que é proibido
│   ├── ai-ready/                o protocolo em si e seus modelos
│   ├── architecture/            arquitetura do produto
│   ├── rules/                   regras vinculantes do projeto
│   ├── procedures/              passo a passo reutilizável
│   ├── gotchas/                 armadilhas verificadas
│   └── legacy/ · historico/     congelado, com banner na primeira linha
│
├── project_state/               contexto OPERACIONAL — o que está acontecendo
│   ├── PROJECT.md               durável: objetivo, escopo, comandos, regras críticas
│   ├── WORKSTREAMS.md           índice das linhas de trabalho
│   ├── AUDITS.md                índice das auditorias
│   ├── DECISIONS.md             escolhas estruturais
│   ├── FINDINGS.md              descobertas reutilizáveis
│   ├── plans/                   planos multi-sessão
│   ├── knowledge/               candidatos, experimentos, histórico
│   └── workstreams/<WS>/
│       ├── STATE.md             tarefas, skills, gates, fases, agentes
│       ├── EVENTS.jsonl         ledger append-only
│       ├── EVIDENCE.md          comando + saída + timestamp + commit
│       └── HANDOFF.md           contrato de passagem
│
├── .agents/                     fundação agnóstica de ferramenta
│   ├── skills/                  FONTE CANÔNICA ÚNICA das skills locais
│   │   ├── priority/            Camada 2 — guias, guardrails, sensores
│   │   ├── memory/              Camada 3 — continuidade
│   │   ├── protocol/            Camada 3b — governança do próprio protocolo
│   │   └── coordination/        Camada 6 — Multi-Harness, sob demanda
│   ├── registry/                índices: skills locais, externas, regras de roteamento
│   ├── templates/               modelos preenchíveis de cada artefato
│   ├── policy/                  orçamento de contexto, captura, escopo do validador
│   ├── coordination/            contrato e schemas do provider (extensão)
│   └── providers/               adapters declarados (extensão)
│
├── tools/                       validadores e automações — provam conformidade
└── audits/                      corpo das auditorias; o índice fica em project_state/
```

### 1.1 Por que `.agents/` e não uma pasta com nome de fornecedor

`.agents/skills/` é a convenção interoperável entre múltiplas ferramentas de agente. Escolher a
pasta de um fornecedor tornaria esse fornecedor a identidade do protocolo — e a troca de
ferramenta viraria migração. O registro (`.agents/registry/local-skills.yaml`) **aponta caminhos;
ele indexa, não copia.**

Ferramentas que exigem um diretório próprio recebem **aliases gerados** (junction no Windows,
symlink relativo em POSIX). Aliases **não** são versionados: são estado local, reprodutível por
comando.

### 1.2 Regras por diretório

| Diretório | Contém | Nunca contém | Obrigatório | Natureza |
|---|---|---|---|---|
| `AGENTS.md` | roteamento e vínculos | explicação do sistema, estado | sim | canônico |
| `docs/` | normativo e referência | estado operacional, tarefa | sim | canônico |
| `docs/legacy/`, `docs/historico/` | congelado, com banner | conteúdo vigente | não | histórico |
| `project_state/` | estado operacional e registros | regra normativa | sim | canônico |
| `project_state/workstreams/<WS>/` | o agora de uma linha de trabalho | regra, história de outra WS | sim | canônico + probatório |
| `project_state/plans/` | planos | estado de execução | quando há nível ≥ 2 | derivado |
| `project_state/knowledge/` | conhecimento promovido | rascunho não revisado | na 1ª promoção | consolidado |
| `.agents/skills/` | skills locais | cópia de skill externa não auditada | sim | canônico |
| `.agents/registry/` | índices e roteamento | corpo de skill | sim | índice |
| `.agents/templates/` | modelos com placeholder | dado real de projeto | sim | configuração |
| `.agents/policy/` | orçamento, captura, escopo | regra de negócio | sim | configuração |
| `tools/` | validadores e automações | opinião, heurística sem regra | sim | operacional |
| `audits/` | corpo das auditorias | índice | na 1ª auditoria | derivado |

**Nomenclatura:** diretório de workstream é `WS-NNN-<slug>`; plano é `PLAN-NNN-<slug>.md`;
auditoria nova é `AUD-NNN-<slug>.md`. O slug é derivado do título, minúsculo, sem acento,
separado por hífen. O **identificador é a identidade; o caminho é campo do índice** — um artefato
antigo pode manter caminho histórico desde que o índice aponte para ele.

**Criação e remoção:** diretório de workstream é criado por automação atômica, que também insere a
linha no índice — as duas coisas na mesma passagem, ou nenhuma. Diretório de workstream **nunca**
é removido; workstream fechada permanece.

## 2. As seis camadas

| Camada | O que é | Quando carrega | Custo |
|---|---|---|---|
| 1 — Núcleo residente | um arquivo que roteia | sempre | pago em toda sessão |
| 2 — Skills prioritárias | guias, guardrails e sensores | por gatilho | pago quando dispara |
| 3 — Skills de memória | continuidade entre sessões | por gatilho | idem |
| 3b — Skills do protocolo | revisão de ciclo, intake externo | por gatilho | idem |
| 4 — Skills externas | catálogo; nenhuma residente | após intake | pago sob demanda |
| 5 — Método VLAEG | lente de análise | por fase da tarefa | pago no FRAME |
| 6 — Coordenação | contrato Multi-Harness | sob demanda (extensão) | pago só se adotada |

O desenho inteiro é uma resposta a uma única pressão: **contexto residente é caro**. Cada camada
existe para tirar algo da Camada 1 sem perdê-lo.

## 3. Fluxo de uma sessão

```text
agente novo
   │ lê AGENTS.md                                      [residente]
   ├─ DISCOVER  → PROJECT.md, WORKSTREAMS.md           [normativo + índice]
   ├─ ORIENT    → workstreams/<WS>/STATE.md            [operacional]
   ├─ RECALL    → HANDOFF.md (se o commit casa) + delta do ledger
   ├─ FRAME     → nível de risco + seleção de skills   [regras de roteamento]
   ├─ EXPLORE   → código (autoridade 1)                [evidência antes de opinião]
   ├─ SPECIFY / PLAN → plans/PLAN-NNN (nível ≥ 2)
   ├─ APPROVE   → limites de autonomia
   ├─ IMPLEMENT → guardrail de causa raiz ativo
   ├─ VERIFY    → comandos declarados → EVIDENCE.md
   ├─ REVIEW    → diff
   ├─ DESLOP    → remover o excesso introduzido
   ├─ CICLO     → G13 (≥ 2) · RC + G14 (≥ 3)
   ├─ RECORD    → EVENTS.jsonl + STATE.md
   ├─ PROMOTE   → proposta de conhecimento
   └─ HANDOFF   → contrato de passagem  |  CLOSE → gates verdes
```

A ordem de descoberta **para** no passo 5. Ler decisões, findings, planos ou ledger inteiros é o
comportamento que o orçamento de contexto existe para impedir; o que a tarefa exigir é buscado por
ponteiro.

## 4. Componentes e responsabilidades

| Componente | Responsabilidade | O que **não** faz |
|---|---|---|
| `AGENTS.md` | rotear e vincular | explicar o sistema, guardar estado |
| `docs/` | normatizar | guardar estado operacional |
| `PROJECT.md` | o que é durável do projeto | o que está acontecendo agora |
| `WORKSTREAMS.md` | índice | detalhe de tarefa |
| `STATE.md` | o agora de uma linha de trabalho | histórico |
| `EVENTS.jsonl` | registro pesquisável | regra |
| `EVIDENCE.md` | prova executada | narrativa |
| `HANDOFF.md` | passagem operacional | substituir ledger ou decisão |
| skills locais | procedimento sob demanda | contexto residente |
| registry | catálogo e roteamento | executar |
| templates | forma do artefato | conteúdo do projeto |
| policy | orçamento e fronteiras | regra de negócio |
| `tools/` | provar conformidade | opinar |

## 5. Fronteira de escopo do validador

Um repositório que hospeda projetos independentes como subpastas **precisa declarar a fronteira**.
Rodar o validador do repositório-pai sobre um projeto-filho produz ruído, não verificação: caminhos
que estão corretos em relação à raiz do filho aparecem como quebrados, e segredos de exemplo do
filho aparecem como vazamento.

A fronteira vive em `.agents/policy/validator-scope.yaml` — **visível e revisável**, em vez de
escondida no código do validador. Ela distingue quatro classes:

| Classe | Significado |
|---|---|
| `excluded_paths` | projetos independentes, com validação própria |
| `excluded_harness` | estado local de ferramenta, efêmero e não versionado |
| `excluded_transient` | rascunho de rodada ainda não promovido a artefato |
| `excluded_vendor` | dependências de terceiros e saída de build |
| `core_paths` | raízes centrais do projeto e vocabulário de escopo do G13 |
| `test_path_patterns` | convenções de teste adicionais, expressas como globs |

**Um caminho central nunca pode ser excluído.** O validador reprova a tentativa: declarar fronteira
é legítimo; silenciar a própria verificação não é.

## 6. Modo degradado

O protocolo **DEVE** continuar operando sem provider de coordenação, sem daemon, sem serviço de
memória, sem rede e com um único agente. Nessa configuração:

| Operação | Equivalente manual |
|---|---|
| registrar evento | acrescentar uma linha JSON ao ledger |
| buscar | `grep`/`rg` sobre ledger, findings e decisões |
| retomar workstream | ler `STATE.md` + ledger a partir da última participação |
| gerar handoff | preencher o template |
| auditar | rodar o validador |

Esse modo é suficiente para satisfazer **todos** os gates. Nenhuma funcionalidade normativa depende
de ferramenta específica — e é isso que impede o protocolo de morrer junto com a ferramenta da vez.

## 7. Subconjunto YAML aceito pelos validadores

Para operar sem dependências externas, os validadores aceitam apenas: mappings por indentação;
escalares simples ou entre aspas; blocos `>` e `|`; listas de escalares inline ou por hífens.
Comentários começam em `#` fora de aspas.

Flow mappings, listas aninhadas, anchors, tags e tipos implícitos **não** fazem parte do contrato.
Metadado que dependa deles **deve ser rejeitado** em vez de interpretado parcialmente — interpretar
pela metade é pior que recusar, porque produz um resultado plausível e errado.
