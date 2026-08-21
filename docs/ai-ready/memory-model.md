<!-- validate-links: illustrative-paths -->

# Modelo de memória e workstreams

Código é o resultado que sobreviveu; não guarda a investigação. A sessão guarda — e a sessão
pertence à ferramenta, que pode mudar de preço, limite, modelo ou formato amanhã. Este modelo tira
a memória da ferramenta e a coloca no projeto, em arquivos versionados.

## 1. Camadas

```text
sessão nativa da ferramenta A ─┐
sessão nativa da ferramenta B ─┼─ workstream ─ ledger portátil + delta + busca
sessão nativa da ferramenta C ─┘
```

O protocolo **não** converte a sessão de uma ferramenta na de outra — isso seria frágil e quebraria
a cada atualização. Cada ferramenta mantém sua sessão nativa; a workstream liga essas sessões a um
registro portátil.

## 2. Workstream

Unidade persistente de continuidade. Uma por linha de trabalho independente.

```yaml
id: WS-NNN
title: ""
objective: ""              # uma frase verificável: o que estará verdadeiro ao terminar
status: proposed           # proposed | active | paused | blocked | completed | cancelled
created_at: "AAAA-MM-DD"
updated_at: "AAAA-MM-DD"
risk_level: 0              # 0-5
current_phase:
  vlaeg: not-applicable    # V | L | A | E | G | cross-cutting | not-applicable
active_plan: null          # PLAN-NNN ou null
active_tasks: []           # [T-NNN]
agents:
  - harness: ""
    session_id: ""
    last_seen: ""          # AAAA-MM-DDTHH:MM:SSZ
branch: ""
worktree: ""
base_commit: ""
current_commit: ""
validated_commit: ""       # ponta da linhagem coberta pelas evidências
open_questions: []
risks: []
pending_gates: []          # vazio é pré-condição para fechar
last_handoff: null
```

### Ciclo de vida

```text
proposed → active → (paused | blocked) → active → completed
                                        ↘ cancelled
```

- `active` exige `objective` preenchido **e** ao menos uma tarefa.
- `paused` exige handoff gerado.
- `blocked` exige a causa em `open_questions` ou `pending_gates`.
- `completed` exige `pending_gates` vazio e evidência dos gates do nível de risco.
- `cancelled` exige motivo; a workstream **permanece** no repositório como registro.

### Ligação exigida

```text
solicitação → requisito → decisão → plano → tarefa → sessão → alteração
→ teste → evidência → conhecimento → conclusão
```

Cada elo é verificável: tarefa aponta plano (ou `ad-hoc`), evento aponta tarefa, evidência aponta
comando e commit, conhecimento aponta finding, finding aponta evidência.

### Concorrência

Uma workstream aceita **um executor por vez**. O executor se declara em `agents` com `last_seen`
atualizado. Um segundo executor que encontre `last_seen` recente de outro agente (referência: menos
de 30 minutos) registra o conflito em `open_questions` **em vez de escrever por cima**.

> **Limitação declarada:** não há lock de processo. O protocolo funciona só com arquivos, e a
> detecção de concorrência é **cooperativa**. Um agente que ignore a convenção sobrescreve. Isso
> está escrito aqui em vez de ser descoberto depois.

## 3. Ledger

Append-only, uma linha JSON por evento. **Editar linha já gravada é proibido.**

```json
{"ts":"AAAA-MM-DDTHH:MM:SSZ","ws":"WS-NNN","agent":"","session":"",
 "task":"T-NNN","commit":"","type":"test_run","authority":"evidence",
 "origin":"harness","summary":"","detail":""}
```

Campos obrigatórios: `ts`, `ws`, `agent`, `session`, `task`, `commit`, `type`, `authority`,
`origin`, `summary`, `detail`. `task` aceita `ad-hoc`; `commit` aceita `none` em projeto sem
controle de versão.

### Allowlist de tipos

`user_message` · `agent_message` · `tool_call` · `tool_result` · `command_run` · `test_run` ·
`git_checkpoint` · `decision` · `finding` · `status_change` · `currency_change` · `skill_selected` ·
`skill_skipped` · `gate_result` · `handoff` · `knowledge_proposed` · `knowledge_approved` ·
`divergence` · `coordination_message` · `coordination_ack` · `coordination_claim` ·
`coordination_conflict` · `provider_status`

Qualquer outro tipo é descartado **com anotação de perda** — o sistema não finge que importou tudo.

### Excluído sempre

Raciocínio oculto · prompts de sistema privados · credenciais · tokens · segredos · dados
confidenciais não autorizados · stores internos em formato desconhecido · arquivos excluídos pela
política de captura.

### Codificação

O ledger deve ser **UTF-8**. Codificação híbrida, UTF-16 ou controles C1 são erro. O leitor deve
detectar BOM, tentar UTF-8 estrito e, só então, cair para um fallback por linha — **nunca**
substituir bytes inválidos em silêncio, o que corromperia o registro sem deixar rastro.

## 4. Handoff

- É resumo **operacional**; não substitui ledger, decisões nem documentação normativa.
- Declara explicitamente o que **não** foi validado.
- É vinculado a branch, worktree e commit.
- Fica histórico quando o commit registrado difere do commit vigente; ser ancestral do `HEAD` **não** prova atualidade.
- Nunca declara conclusão sem apontar a evidência que a sustenta.

## 5. Promoção de conhecimento

```text
evento → evidência → finding → conhecimento candidato → revisão → aprovação
→ conhecimento ativo → regra | decisão | procedimento | armadilha
```

| Destino | Quando | Autoridade exigida |
|---|---|---|
| `docs/rules/` | vira restrição vinculante | humano |
| `DECISIONS.md` | escolha estrutural | humano |
| `docs/procedures/` | passo a passo reutilizável | humano ou agente sênior designado |
| `docs/gotchas/` | armadilha específica, verificada | agente, com evidência |
| `knowledge/experiments/` | hipótese em teste | agente |
| `knowledge/historical/` | valeu, não vale mais | qualquer |

Toda promoção declara: origem · evidência · workstream · validade · autoridade · quem aprovou ·
data de verificação · condições de supersessão.

**Auto-improvement produz proposta, nunca alteração automática** de regra normativa, política de
segurança, decisão arquitetural aprovada, limite de autonomia ou gate.

## 6. Retenção

| Registro | Retenção padrão | Purga |
|---|---|---|
| ledger de workstream ativa | indefinida | nunca |
| ledger de workstream fechada | 12 meses | compactação para digest + arquivamento |
| evidência | vida do projeto | nunca automática |
| conhecimento histórico | vida do projeto | nunca automática |
| evento com dado sensível detectado tardiamente | imediata | purga registrada em decisão |

Purga é ação de nível 5: exige aprovação humana e deixa registro do que foi purgado (metadado),
**nunca apagando o rastro de que houve purga**.

## 7. Isolamento

Uma workstream não lê o estado de outra sem referência explícita. Um projeto não lê a memória de
outro. Isolamento por cliente ou organização, quando aplicável, é declarado no `PROJECT.md` e vale
como restrição de nível 5.
