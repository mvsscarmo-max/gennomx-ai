<!-- validate-links: illustrative-paths -->

# Roteamento de skills

O roteador escolhe o **conjunto mínimo** de skills. Carregar todas destrói a economia que torna
skills úteis; carregar nenhuma devolve o agente ao comportamento genérico que este protocolo existe
para corrigir.

## 1. Sinais de entrada

Avalie no `FRAME` e registre no `STATE.md`:

intenção · nível de risco (0–5) · fase VLAEG · stack · tipo de alteração · tamanho estimado do
diff · precisa pesquisar? · precisa planejar? · precisa revisar? · precisa validar? · precisa de
memória? · há continuidade? · precisa documentar?

## 2. Gatilhos obrigatórios

Disparam **sem julgamento** — se a condição vale, a skill entra:

| Condição | Skill | Camada |
|---|---|---|
| Vai escrever, corrigir ou revisar código | `no-workarounds` | prioritária |
| Vai declarar tarefa de código concluída, commitar ou abrir PR | `deslop` | prioritária |
| Vai criar ou editar o núcleo residente | `writing-agents-md` | prioritária |
| Vai criar, editar ou depurar uma skill | `writing-skills` | prioritária |
| Nível ≥ 3, ou pedido explícito de Revisão de Ciclo | `cycle-review` | protocolo |
| Mudança visível ao usuário em candidato a release | `qa-execution` | prioritária |
| Sessão nova em workstream existente | `memory-recall` | memória |
| Vai encerrar com trabalho aberto, ou trocar de agente/ferramenta | `session-handoff` | memória |
| Vai criar, pausar, retomar ou fechar workstream | `workstream-management` | memória |
| Finding verificado que vale além desta tarefa | `knowledge-promotion` | memória |
| Vai capturar, exportar ou registrar conteúdo sensível | `memory-privacy` | memória |
| Vai usar skill externa ainda não aprovada | `external-skill-intake` | protocolo |

## 3. Anti-gatilhos

Uma skill **não** entra só porque o nome parece relevante:

- `qa-execution` **não** roda em mudança sem superfície visível ao usuário, nem substitui suíte automatizada.
- `cycle-review` **não** roda durante edição ativa, nem em diff vazio, nem antes do pré-voo.
- `deslop` **não** roda em diff só de documentação ou formatação.
- `writing-skills` **não** é usada para escrever o núcleo residente nem documentação humana.
- `writing-agents-md` **não** é usada para skills sob demanda nem para README.
- `no-workarounds` **não** entra em edição só de formatação ou documentação.
- Skill de stack só entra se a stack aparece **no diff**, não se aparece no repositório.

Sem anti-gatilho declarado, a seleção volta a ser por semelhança de nome — que é exatamente o
comportamento genérico que o roteamento substitui.

## 4. Registro obrigatório da seleção

No `STATE.md`, seção `## Skills selecionadas`:

```yaml
selected_skills:
  - name: no-workarounds
    version: 1.0.0
    reason: "correção de bug com tentação de silenciar tipo"
    trigger: "escrever/corrigir código"
    expected_output: "correção na causa raiz + registro do sinal silenciado, se houver"
    mandatory: true
```

Quando um gatilho obrigatório dispara e a skill **não** é usada:

```yaml
skipped_skills:
  - name: qa-execution
    reason: "alteração sem superfície visível ao usuário — apenas job interno"
    approved_by: "agente | humano"
```

Pular gatilho obrigatório **sem** esse registro é violação de gate, detectável pelo validador.

## 5. Ordem de execução

```text
memory-recall → workstream-management → [skills de stack] → no-workarounds
→ (implementação) → deslop → cycle-review → qa-execution
→ knowledge-promotion → session-handoff
```

`no-workarounds` é um **guardrail ativo durante a implementação**, não uma etapa isolada.
`deslop` roda **antes** de `cycle-review`: a revisão não deve gastar orçamento apontando excesso que
o guardrail local removeria de graça.

## 6. Contrato de metadados de uma skill

Toda skill local declara frontmatter YAML com `name`, `description` e um bloco `metadata`:

```yaml
---
name: <kebab-case, igual ao nome do diretório>
description: <o que faz · quando usar · quando NÃO usar — em terceira pessoa>
metadata:
  protocol: VLAEG IA-ready
  layer: priority | memory | protocol | coordination
  version: <semver>
  risk: low | medium | high
  vlaeg_phases: [V, L, A, E, G]
  triggers:
    - "<condição que faz a skill entrar>"
  negative_triggers:
    - "<condição em que a skill NÃO entra, mesmo parecendo relevante>"
  produces: ["<artefato de saída>"]
  gates: ["<gate que a skill ajuda a satisfazer>"]
---
```

Regras verificáveis:

- `name` **deve** casar com o nome do diretório e usar apenas minúsculas, dígitos e hífen.
- `description` **deve** declarar o quando-usar **e** o quando-não-usar. Descrição sem gatilho negativo é reprovada.
- `layer` **deve** casar com o diretório em que a skill vive.
- Corpo da skill **deveria** caber num teto declarado de linhas; procedimento longo desce para `references/`.
- Duas skills **não devem** ter o mesmo nome nem o mesmo conteúdo (detecção por hash).

## 7. Skills externas

Nunca residentes. Gate de intake:

1. confirmar existência e commit de origem
2. ler o `SKILL.md` integralmente
3. ler **todos** os scripts
4. verificar dependências e binários exigidos
5. verificar licença
6. classificar risco
7. verificar compatibilidade com a stack
8. registrar a seleção no `STATE.md`
9. limitar o escopo da execução
10. validar a saída contra o resultado esperado

Skill com aprovação `blocked` **nunca** executa. `not-evaluated` exige intake antes do uso.
**Atualização automática é desativada**: mudar o commit de origem de uma skill externa é decisão
registrada.

## 8. Orçamento

O conjunto selecionado deve caber no orçamento de contexto. Se estourar, corte pela ordem: skills
de stack → skills de documentação → skills de memória não obrigatórias. Skills prioritárias com
gatilho disparado **não são cortáveis**; se não couberem, **divida a tarefa**.
