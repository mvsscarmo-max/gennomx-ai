<!-- validate-links: illustrative-paths -->

# Operação Multi-Harness

**Extensão opcional.** Aplica-se a partir do perfil 1.

## 1. Checkpoints de polling

Consulte a inbox: ao iniciar a sessão · antes de aceitar trabalho · antes de alterar contrato
compartilhado · antes de editar escopo compartilhado · ao solicitar merge · ao declarar conclusão ·
ao gerar handoff.

Fora desses pontos, não é preciso consultar — polling constante custa e não acrescenta.

## 2. Fluxo supervisionado

1. Crie ou retome a workstream canônica.
2. Registre o agente e suas capabilities.
3. Crie ou associe o trabalho a uma workstream e uma tarefa.
4. Obtenha claim do escopo.
5. Para escrita paralela, crie branch e worktree próprias. O claim confere **ambas** contra a lista real de worktrees e **falha fechado** se não conseguir verificá-las.
6. Execute, publique progresso e produza evidência.
7. Libere o claim e gere handoff ou resultado.
8. Integre em branch própria e rode os gates **sobre o resultado combinado**.

O passo 5 falha fechado por desenho: um claim que não consegue verificar o isolamento e mesmo assim
concede a posse é pior que nenhum claim, porque cria confiança injustificada.

## 3. Limites declarados

O perfil 2 usa **polling e arquivos locais**: não interrompe uma sessão aberta. Push e injeção
ativa dependem da ferramenta e não fazem parte do contrato.

Um orquestrador **não** aprova a própria mudança crítica, **não** omite conflito e **não**
interpreta silêncio como aceite.

## 4. Contratos compartilhados

Alteração de schema, API, evento, interface, migração, dependência ou política exige **mensagem de
mudança com acknowledgment dos agentes dependentes**.

A mensagem **alerta**; a decisão e a documentação continuam nos artefatos canônicos. Uma mudança de
contrato que existe apenas como mensagem trocada entre agentes não está registrada em lugar nenhum
que sobreviva à sessão.
