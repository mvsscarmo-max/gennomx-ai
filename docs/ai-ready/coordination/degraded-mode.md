<!-- validate-links: illustrative-paths -->

# Modo degradado

O protocolo continua operando **sem** provider externo, daemon, serviço de contexto, transporte em
tempo real, extensão de IDE ou mais de um agente.

## 1. O que sobrevive

Tudo o que é normativo. Nenhum gate, nenhuma regra e nenhum registro do protocolo depende da camada
de coordenação. O piso de conformidade é: arquivos versionados + um interpretador Python.

| Capacidade | No perfil 2 | No modo degradado |
|---|---|---|
| Registrar evento | provider | linha JSON no ledger |
| Buscar histórico | provider | `grep`/`rg` |
| Retomar trabalho | briefing + delta do provider | ler `STATE.md` + ledger |
| Passar trabalho adiante | mensagem + recibo | `HANDOFF.md` |
| Detectar conflito de escrita | claim | campo `agents` com `last_seen`, cooperativo |
| Auditar | operação do provider | rodar o validador |

## 2. Recuperação

O provider de referência preserva identificadores e registros em disco. Retry com chave idempotente
preserva o identificador dentro daquele runtime. **Uma falha não altera o estado normativo.** Depois
da recuperação, uma passagem de auditoria verifica referências e acknowledgments pendentes.

## 3. Limites declarados do fallback

O fallback de referência é **local**, usa conflito de **escopo exato** e **não** possui sessão
persistente de modelo, push, interrupção nem provisionamento automático de worktree. Essas
capabilities retornam **indisponibilidade explícita** — nunca um resultado plausível e falso.

Um sistema que degrada em silêncio é pior que um sistema que cai: o silêncio é indistinguível do
sucesso.
