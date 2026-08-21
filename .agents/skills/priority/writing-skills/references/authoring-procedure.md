# Procedimento de autoria — criando uma skill nova

Mecânica de estrutura e conformidade. A doutrina do `SKILL.md` governa toda decisão de conteúdo;
este arquivo governa forma.

## Regra de caminho

Resolva caminhos empacotados a partir do diretório que contém o `SKILL.md` da skill. Ao invocar um
auxiliar de outro diretório de trabalho, escreva o caminho completo a partir da raiz do repositório
— nunca `scripts/x.py` solto, que depende silenciosamente do CWD.

## Passo 1 — Metadados

1. Defina um `name` único: 1–64 caracteres, minúsculas, números e hífens simples. Deve casar **exatamente** com o nome do diretório.
2. Redija a `description`: máximo 1.024 caracteres, terceira pessoa, com gatilhos positivos ("Use ao…") e negativos ("Não use para…").
3. Preencha o bloco `metadata` do protocolo: `protocol`, `layer`, `version`, `risk`, `vlaeg_phases`, `triggers`, `negative_triggers`, `produces`, `gates`. Skills adaptadas de fonte externa acrescentam `source` com o commit de origem.
4. Execute o validador (somente leitura):

```bash
python .agents/skills/priority/writing-skills/scripts/validate_metadata.py --path <dir-da-skill>
```

5. Corrija com base no `stderr` e repita até sair 0.

*Concluído quando:* o validador sai 0.

## Passo 2 — Estrutura de diretório

1. Crie o diretório raiz com o `name` validado, sob a camada correta: `.agents/skills/{priority,memory,protocol,coordination}/`.
2. Use apenas estes subdiretórios, cada um com um nível de profundidade:
   - `scripts/` — CLIs minúsculas e lógica determinística;
   - `references/` — contexto sob demanda: esquemas, catálogos, contratos profundos;
   - `assets/` — templates de saída, esquemas, arquivos estáticos.
3. A skill embarca apenas arquivos voltados ao agente. README, CHANGELOG e guia de instalação vivem fora dela.

*Concluído quando:* a árvore contém `SKILL.md` e apenas as pastas padrão.

## Passo 3 — Redigir o SKILL.md

1. Escreva no imperativo em terceira pessoa ("Extraia o texto", "Rode o build").
2. Mantenha abaixo de 500 linhas — o teto da spec; a barra de *sprawl* da doutrina costuma cair bem antes.
3. Decida inline × ponteiro pela seção *Hierarquia de informação* da doutrina, e redija cada ponteiro codificando **quando** carregar.
4. Termine cada passo num critério de conclusão verificável (*Concluído quando:*).
5. Rode a poda: relevância linha a linha, teste de no-op frase a frase, proibição reescrita como alvo positivo, qualidades repetidas colapsadas em palavras-âncora.

*Concluído quando:* todo bloco do rascunho está tipado — passo ou referência — e a poda tocou toda frase.

## Passo 4 — Scripts

1. Identifique tarefas frágeis (regex, parsing complexo, boilerplate repetitivo) e escreva uma CLI de propósito único para cada uma em `scripts/`.
2. Scripts se comunicam por streams: `stdout` descritivo no sucesso, `stderr` na falha, para o agente se autocorrigir.
3. Rotule cada auxiliar no `SKILL.md` como **somente leitura**, **bootstrap** ou **mutante**.

*Concluído quando:* todo auxiliar tem caminho inequívoco e rótulo de papel no `SKILL.md`.

## Passo 5 — Registro no protocolo

1. Acrescente a skill a `.agents/registry/local-skills.yaml` com nome, camada, versão, caminho, gatilhos e gates.
2. Se ela substitui um rito anterior, registre a migração e remova a duplicação — o núcleo residente fica só com o ponteiro.
3. Rode `python tools/validate.py`.

*Concluído quando:* o validador passa e a skill aparece no registro.

## Passo 6 — Auditoria final

Leia `references/checklist.md` integralmente e produza a auditoria escrita: cada item, Parte A e
Parte B, marcado Passa ou Falha contra a saída final. Corrija toda Falha e reaudite.

*Concluído quando:* a auditoria escrita mostra todo item como Passa.

## Tratamento de falhas

- **Falha de metadados:** identifique o erro específico do validador e reescreva o campo — remova pronomes de primeira/segunda pessoa, encurte, corrija o conjunto de caracteres do nome.
- **Inchaço de contexto:** se o rascunho passar de 500 linhas, extraia o maior bloco que só alguns ramos precisam para `references/`, deixando um ponteiro redigido para quando carregar.
- **Skill que ninguém dispara:** o problema quase sempre está na descrição, não no corpo — palavra-âncora ausente ou gatilhos que renomeiam um mesmo ramo.
