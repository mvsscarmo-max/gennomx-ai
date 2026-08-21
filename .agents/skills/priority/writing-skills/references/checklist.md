# Auditoria de skill — doutrina + conformidade

Portão de saída de uma skill criada ou refatorada. Percorra contra a saída final e marque **Passa**
ou **Falha** item a item, numa auditoria escrita. Sem resumir, sem pular seção. Corrija toda Falha e
reaudite; o trabalho só termina quando todo item lê Passa.

## Parte A — Doutrina

### A1. Invocação e descrição

- [ ] **Invocação justificada:** a skill é invocada por modelo porque o agente ou outra skill precisa alcançá-la sozinho.
- [ ] **Palavra-âncora na frente:** a descrição abre com a palavra que faz o trabalho de invocação.
- [ ] **Um gatilho por ramo:** todo gatilho nomeia um ramo genuinamente distinto; sinônimos colapsados.
- [ ] **Gatilhos negativos presentes:** a descrição diz para que **não** usar.
- [ ] **Só gatilhos:** nenhuma prosa de identidade que já viva no corpo.

### A2. Hierarquia de informação

- [ ] **Conteúdo tipado:** todo bloco é passo (ação ordenada terminando em critério) ou referência. Nenhuma sequência de passos fabricada para parecer procedural.
- [ ] **Critérios verificáveis:** todo critério decide pronto × não-pronto e, onde importa, é exaustivo.
- [ ] **Divulgação por ramo:** o que todo ramo precisa está inline; o que só alguns alcançam está atrás de ponteiro.
- [ ] **Ponteiros redigidos para quando:** todo ponteiro nomeia sua condição de disparo; os que devem disparar dizem "integralmente"; nenhum "veja X para mais".
- [ ] **Co-locação:** definição, regras e ressalvas de um conceito ficam sob um mesmo título.

### A3. Poda — frase a frase

- [ ] **Fonte única:** nenhum significado em dois lugares.
- [ ] **Relevância:** toda linha ainda diz respeito ao que a skill faz.
- [ ] **Caça a no-op:** o teste foi aplicado a cada frase isolada; as que falharam foram apagadas inteiras.
- [ ] **Negação:** proibições reescritas como alvo positivo; as remanescentes são guardrails duros com o que fazer no lugar.
- [ ] **Palavras-âncora:** qualidades repetidas colapsadas em palavras únicas, cada uma forte o bastante para passar no teste de no-op.

## Parte B — Conformidade de spec

### B1. Metadados e descoberta

- [ ] **Nome:** 1–64 caracteres, minúsculas, números ou hífens simples, casando exatamente com o diretório.
- [ ] **Tamanho da descrição:** abaixo de 1.024 caracteres.
- [ ] **Cobertura de gatilho:** gatilhos positivos e negativos presentes.
- [ ] **Terceira pessoa:** a descrição evita "eu", "meu", "você", "seu".

### B2. Estrutura e caminhos

- [ ] **Pastas padrão, planas:** apenas `scripts/`, `references/`, `assets/`, cada uma com um nível.
- [ ] **Sem docs humanos:** nenhum README, CHANGELOG ou guia de instalação dentro da skill.
- [ ] **Barras normais:** todo caminho no `SKILL.md` usa `/`.
- [ ] **Caminhos de auxiliar explícitos:** invocáveis a partir da raiz do repositório, nunca dependentes do CWD.
- [ ] **Sem órfãos:** todo arquivo empacotado é alcançável por ponteiro no `SKILL.md`.

### B3. Corpo e scripts

- [ ] **Corpo enxuto:** `SKILL.md` abaixo de 500 linhas.
- [ ] **Imperativo:** instruções no imperativo em terceira pessoa.
- [ ] **Vocabulário de domínio:** usa consistentemente os termos do domínio.
- [ ] **CLI:** scripts são minúsculos e de propósito único; `stdout` no sucesso, `stderr` na falha.
- [ ] **Papel do auxiliar:** cada auxiliar rotulado somente leitura, bootstrap ou mutante.
- [ ] **Estados de falha:** onde a skill roda script ou tem falha conhecida, o `SKILL.md` diz como recuperar — e uma skill sem nenhum dos dois não carrega boilerplate de erro.

## Parte C — Contrato deste protocolo

- [ ] **Bloco `metadata` completo:** `protocol`, `layer`, `version`, `risk`, `vlaeg_phases`, `triggers`, `negative_triggers`, `produces`, `gates`.
- [ ] **Fonte declarada:** skill adaptada cita `source` com commit de origem.
- [ ] **Gates nomeados:** os gates listados existem em `docs/ai-ready/quality-gates.md`.
- [ ] **Sem sandbox:** a skill não pressupõe, exige nem recomenda sandbox, `ai-jail` ou modo YOLO.
- [ ] **Registrada:** consta em `.agents/registry/local-skills.yaml` com o mesmo caminho e versão.
- [ ] **Validador verde:** `python tools/validate.py` passa.
