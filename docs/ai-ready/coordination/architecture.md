<!-- validate-links: illustrative-paths -->

# Arquitetura de coordenação Multi-Harness

**Extensão opcional.** Um projeto conforme opera sem esta camada, com um agente por vez. Adote-a
quando mais de um agente escrever no mesmo projeto ao mesmo tempo.

## 1. Divisão de responsabilidade

```text
Protocolo VLAEG IA-ready     autoridade, identificadores, workstreams, gates e contratos
Provider adapter             projeção entre o contrato e um runtime concreto
Provider de filesystem       referência e fallback dos perfis 0–2
Provider externo             experimental, sempre gated
IDE / cockpit humano         visualização, nunca fonte única
Controle de versão           registro durável e auditável
diretório de estado quente   local, não normativo, não versionado
```

A camada pertence à **infraestrutura de desenvolvimento**. O runtime do produto — backend,
frontend, banco, APIs — não importa nada dessa camada, não lê o estado quente e não depende de
daemon. Se essa fronteira for atravessada, um problema de coordenação de agentes vira incidente de
produção.

## 2. Fontes de verdade

| Registro | Fonte canônica |
|---|---|
| Regras e contratos | núcleo residente, `docs/`, contrato de coordenação |
| Skills | `.agents/skills/` |
| Workstreams e tarefas | `project_state/` |
| Estado quente | diretório local de coordenação |
| Identificadores do provider | **metadado de correlação**, nunca identidade |

O provider **pode** executar e representar estado operacional. Ele **não** aprova plano, não muda
regra, não encerra gate, não promove conhecimento e não substitui os identificadores do protocolo.

## 3. Estado quente

Presença, inbox, recibos, claims ativos, leases, locks, sockets, cache e logs ficam **fora** do
controle de versão. Conflitos materiais, evidências selecionadas e handoffs consolidados entram na
workstream **com autoridade explícita**.

A regra existe porque estado quente versionado produz conflito de merge em cada heartbeat — e
transforma um registro de infraestrutura em ruído no histórico do projeto.

## 4. Perfis operacionais

| Perfil | Modo | Provider | Capabilities |
|---|---|---|---|
| 0 | desativado | filesystem | somente protocolo e controle de versão |
| 1 | agente único | filesystem | registro, heartbeat, trabalho e handoff |
| 2 | arquivos compartilhados | filesystem | perfil 1 + mensagens, recibos, polling e claims |

O perfil 0 é o padrão. Subir de perfil é decisão registrada.

## 5. Escrita paralela

Cada agente escritor recebe **branch e worktree próprias**. O claim nomeia a posse lógica; a
worktree isola o disco. A branch de integração recebe as mudanças e executa os gates **sobre o
resultado combinado** — nunca só sobre as partes.

Claim sem worktree é acordo de cavalheiros; worktree sem claim é dois agentes editando o mesmo
arquivo em cópias diferentes. Os dois juntos é o que funciona.
