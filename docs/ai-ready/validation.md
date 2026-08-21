<!-- validate-links: illustrative-paths -->
<!-- Os caminhos citados em prosa descrevem a estrutura de destino num projeto que adota o
     protocolo, não o layout do repositório de origem. Links markdown continuam verificados. -->

# Validação de conformidade

**AI Ready é o que o validador diz, não o que o README promete.** Este documento descreve o que é
verificado automaticamente, o que só pode ser verificado por um humano, e como provar que o
validador consegue reprovar.

---

## 1. Como rodar

```bash
python validators/validate.py --root /caminho/projeto      # a partir do Kit
python tools/validate.py                                   # de dentro do projeto
python validators/validate.py --root . --only state        # um validador só
python validators/validate.py --root . --json              # saída estruturada
python validators/validate.py --root . --currency          # + passagem de vigência
```

Sai `0` sem erro, `1` com erro, `2` quando o alvo não é um projeto VLAEG (sem `AGENTS.md`).

## 2. Severidades

| Nível | Significa | Efeito |
|---|---|---|
| **ERROR** | violação de regra normativa | **bloqueia** declarar trabalho concluído |
| **WARNING** | sinal de degradação: algo está no limite, envelhecendo ou indisponível | não bloqueia; exige leitura |
| **INFO** | contexto sobre o que foi verificado ou pulado | nenhum |

Um aviso que ninguém lê vira erro depois. A distinção existe para que o vermelho continue
significando alguma coisa — validador cronicamente vermelho deixa de ser lido, e aí não valida
nada.

## 3. Cobertura automática

Seis validadores, **172 verificações distintas**:

| Validador | Checagens | O que prova |
|---|---|---|
| `ai-ready` | 22 | as dez capacidades, orçamentos, políticas, fronteira de escopo, ausência de segredo e dos mecanismos excluídos |
| `state` | 89 | identificadores, workstreams, tarefas, evidência, decisões, findings, auditorias, ledger, handoff, vigência |
| `skills` | 34 | metadados, camadas, gatilhos e anti-gatilhos, duplicidade por hash, sincronia com o registro |
| `links` | 2 | links markdown e caminhos citados em prosa |
| `coordination` | 16 | contrato, schemas, paridade adapter↔runtime, estado quente fora do versionamento |
| `g13` | 9 | verificação diferencial sobre a janela `base..HEAD` |

### O que cada um detecta

**Estrutura e descoberta** — núcleo residente ausente ou acima do teto · seção obrigatória
faltando · estado durável sem objetivo, comandos ou regras críticas · índice de workstreams
ausente · roteamento sem gatilhos ou sem anti-gatilhos · gates não declarados.

**Identificadores e registros** — identificador reutilizado em qualquer família · workstream órfã
(diretório sem linha, ou linha sem diretório) · nome de diretório divergente do identificador ·
status divergente entre índice e frontmatter · plano duplicado em dois caminhos.

**Trabalho e prova** — tarefa sem origem declarada · tarefa concluída sem evidência · evidência
sem comando, saída, timestamp ou commit · evidência de commit anterior ao vigente · workstream
ativa sem plano ou sem tarefa · workstream fechada com gate pendente · gate retirado sem artefato ·
aceite de fechamento assinado por agente.

**Ledger** — JSON inválido · campo obrigatório ausente · tipo fora da allowlist · autoridade
inválida · timestamp malformado · data futura · codificação não-UTF-8 · commit inexistente ·
transição de vigência sem o evento correspondente.

**Skills** — frontmatter ausente ou incompleto · nome divergente do diretório · descrição sem
gatilho negativo · camada divergente do diretório · corpo acima do teto · duas skills com o mesmo
conteúdo · registro dessincronizado do conteúdo (por hash) · skill externa sem status de aprovação ·
atualização automática não desativada.

**Segurança e fronteira** — padrão de segredo em qualquer arquivo de texto · busca entre projetos
ativada sem os quatro requisitos · política de captura incompleta · caminho central excluído do
escopo · menção aos mecanismos excluídos fora de contexto de exclusão · estado transitório
versionado.

**Diferencial (G13)** — arquivo fora do escopo declarado · teste enfraquecido · comportamento novo
sem teste · sinal silenciado · linha de ledger alterada · contrato sem paridade · evidência
incompleta · segredo no diff.

## 4. Verificações que NÃO são automatizáveis

Estas exigem julgamento. **Fingir que são mecanizáveis produziria um conjunto que sempre passa** —
e um conjunto que sempre passa não prova nada.

| # | Verificação manual | Como fazer |
|---|---|---|
| M1 | O objetivo da workstream é de fato verificável? | leia: alguém consegue dizer, olhando o sistema, se ele foi atingido? |
| M2 | As regras críticas são as que um agente violaria por não saber? | remova mentalmente cada uma: alguma quebraria algo real? |
| M3 | O nível de risco atribuído corresponde ao risco real? | a mudança toca segredo, autorização, dinheiro ou é irreversível? |
| M4 | A evidência sustenta a conclusão que ela alega sustentar? | um teste verde prova que **aquele teste** passou, não que a funcionalidade está correta |
| M5 | O plano tem critério observável por terceiro, ou só intenção? | todo critério tem comando exato? |
| M6 | O `AGENTS.md` passa no teste do aluguel, linha a linha? | delta, frequência, economia — as três |
| M7 | O revisor da Revisão de Ciclo é de fato independente do autor? | modelo distinto, processo separado, nunca subagente |
| M8 | A fonte canônica declarada é a que o código realmente usa? | siga o código, não o documento |
| M9 | O bloco "Não validado" está honesto, ou vazio por otimismo? | compare com o que foi de fato executado |
| M10 | O congelado está mesmo fora do planejamento? | procure citações a arquivo congelado em plano ou decisão recente |

M4 e M9 são as que mais falham na prática, e as duas falham do mesmo jeito: por otimismo, não por
ignorância.

## 5. Provar que o validador reprova

Um validador que só aprova não prova nada:

```bash
python scripts/kit_selfcheck.py --negative
```

O comando monta um projeto **verde** num diretório temporário, injeta **um** defeito de cada vez e
exige o código de erro esperado:

| Defeito injetado | Erro exigido |
|---|---|
| núcleo residente removido | recusa nomeada, com a causa |
| índice de workstreams removido | `ai-ready::workstreams-missing` |
| política de captura removida | `ai-ready::capture-missing` |
| workstream órfã | `state::ws-orphan` |
| tarefa concluída sem evidência | `state::task-no-evidence` |
| link para arquivo inexistente | `links::broken` |
| hash de skill divergente | `skills::registry-value` |
| caminho central excluído do escopo | `ai-ready::scope-core` |
| segredo versionado | `ai-ready::secret` |
| critério de plano com encadeamento de shell | `g13::criterio-nao-executavel` |
| critério com substituição de comando | `g13::criterio-nao-executavel` |
| critério com executável fora da allowlist | `g13::criterio-nao-executavel` |

E uma **invariante de segurança**, que não é um erro esperado mas o oposto: um projeto declara um
critério que criaria um arquivo se fosse executado, e o teste exige que **o arquivo não exista**
depois da validação. Detectar é uma coisa; ser imune é outra.

Nada é escrito dentro do Kit nem do projeto de origem.

## 6. Integridade do próprio Kit

```bash
python scripts/kit_selfcheck.py                       # + artefatos gerados e regressões F-039/F-042
python scripts/kit_selfcheck.py --drift /caminho/origem   # compara com o projeto de origem
```

O modo `--drift` existe por uma razão concreta: uma distribuição do protocolo sem verificação de
versão **dessincroniza silenciosamente** do projeto que a gerou, e ninguém percebe até adotar uma
versão que já não existe. Divergência esperada (a parametrização declarada) e divergência
inesperada (a origem evoluiu) aparecem do mesmo jeito — cabe a quem lê distinguir.

## 7. Fronteira de escopo

Um repositório que hospeda projetos independentes como subpastas **precisa declarar a fronteira**
em `.agents/policy/validator-scope.yaml`:

| Classe | Para |
|---|---|
| `excluded_paths` | projetos independentes, com validação própria |
| `excluded_harness` | estado local de ferramenta, efêmero |
| `excluded_transient` | rascunho de rodada ainda não promovido |
| `excluded_vendor` | dependências e saída de build |
| `core_paths` | caminhos que **nunca** podem ser excluídos e que G13 reconhece no escopo declarado |
| `test_path_patterns` | globs para convenções de teste específicas do projeto |

G13 não conhece nomes de produto. Uma raiz nova ou específica, inclusive com espaços, deve entrar
em `core_paths`; uma suíte que não siga as convenções embutidas deve entrar em
`test_path_patterns`. Assim, ampliar o layout não exige editar o validador.

**Caminho central não pode ser excluído.** O validador reprova a tentativa: declarar fronteira é
legítimo; silenciar a verificação para ficar verde não é.

## 8. Limitações declaradas

O protocolo declara o que **não** garante, em vez de vender garantia que não tem:

- **Exclusão por caminho não é prevenção completa de vazamento.** Ela não interpreta comando de shell arbitrário nem rastreia conteúdo citado em texto livre.
- **A detecção de concorrência é cooperativa.** Não há lock de processo: um agente que ignore a convenção sobrescreve.
- **G13 depende de controle de versão.** Sem ele não há janela diferencial, e a verificação é pulada — a garantia perdida está escrita, não escondida.
- **O validador verifica forma e vínculo, não mérito.** Ele sabe dizer que a evidência tem comando, saída, timestamp e commit; não sabe dizer se ela sustenta a conclusão. Isso é M4.
- **G14 não autentica.** Texto em Markdown é declaração, não assinatura. O validador garante que o bloco existe, nomeia um signatário declarado em `g14_signers` e não foi assinado por agente — não que a pessoa leu e aceitou.
- **A execução de critérios do plano é opt-in e não é sandbox.** Sem `--exec-criteria` nada roda. Com a flag, o comando é executado sem shell e restrito a uma allowlist — mas `python -c` executa Python arbitrário. A allowlist reduz a superfície; a fronteira real é confiar no projeto.
- **A varredura de identificadores no inventário de adoção é textual.** Ela não distingue registro real de fixture.
