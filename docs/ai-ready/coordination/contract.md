<!-- validate-links: illustrative-paths -->

# Contrato de Coordination Provider

**Extensão opcional.** Adotada a camada, o contrato executável vive em
`.agents/coordination/contract.yaml` e os schemas públicos em `.agents/coordination/schemas/`.

No Kit, os schemas estão em `schemas/coordination/`; o bootstrap só os instala com
`--with-coordination`, porque um projeto de um agente por vez não deve carregar o contrato de uma
camada que não opera.

## 1. Invariantes

Valem em **qualquer** provider, presente ou futuro:

- Provider é **opcional, substituível e abaixo do protocolo** na ordem de autoridade.
- Workstreams, planos e tarefas permanecem canônicos.
- Identificadores internos do provider são **correlações**, nunca identidade.
- **Mensagem aceita não é acknowledgment.**
- **Recibo não é conclusão.**
- **Presença não é progresso.**
- **Evento de provider não é regra.**
- **Ausência de resposta nunca é aprovação.**
- Escrita paralela **exige** worktree.
- Polling passivo é o baseline.

Cada uma dessas frases nega uma inferência que parece razoável e não é. São exatamente as
inferências que transformam um sistema de mensagens em um sistema de decisões acidental.

## 2. Capabilities

Cada adapter classifica **toda** capability relevante como `supported`, `partially_supported`,
`emulated`, `unsupported` ou `unverified`. **Emulação nunca é anunciada como suporte nativo.**

Erros distintos para casos distintos:

| Situação | Erro |
|---|---|
| operação existe mas está desativada | `capability-not-enabled` |
| operação não existe neste provider | `capability-not-supported-by-provider` |
| contenção de lock além do limite | `coordination-busy` |
| falha de acesso ao runtime | `filesystem-error` |

O chamador **pode** repetir a operação, mas **nunca** deve interpretar qualquer desses erros como
sucesso. Reservar um nome de operação **não** equivale a implementá-la.

## 3. Identificadores

São únicos por projeto e **alocados pelo protocolo**. O provider de referência usa contador
protegido por lock atômico. Adapters futuros **recebem ou correlacionam** o identificador canônico
antes de chamar o runtime — nunca inventam o seu e chamam de canônico.

## 4. Mensagens

Carregam projeto, workstream, tarefa, remetente, destinatários, tipo, prioridade e regra de
acknowledgment. Mensagem crítica exige **recibo explícito de cada destinatário**.

Retry com a mesma chave de idempotência **e o mesmo envelope** preserva o identificador da
mensagem; reutilizar a chave com **outro** envelope falha com erro de identificador duplicado.

## 5. Claims

Detectam conflito de **escopo exato**. Leitura coexiste com leitura; qualquer claim de escrita ou
exclusivo conflita com outro agente no mesmo escopo. **Lease expirado não preserva posse.** Token
de fencing impede liberação obsoleta.

O limite é declarado: conflito de escopo exato não detecta sobreposição parcial de caminho. Isso
é limitação da v1, escrita aqui em vez de descoberta em produção.

## 6. Autoridade

Pedidos de decisão e aprovação **podem** trafegar pelo provider, mas **somente o artefato governado
pelo protocolo adquire autoridade**. Uma aprovação que existe apenas como mensagem não é aprovação
— é uma mensagem sobre uma aprovação que ainda não foi registrada.

## 7. Recuperação e fallback

O provider de referência preserva identificadores e registros em disco. Retry com chave idempotente
preserva o identificador dentro daquele runtime. Uma falha **não altera o estado normativo**.
Depois da recuperação, uma passagem de auditoria verifica referências e acknowledgments pendentes.

Providers futuros precisam implementar importação e reconciliação **sem duplicar** mensagem,
recibo, claim ou conclusão **antes** de assumir o runtime. Enquanto essa reconciliação não existir,
o provider permanece inativo e o filesystem continua padrão.

O fallback ocorre **antes** da ativação: um provider experimental indisponível não assume o
runtime. Failover depois que outro provider já emitiu identificadores e eventos é capability
reservada — a operação **pausa** em vez de fingir continuidade.
