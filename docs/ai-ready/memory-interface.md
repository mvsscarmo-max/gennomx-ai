<!-- validate-links: illustrative-paths -->

# Interface de memória

O protocolo define **contratos**, não uma ferramenta. Qualquer implementação que satisfaça esta
interface serve: arquivos Markdown/YAML/JSONL versionados, banco local, ou um provider externo.

O modo de referência — e o **piso de conformidade** — é **arquivos versionados**. Se o provider
cair, o protocolo continua operando em modo degradado sem perda de rastreabilidade.

## 1. Operações

| Operação | Entrada | Saída | Efeito no modo arquivos | Autonomia |
|---|---|---|---|---|
| `start_workstream` | título, objetivo, nível de risco | `WS-NNN` | cria diretório + linha no índice | livre |
| `resume_workstream` | ws_id, agente | briefing + delta | lê `STATE.md`, filtra ledger por `last_seen` | livre |
| `pause_workstream` | ws_id, motivo | ok | `status: paused` + handoff obrigatório | livre |
| `close_workstream` | ws_id | ok | exige gates pendentes vazios; `status: completed` | livre se gates verdes |
| `create_handoff` | ws_id, alvo | caminho | escreve `HANDOFF.md` a partir do template | livre |
| `record_event` | evento | ok | append no ledger | livre |
| `search` | query, escopo, limite | eventos | busca textual em ledger, findings, decisões, conhecimento | livre |
| `propose_knowledge` | finding_id, destino | `K-NNN` candidato | escreve em `knowledge/candidates/` | livre |
| `approve_knowledge` | `K-NNN`, aprovador | ok | move para o destino + registra autoridade | **humano** |
| `supersede_knowledge` | id, novo_id | ok | marca supersessão, nunca apaga | humano para normativo |
| `purge` | seletor, motivo | relatório | remove conteúdo, preserva metadado da purga | **humano** (nível 5) |
| `audit` | escopo | relatório | roda o validador de estado | livre |

## 2. Contratos invariantes

1. **Append-only** — `record_event` nunca reescreve linha existente.
2. **Sanitização antes da persistência** — nenhuma operação grava sem passar pela política de captura.
3. **Autoridade explícita** — todo registro nasce com nível; ausente = `hypothesis`.
4. **Idempotência de retomada** — `resume_workstream` chamada duas vezes não duplica eventos.
5. **Degradação declarada** — se o provider não entende um formato, o evento é descartado **com anotação de perda**; não se finge importação completa.
6. **Sem isolamento externo** — nenhuma operação assume, exige ou recomenda contenção de processo.

## 3. Modo degradado

Sem provider algum, o agente executa a interface manualmente:

| Operação | Equivalente manual |
|---|---|
| `record_event` | acrescentar uma linha JSON ao ledger |
| `search` | `rg "termo" project_state/` |
| `resume_workstream` | ler `STATE.md` + ledger a partir do `last_seen` |
| `create_handoff` | preencher o template de handoff |
| `audit` | rodar o validador |

Este modo é suficiente para satisfazer **todos** os gates do protocolo. Nenhuma funcionalidade
normativa depende de ferramenta específica — e é o que garante que o protocolo sobreviva à troca da
ferramenta.
