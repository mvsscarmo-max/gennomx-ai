<!-- validate-links: illustrative-paths -->
<!-- Os caminhos citados em prosa descrevem a estrutura de destino num projeto que adota o
     protocolo, não o layout do repositório de origem. Links markdown continuam verificados. -->

# Protocolo VLAEG IA-ready 4.0 — especificação normativa

**Versão:** 4.0.0 · **Estado:** normativo · **Substitui:** 3.0.0 (regime de gates predicativos) ·
**Ancestral:** Protocolo VLAEG 2.0

Este documento é a fonte normativa do protocolo. Ele é suficiente para implementar o VLAEG
IA-ready 4.0 sem acesso ao repositório de onde foi extraído.

## Convenção normativa

| Termo | Significado |
|---|---|
| **DEVE** | requisito absoluto. Uma implementação que o viola **não** é conforme |
| **NÃO DEVE** | proibição absoluta |
| **DEVERIA** | recomendação forte. Ignorar exige razão registrada |
| **NÃO DEVERIA** | desaconselhado. Fazer exige razão registrada |
| **PODE** | opcional, sem prejuízo de conformidade |

Requisitos marcados **[NÚCLEO]** valem em qualquer tamanho de projeto. Os marcados
**[EXTENSÃO]** são opcionais e só se aplicam se o projeto adotar a camada correspondente.

---

## 1. Tese

A unidade de trabalho **não** é o commit nem o sprint: é a **sessão de um agente sem memória da
anterior**. Todo requisito deste documento existe para que essa sessão comece produtiva e termine
auditável.

Três invariantes governam o resto:

1. **Contexto residente é caro.** Cada linha sempre carregada tributa toda tarefa e dilui as demais regras.
2. **Memória não é verdade.** Um registro prova que algo foi dito, tentado, observado ou executado — não que continua correto.
3. **Conclusão sem evidência não é conclusão.**

## 2. AI Ready como propriedade verificável [NÚCLEO]

Um repositório **é** AI Ready quando um agente novo, sem histórico de conversa, consegue — só
lendo arquivos versionados — satisfazer as dez capacidades abaixo.

| # | Capacidade | Artefato que a satisfaz |
|---|---|---|
| 1 | Descobrir como trabalhar no projeto | `AGENTS.md` |
| 2 | Entender objetivo e arquitetura | `project_state/PROJECT.md`, `docs/architecture/` |
| 3 | Localizar a linha de trabalho ativa | `project_state/WORKSTREAMS.md` |
| 4 | Identificar a tarefa atual | `workstreams/<WS>/STATE.md` |
| 5 | Carregar só as skills necessárias | regras de roteamento + registries |
| 6 | Encontrar decisões e restrições | `DECISIONS.md`, `docs/rules/` |
| 7 | Conhecer os comandos de validação | `PROJECT.md` § Comandos |
| 8 | Retomar com segurança | `HANDOFF.md` + verificação de commit |
| 9 | Registrar o que realizou | `EVENTS.jsonl`, `STATE.md` |
| 10 | Verificar a própria entrega | gates de qualidade com prova exigida |

**R2.1** O projeto **DEVE** dispor de um comando único que verifique as dez capacidades e devolva
erro acionável — arquivo, regra violada e o que fazer.

**R2.2** Conformidade **é** o resultado desse comando. Um projeto **NÃO DEVE** declarar-se AI
Ready com base em documentação, intenção ou revisão informal.

**R2.3** O comando **DEVE** sair com código diferente de zero quando houver erro, para poder ser
usado como gate em automação.

## 3. Hierarquia de autoridade das fontes [NÚCLEO]

**R3.1** O projeto **DEVE** declarar, por escrito, a ordem de precedência entre suas fontes de
regra, e essa ordem **DEVE** ser total (sem empates).

**R3.2** Uma fonte de prioridade inferior **NÃO DEVE** enfraquecer, impedir ou contradizer uma
superior. Fidelidade histórica **NÃO** é justificativa para preservar regra.

**R3.3** A precedência de referência, do mais forte ao mais fraco, é:

```
1. Restrições legais e de segurança
2. Instrução explícita do responsável humano na sessão corrente
3. Princípios do protocolo
4. Skills prioritárias
5. Gates de conclusão e Revisão de Ciclo
6. Skills de memória e continuidade
7. Regras do projeto e decisões ativas
8. Skills de stack e skills externas aprovadas
9. Método VLAEG como lente
10. Preferências globais e defaults do agente
```

**R3.4** Preferência global **NÃO DEVE** sobrescrever regra local, decisão ativa, requisito,
segurança, padrão técnico local ou política de privacidade.

### 3.1 Exclusão normativa do isolamento externo [NÚCLEO]

**R3.5** Sandbox, `ai-jail`, modo YOLO, wrappers de execução irrestrita e qualquer recomendação de
autonomia baseada em isolamento externo estão **excluídos** deste protocolo. Uma implementação
conforme **NÃO DEVE** reintroduzi-los, e um agente **NÃO DEVE** reinterpretar esta exclusão.

A segurança neste protocolo vem de **limites de autonomia, gates, política de captura e
evidência** — nunca de contenção de processo. Consequência prática: nenhum ganho de fluidez pode
ser justificado por "roda isolado".

> Esta exclusão é a única regra do protocolo que nomeia mecanismos concretos para proibi-los. Ela
> existe porque autonomia comprada com isolamento externo transfere a responsabilidade do
> julgamento para a infraestrutura, e a infraestrutura não sabe o que a tarefa autorizava.

## 4. Camadas [NÚCLEO + EXTENSÃO]

| Camada | Conteúdo | Carregamento | Estado |
|---|---|---|---|
| 1 — Núcleo residente | `AGENTS.md` | sempre, integral | NÚCLEO |
| 2 — Skills prioritárias | guias, guardrails e sensores | por gatilho | NÚCLEO |
| 3 — Skills de memória | continuidade entre sessões | por gatilho | NÚCLEO |
| 3b — Skills do protocolo | revisão de ciclo, intake de skill externa | por gatilho | NÚCLEO |
| 4 — Skills externas | catalogadas, nunca residentes | sob demanda, após intake | RECOMENDAÇÃO |
| 5 — Método VLAEG | lente de análise e classificação | por fase da tarefa | NÚCLEO |
| 6 — Coordenação Multi-Harness | contrato, provider, claims, mensagens | sob demanda | EXTENSÃO |

**R4.1** Só a Camada 1 **PODE** ser residente. Qualquer outra camada carregada sempre viola o
orçamento de contexto.

## 5. Modelo de contexto [NÚCLEO]

**R5.1** O projeto **DEVE** separar seis tipos de contexto, e um arquivo **NÃO DEVE** misturar
dois deles.

| Tipo | Pergunta que responde | Onde vive | Frequência de mudança |
|---|---|---|---|
| Residente | Como se trabalha aqui? | `AGENTS.md` | raramente |
| Normativo | O que o sistema é e o que é proibido? | `docs/` | quando o sistema muda |
| Operacional | O que está acontecendo agora? | `STATE.md` da workstream | a cada ciclo |
| Delta | O que mudou desde a última participação **deste** agente? | ledger filtrado | a cada troca |
| Pesquisável | O que já foi tentado? | ledger, evidência, findings | append-only |
| Consolidado | O que aprendemos que vale adiante? | conhecimento, regras | por promoção aprovada |

**R5.2** O `STATE.md` **NÃO DEVE** guardar histórico; o ledger **NÃO DEVE** guardar regra; `docs/`
**NÃO DEVE** guardar estado operacional.

**R5.3** O agente **NÃO DEVE** receber histórico completo. Ele recebe briefing limitado +
workstream atual + delta + ponteiros de busca.

**R5.4** O projeto **DEVE** declarar um orçamento de contexto com, no mínimo: teto do núcleo
residente, teto do briefing, teto do delta e a ordem de corte quando estourar. Os itens
não cortáveis **DEVEM** estar nomeados.

**R5.5** Busca entre projetos **DEVE** ser desativada por padrão. Ativar exige, cumulativamente:
decisão registrada, justificativa escrita, lista explícita de projetos e data de revisão.

### 5.1 Teste do aluguel

**R5.6** Toda linha do núcleo residente **DEVE** passar nos três testes, ou ser removida ou
realocada — nunca suavizada:

1. **Delta** — muda o que o agente faria de outro jeito. Repetir boa prática geral falha.
2. **Frequência** — vale para a maioria das sessões naquele escopo. Regra de nicho desce um degrau.
3. **Economia** — mantê-la residente é mais barato que derivá-la sob demanda. O que a ferramenta já anuncia sozinha falha.

Escada de escopo, do mais caro ao mais barato:
`global → raiz do repositório → subdiretório → skill → documento linkado`.

## 6. Fluxo operacional [NÚCLEO]

```
DISCOVER   localizar instruções, protocolo, catálogo e estado
ORIENT     projeto, branch, worktree, workstream, plano, tarefa, fase
RECALL     briefing, handoff válido, decisões e findings pertinentes
FRAME      separar fato / hipótese / lacuna; classificar risco; selecionar skills
EXPLORE    inspecionar código, padrões, consumidores, testes — evidência antes de opinião
SPECIFY    requisitos, critérios de aceitação, fora de escopo, casos extremos
PLAN       etapas, arquivos, riscos, gates, skills, testes
APPROVE    aplicar limites de autonomia; pedir aprovação só quando o nível exigir
IMPLEMENT  alteração mínima, padrão local, causa raiz, sem ampliar escopo
VERIFY     testes, lint, typecheck, build, validações — com saída registrada
REVIEW     diff, regressões, segurança, arquitetura, qualidade
DESLOP     remover excesso de comentário, defesa desnecessária e complexidade introduzida
CICLO      verificação independente proporcional ao risco
RECORD     tarefa, workstream, evidência, decisões, findings
PROMOTE    propor aprendizado reutilizável — promover só com autoridade
HANDOFF    gerar handoff se há continuidade
CLOSE      fechar a workstream quando os gates forem atendidos
```

**R6.1** Etapa pulada **DEVE** ter o motivo registrado. Silêncio **NÃO** é justificativa.

**R6.2** Quais etapas são obrigatórias depende do nível de risco (§7).

## 7. Flexibilidade proporcional ao risco [NÚCLEO]

**R7.1** Toda tarefa **DEVE** receber um nível de risco de 0 a 5, escolhido no `FRAME` e registrado
no `STATE.md`.

| Nível | Nome | Exemplos |
|---|---|---|
| 0 | Consulta | ler, pesquisar, explicar, diagnosticar sem alterar arquivo |
| 1 | Trivial e reversível | typo, comentário, formatação, renomear variável local |
| 2 | Localizada | corrigir bug em um módulo, adicionar teste, ajustar função existente |
| 3 | Relevante | funcionalidade nova, refatoração multi-arquivo, contrato interno |
| 4 | Estrutural | arquitetura, schema, dependência principal, contrato público, migração de dados |
| 5 | Crítica | segurança, autenticação, dados de produção, financeiro, deploy, retenção, privacidade |

**R7.2** O nível **DEVE** ser elevado, qualquer que seja o tamanho do diff, quando a mudança toca
segredo, autenticação, autorização, dados pessoais, cálculo financeiro, migração destrutiva, ou é
irreversível.

**R7.3** Na dúvida entre dois níveis, o agente **DEVE** escolher o maior.

**R7.4** Um agente **PODE** elevar o nível sozinho. Um agente **NÃO DEVE** rebaixá-lo: rebaixamento
exige humano, com decisão registrada.

**R7.5** O rito por nível está em [docs/risk-levels.md](risk-levels.md). Nenhum nível dispensa
o piso inegociável: rastreabilidade, evidência, segurança, atualização de estado, causa raiz e
gates aplicáveis.

## 8. Workstreams [NÚCLEO]

**R8.1** A workstream **é** a unidade persistente de continuidade — sobrevive à sessão, ao agente e
à ferramenta. O projeto **DEVE** manter uma workstream por linha de trabalho independente.

**R8.2** Toda workstream **DEVE** ligar, de forma verificável:

```
solicitação → requisito → decisão → plano → tarefa → sessão → alteração
→ teste → evidência → conhecimento → conclusão
```

Cada elo **DEVE** ser verificável: tarefa aponta plano (ou declara `ad-hoc`), evento aponta tarefa,
evidência aponta comando e commit, finding aponta evidência, conhecimento aponta finding.

**R8.3** Ciclo de vida:

```
proposed → active → (paused | blocked) → active → completed
                                        ↘ cancelled
```

| Estado | Pré-condição |
|---|---|
| `active` | objetivo preenchido **e** ao menos uma tarefa em andamento |
| `paused` | handoff gerado |
| `blocked` | causa registrada em questões abertas ou gates pendentes |
| `completed` | gates pendentes vazios e evidência dos gates do nível de risco |
| `cancelled` | motivo registrado; a workstream permanece no repositório |

**R8.4** Workstream concluída ou cancelada **NÃO DEVE** ser apagada. Fechada não é apagada.

**R8.5** Uma workstream aceita **um executor por vez**. O executor se declara com carimbo de
última atividade. Um segundo executor que encontre atividade recente de outro **DEVE** registrar o
conflito em vez de escrever por cima.

> O protocolo declara a limitação em vez de vendê-la resolvida: **não há lock de processo**. A
> detecção de concorrência é cooperativa.

## 9. Autoridade da informação [NÚCLEO]

**R9.1** Em conflito, vale a ordem abaixo — e é a **ordem**, não a recência, que decide:

```
1.  Código, configuração e schema atuais
2.  Requisitos aprovados
3.  Regras normativas
4.  Decisões ativas
5.  Testes e evidências recentes
6.  Conhecimento consolidado
7.  Estado operacional
8.  Handoff
9.  Ledger
10. Transcrição bruta
```

Exceção a essa ordem **DEVE** ter justificativa escrita no `STATE.md`.

> A ordem não diz "o código está certo". Diz "o código é o que **é**". Um teste recente que
> reprova o código não torna o código correto — torna o código defeituoso.

**R9.2** Todo registro **DEVE** carregar um nível de autoridade. Sem nível declarado, o padrão é
`hypothesis`.

| Nível | Significa | Quem pode criar | Vira regra? |
|---|---|---|---|
| `normative` | regra vinculante do projeto | humano | já é |
| `approved-decision` | escolha estrutural aprovada | humano | já é |
| `verified-knowledge` | aprendizado revisado e aprovado | humano aprova, agente propõe | sim, por promoção |
| `operational-state` | o que está acontecendo agora | agente | não |
| `evidence` | comando executado e sua saída | agente | não, mas fundamenta |
| `hypothesis` | suposição não verificada | agente | nunca sem verificação |
| `historical` | verdadeiro no passado, não revalidado | qualquer | não |
| `superseded` | substituído por registro mais novo | qualquer | não |

**R9.3** Divergência entre documentação e código: **o código vence**. O agente **DEVE** registrar a
divergência como finding e corrigir o documento — **não** o código, salvo se a tarefa for
exatamente essa. Se o código contradiz uma **decisão ativa**, o agente **DEVE** parar, registrar o
finding e propor decisão substituta.

**R9.4** Registro **NÃO DEVE** ser apagado quando deixa de valer. Ele recebe marcação de
supersessão e o novo registro referencia o antigo.

## 10. Estado canônico e registros [NÚCLEO]

**R10.1** O projeto **DEVE** declarar suas camadas de fonte única de verdade, com autoridade
decrescente, e **NÃO DEVE** criar um segundo sistema de estado em paralelo.

**R10.2** Regras de desempate entre documentos:

1. o **código** vence o documento;
2. entre documentos, a **camada mais alta** vence;
3. dentro da mesma camada, o registro **mais recente** vence.

**R10.3** Os artefatos mínimos de estado são:

| Artefato | Papel | Obrigatório |
|---|---|---|
| `AGENTS.md` | núcleo residente: rotear e vincular | sim |
| `project_state/PROJECT.md` | o que é durável do projeto | sim |
| `project_state/WORKSTREAMS.md` | índice das linhas de trabalho | sim |
| `workstreams/<WS>/STATE.md` | o agora de uma linha de trabalho | sim |
| `workstreams/<WS>/EVENTS.jsonl` | ledger append-only | sim |
| `workstreams/<WS>/EVIDENCE.md` | prova executada | sim |
| `workstreams/<WS>/HANDOFF.md` | contrato de passagem | quando há continuidade |
| `project_state/DECISIONS.md` | escolhas estruturais | na primeira decisão |
| `project_state/FINDINGS.md` | descobertas reutilizáveis | no primeiro finding |
| `project_state/plans/` | planos multi-sessão | na primeira iniciativa de nível ≥ 2 |
| `project_state/knowledge/` | conhecimento promovido | na primeira promoção |
| `project_state/AUDITS.md` | índice de auditorias | na primeira auditoria |

Detalhe completo em [CANONICAL-STATE.md](canonical-state.md).

### 10.1 Ledger

**R10.4** O ledger **DEVE** ser append-only, uma linha JSON válida por evento. Editar linha já
gravada é **proibido**, salvo normalização de codificação autorizada por decisão registrada.

**R10.5** Todo evento **DEVE** conter: `ts`, `ws`, `agent`, `session`, `task`, `commit`, `type`,
`authority`, `origin`, `summary`, `detail`. O campo `task` aceita `ad-hoc`; `commit` aceita `none`
em projeto sem controle de versão.

**R10.6** O projeto **DEVE** declarar uma allowlist de tipos de evento. Tipo fora da lista **DEVE**
ser descartado **com anotação de perda** — o sistema não finge que importou tudo.

**R10.7** O ledger **NÃO DEVE** conter: raciocínio oculto, prompts de sistema privados,
credenciais, tokens, segredos, dados confidenciais não autorizados ou formatos binários
desconhecidos.

**R10.8** O ledger **DEVE** ser UTF-8.

**R10.9** Um evento prova **apenas** que aquilo aconteceu naquele momento, naquele commit. Ele
**não** prova que a solução ainda funciona, que a decisão continua válida, que o caminho descartado
continua inviável, nem que o teste ainda passa.

### 10.2 Evidência

**R10.10** Evidência **é** comando + saída + timestamp + commit. Faltando qualquer um dos quatro, é
hipótese.

**R10.11** Resumo **NÃO É** evidência. Saída capturada antes da última alteração é `historical`.

**R10.12** O bloco "Não provado" no arquivo de evidência **DEVE** existir e **NÃO DEVE** ficar
vazio por otimismo.

### 10.3 Handoff

**R10.13** O handoff **DEVE** estar vinculado a branch, worktree e commit, e **DEVE** declarar
explicitamente o que **não** foi validado.

**R10.14** O handoff passa a `historical` quando o commit registrado difere do commit vigente no
`STATE.md`. Ser ancestral do `HEAD` **NÃO** prova atualidade.

**R10.15** O handoff **NÃO DEVE** declarar conclusão sem apontar a evidência que a sustenta, e
**NÃO** substitui ledger, decisões nem documentação normativa.

## 11. Vigência do estado [NÚCLEO]

**R11.1** O projeto **DEVE** ter critério objetivo para responder "este registro ainda vale?".
Perda de vigência **NÃO DEVE** ocorrer por "parecer desatualizado".

**R11.2** Vocabulário de status **DEVE** ser fechado por tipo de registro. Status fora da lista é
inválido.

**R11.3** Toda transição de vigência **DEVE** gerar evento no ledger com o motivo. Transição
detectada sem evento correspondente é erro.

**R11.4** Data futura em qualquer registro é erro.

**R11.5** Conteúdo congelado **NÃO DEVE** orientar planejamento, priorização ou decisão, salvo
consulta explícita declarada no `STATE.md`. Arquivo congelado **DEVE** carregar banner de
congelamento na primeira linha.

Critérios completos por tipo em [docs/state-currency.md](state-currency.md).

## 12. Skills [NÚCLEO]

**R12.1** As skills locais **DEVEM** ter **uma única fonte canônica** no repositório. Um registro
**PODE** indexá-las; ele **NÃO DEVE** copiá-las.

**R12.2** O roteador **DEVE** selecionar o **conjunto mínimo**. Carregar todas destrói a economia
que torna skills úteis.

**R12.3** O projeto **DEVE** declarar gatilhos obrigatórios **e** anti-gatilhos. Sem anti-gatilho,
a seleção volta a ser por semelhança de nome.

**R12.4** Quando um gatilho obrigatório dispara e a skill **não** é usada, o agente **DEVE**
registrar a omissão com motivo e quem aprovou.

**R12.5** Skill externa **NÃO DEVE** ser residente e **NÃO DEVE** executar antes de passar por
intake: existência e commit de origem, leitura integral, auditoria dos scripts, dependências,
licença, classificação de risco, compatibilidade, registro da seleção, escopo limitado e validação
da saída.

**R12.6** Atualização automática de skill externa **DEVE** estar desativada. Mudar o commit de
origem é decisão registrada.

**R12.7** Skill com aprovação `blocked` **NÃO DEVE** executar em nenhuma circunstância.

Contrato de metadados e roteamento em [docs/skill-routing.md](skill-routing.md).

## 13. Gates de conclusão [NÚCLEO]

**R13.1** Um gate **é** uma condição observável por terceiro. Se só o agente consegue afirmar que
passou, **não é gate** — é opinião.

**R13.2** Nenhuma tarefa que altera arquivos **DEVE** ser declarada concluída sem todos os gates
aplicáveis ao seu nível de risco, com evidência executada anexada.

| Gate | Prova exigida |
|---|---|
| G1 — Build/verificação | comando declarado no projeto, executado, saída registrada |
| G2 — Testes | comando + saída; teste novo para comportamento novo; regressão vermelha antes / verde depois para correção de bug |
| G3 — Lint / typecheck | comando + saída, quando o projeto declara |
| G4 — Causa raiz | nenhum sinal silenciado sem a válvula de escape documentada |
| G5 — Deslop | bloco na evidência com resumo de 1–3 frases do que foi removido |
| G6 — Escopo | o diff contém apenas o que a tarefa declarou |
| G7 — Estado | `STATE.md`, ledger e evidência atualizados |
| G8 — Rastreabilidade | alteração ligada a tarefa; tarefa ligada a plano ou marcada `ad-hoc` |
| G9 — Segredos | nenhum segredo no diff nem no ledger |
| G10 — Documentação | doc afetado atualizado, ou finding explicando por que não |
| G13 — Verificação diferencial | nível ≥ 2: detectores determinísticos sobre a janela `base..HEAD`, recomputáveis |
| G14 — Aceite de fechamento | nível ≥ 3: bloco assinado por **humano**. Agente **NÃO DEVE** assinar |

**R13.3** Os identificadores G11 e G12 estão **aposentados** e **NÃO DEVEM** ser reutilizados.
Artefatos produzidos sob eles permanecem como registro histórico, nunca como prova de conclusão.

**R13.4** A fase **RC — Revisão de Ciclo** (nível ≥ 3) **DEVE** ocorrer **uma vez por workstream**,
antes do commit de fechamento, e **PODE** barrar o fechamento. Não existe rodada 2 de julgamento;
correção de achado crítico é verificada por G13.

**R13.5** O revisor da RC **DEVE** ser independente do autor: modelo distinto e, no mesmo ambiente,
processo separado — nunca subagente do próprio autor.

**R13.6** Antes de gastar uma invocação de revisor, o pré-voo **DEVE** passar: gate verde agora ·
diff não vazio · sem artefato local · sem marcador de trabalho em andamento · gerados
co-embarcados · escopo revisável.

**R13.7** Princípio da RC: **liberal na notação, estrito no julgamento**. Diferença de caractere,
seta ASCII, travessão simples e contador desalinhado **NÃO DEVEM** reprovar rodada nem consumir
orçamento. Contrato não avaliado, tabela de paridade ausente e autor igual a revisor **DEVEM**
reprovar.

### 13.1 O que invalida uma alegação de conclusão

**R13.8** Cada um dos itens abaixo **é falsificação de evidência**, não erro de forma:

- teste não executado descrito como aprovado;
- teste enfraquecido, marcado como ignorado ou com asserção removida para passar;
- evidência colada de execução anterior ao último commit;
- "deve funcionar", "provavelmente passa", "não consegui rodar mas está correto";
- resumo apresentado no lugar da saída do comando;
- gate pulado sem registro do motivo.

**R13.9** Falha parcial **DEVE** ser declarada como parcial: o que passou é registrado com
evidência, o que não foi validado é declarado, a tarefa **NÃO** é marcada concluída, e o gate falho
vira bloqueio visível — não nota de rodapé.

## 14. Limites de autonomia [NÚCLEO]

**R14.1** O projeto **DEVE** declarar três conjuntos explícitos:

**Sem aprovação:** ler, pesquisar, rodar testes e validadores, explorar, propor plano, implementar
tarefa já aprovada dentro do escopo, atualizar o estado do próprio trabalho, gerar handoff.

**Exige aprovação humana:** aprovar plano de nível ≥ 3, mudar arquitetura ou schema, alterar
estrutura de dados, deploy, publicação, apagar memória, promover conhecimento a regra ou decisão.

**Proibido:** versionar segredo; declarar aprovado um teste não executado; enfraquecer teste para
passar; apagar histórico auditável; reescrever linha de ledger já gravada; ampliar escopo em
silêncio; adotar os mecanismos excluídos em §3.1.

## 15. Memória e privacidade [NÚCLEO]

**R15.1** O protocolo define **contratos**, não uma ferramenta. Qualquer implementação que
satisfaça a interface serve. O modo de referência — e o piso de conformidade — é **arquivos
versionados**.

**R15.2** O projeto **DEVE** continuar operando sem provider externo, sem daemon e sem rede, em
modo degradado declarado.

**R15.3** A política de captura **DEVE** ser aplicada **antes** de qualquer persistência ou
transmissão, e **DEVE** declarar, no mínimo: caminhos ignorados, allowlist de tipos de evento e
padrões de redação.

**R15.4** O projeto **DEVE** declarar que exclusão por caminho **não** é prevenção completa de
vazamento. Vender garantia falsa é pior que declarar o limite.

**R15.5** Purga de conteúdo é ação de nível 5: exige aprovação humana e **DEVE** deixar registro
de que houve purga, sem apagar o rastro.

## 16. Promoção de conhecimento [NÚCLEO]

**R16.1** O funil **DEVE** ser respeitado:

```
evento → evidência → finding → conhecimento candidato → revisão → aprovação
→ conhecimento ativo → regra | decisão | procedimento | armadilha
```

**R16.2** Nenhuma transcrição ou saída de agente vira regra automaticamente. Auto-improvement
produz **propostas**; **NÃO DEVE** alterar regra normativa, política de segurança, decisão
arquitetural aprovada, limite de autonomia ou gate.

**R16.3** Toda promoção **DEVE** declarar: origem · evidência · workstream · validade · autoridade ·
quem aprovou · data de verificação · condições de supersessão.

**R16.4** Conhecimento que não sabe dizer quando deixa de valer **NÃO DEVE** ser promovido.

## 17. Método VLAEG como lente [NÚCLEO]

**R17.1** V-L-A-E-G **é** a identidade do protocolo e funciona como **lente**, não como funil
obrigatório.

| Fase | Pergunta |
|---|---|
| **V — Visão** | Que problema, para quem, com que critério de sucesso? |
| **L — Link** | As conexões existem e respondem? |
| **A — Arquitetura** | Quais módulos, responsabilidades, dados e fluxos? |
| **E — Estilo** | O usuário entende, decide e age? |
| **G — Gatilho** | Opera de forma confiável e observável? |

**R17.2** Cada tarefa **DEVE** declarar o estado de cada fase: `aplicável` · `parcial` · `não
aplicável` · `obrigatória por risco`. Declarar `não aplicável` é resposta legítima; **presumir
não é**.

**R17.3** Nenhuma tarefa pequena **DEVE** percorrer as cinco fases por obrigação.

**R17.4** Princípios do VLAEG preservados como normativos:

- **Dados primeiro** — entrada, origem, fonte da verdade, campos obrigatórios, validações e payload de saída antes de construir.
- **Lógica determinística** — IA sugere, classifica e auxilia; código determinístico valida, calcula, registra e executa. Cálculo financeiro, autorização, integração oficial e atualização de registro produtivo **NÃO DEVEM** depender de inferência.
- **Fonte única da verdade** — o projeto declara sua fonte primária e a precedência entre fontes concorrentes.
- **Autocorreção estruturada** — analisar → isolar → corrigir → testar → documentar → prevenir recorrência.
- **Segurança desde o início** — entra na Visão, não é fase final.

## 18. Coordenação Multi-Harness [EXTENSÃO]

**R18.1** Esta camada é **opcional**. Um projeto conforme **PODE** operar com um agente por vez sem
implementá-la.

**R18.2** Quando adotada, o provider de coordenação **DEVE** estar **abaixo** do protocolo na ordem
de autoridade. Workstreams, planos e tarefas permanecem canônicos; IDs internos do provider são
**correlações**, nunca identidade.

**R18.3** Invariantes que **DEVEM** valer em qualquer provider:

- mensagem aceita **não é** acknowledgment;
- recibo **não é** conclusão;
- presença **não é** progresso;
- evento de provider **não é** regra;
- ausência de resposta **nunca** é aprovação;
- escrita paralela **exige** worktree própria.

**R18.4** Capability emulada **NÃO DEVE** ser anunciada como suporte nativo. Operação desativada e
operação não suportada **DEVEM** ter erros distintos.

**R18.5** O estado quente do provider (presença, inbox, recibos, claims, leases, locks)
**NÃO DEVE** ser versionado. Conflitos materiais, evidências e handoffs consolidados entram na
workstream com autoridade explícita.

Detalhe em [docs/coordination/architecture.md](coordination/architecture.md) e
[docs/coordination/contract.md](coordination/contract.md).

## 19. Anti-patterns proibidos [NÚCLEO]

Uma implementação conforme **NÃO DEVE** apresentar:

núcleo residente gigante · duplicação entre protocolo e skills · duplicação entre workstream e
estado global · carregar todas as skills · memória tratada como verdade · resumo tratado como
evidência · promoção automática a regra normativa · atualização silenciosa de skill externa ·
busca global entre projetos por padrão · histórico sem retenção · captura indiscriminada ·
documentação que não corresponde ao código · plano sem critério de validação · tarefa sem origem ·
decisão sem autoridade · gate opinativo · VLAEG rígido para toda mudança · remover a identidade
VLAEG sem necessidade · preservar VLAEG contra prioridade superior · qualquer forma de autonomia
comprada por isolamento externo (§3.1).

## 20. Adoção gradual [NÚCLEO]

**R20.1** Um projeto pequeno **PODE** começar com quatro arquivos: `AGENTS.md`,
`project_state/PROJECT.md`, `project_state/WORKSTREAMS.md` e uma workstream com `STATE.md`.

**R20.2** `DECISIONS.md` nasce na primeira decisão estrutural; `plans/` na primeira iniciativa
multi-sessão; `knowledge/` na primeira promoção; `AUDITS.md` na primeira auditoria.

**R20.3** O que **NÃO É** negociável em nenhum tamanho de projeto:

1. descoberta a partir do núcleo residente;
2. estado em arquivo versionado;
3. evidência antes de conclusão;
4. nenhuma prioridade inferior enfraquecendo uma superior.

## 21. Identificadores [NÚCLEO]

**R21.1** Todo registro do projeto **DEVE** ter identificador estável, e cada família **DEVE** viver
numa camada declarada da fonte única de verdade.

**R21.2** **Identificadores NÃO DEVEM ser reutilizados** — nem os de linhas de trabalho canceladas,
nem os de tarefas que nunca começaram, nem os de descobertas resolvidas, nem os de gates
aposentados.

**R21.3** Cada família **DEVE** declarar: onde o identificador nasce, onde vive, quem o aloca, seus
estados válidos e o que o valida.

**R21.4** Identificador local a um documento (itens numerados dentro de um parecer, auditoria ou
plano) **NÃO DEVE** entrar no ledger global sem promoção explícita, e a promoção **DEVE** citar o
identificador local de origem.

**R21.5** Identificador de proveniência externa **DEVE** carregar namespace explícito e **NÃO DEVE**
ser resolvido contra o estado local. Homônimo não é o mesmo registro.

**R21.6** Numeração local a uma workstream (evidência, por exemplo) **DEVE** ser prefixada ao ser
citada de fora.

Mapa completo das famílias, correlação e erros comuns em
[IDS-AND-REGISTRIES.md](ids-and-registries.md).

---

## Apêndice A — Checklist de conformidade

Um projeto é conforme ao VLAEG IA-ready 4.0 quando **todos** os itens abaixo são verdadeiros e
verificáveis por comando ou inspeção de terceiro. Os códigos de verificação estão em
[VALIDATION.md](validation.md).

- [ ] Existe núcleo residente com precedência, ordem de descoberta, limites de autonomia, evidência e comandos (R2.1, R14.1)
- [ ] O núcleo residente respeita o teto declarado de tamanho (R5.4, R5.6)
- [ ] Existe arquivo durável com objetivo, comandos e regras críticas (R2, cap. 2 e 7)
- [ ] Existe índice de workstreams, e toda workstream indexada tem diretório, e vice-versa (R8.1)
- [ ] Toda workstream ativa tem objetivo, plano e tarefa em andamento (R8.3)
- [ ] Toda tarefa declara origem; toda tarefa concluída aponta evidência executada (R8.2, R10.10)
- [ ] O ledger é JSON válido por linha, com os onze campos, em UTF-8 (R10.4–R10.8)
- [ ] Handoff aponta commit e declara o que não foi validado (R10.13–R10.15)
- [ ] Identificadores nunca são reutilizados (R21.2)
- [ ] Skills têm fonte canônica única, com gatilhos e anti-gatilhos declarados (R12.1–R12.3)
- [ ] Nenhuma skill externa instalada sem intake registrado (R12.5–R12.7)
- [ ] Existe orçamento de contexto com busca entre projetos desativada (R5.4, R5.5)
- [ ] Existe política de captura com caminhos ignorados, allowlist e redação (R15.3)
- [ ] Nenhum segredo versionado (R14.1, G9)
- [ ] Os mecanismos de §3.1 não aparecem como adoção em nenhum documento (R3.5)
- [ ] Gates declarados com prova exigida por gate (R13.1, R13.2)
- [ ] Existe comando único de conformidade que sai diferente de zero em erro (R2.1, R2.3)
