<!-- validate-links: illustrative-paths -->

# Níveis de risco e rito proporcional

O mesmo rito para toda alteração é burocracia num extremo e negligência no outro. O nível é
escolhido no `FRAME` e registrado no `STATE.md`. **Na dúvida entre dois níveis, suba.**

## 1. Classificação

| Nível | Nome | Exemplos |
|---|---|---|
| 0 | Consulta | ler, pesquisar, explicar, diagnosticar sem alterar arquivo |
| 1 | Trivial e reversível | typo, comentário, formatação, ajuste de texto, renomear variável local |
| 2 | Localizada | corrigir bug em um módulo, adicionar teste, ajustar função existente |
| 3 | Relevante | funcionalidade nova, refatoração multi-arquivo, mudança de contrato interno |
| 4 | Estrutural | arquitetura, schema, dependência principal, contrato público, migração de dados |
| 5 | Crítica | segurança, autenticação, dados de produção, financeiro, deploy, retenção, privacidade |

**Eleva o nível automaticamente**, qualquer que seja o tamanho do diff: tocar segredo,
autenticação, autorização, dados pessoais, cálculo financeiro, migração destrutiva — ou ser
irreversível.

## 2. Rito exigido

| Requisito | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| Plano (`PLAN-NNN`) | — | — | ✓ curto | ✓ | ✓ | ✓ |
| Aprovação humana | — | — | — | ✓ do plano | ✓ | ✓ + explícita por etapa |
| Decisão registrada (`D-NNN`) | — | — | se houver escolha | ✓ | ✓ | ✓ |
| Guardrail de causa raiz | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| Deslop | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| Testes executados | — | se existirem | ✓ | ✓ | ✓ + regressão | ✓ + regressão + caso negativo |
| G13 — verificação diferencial | — | — | ✓ | ✓ | ✓ | ✓ |
| Revisão de Ciclo (RC) | — | — | — | ✓ | ✓ | ✓ |
| QA de superfície visível | — | — | se visível | se visível | ✓ | ✓ |
| G14 — aceite humano assinado | — | — | — | ✓ | ✓ | ✓ |
| Evidência em `EVIDENCE.md` | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| Evento no ledger | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Atualização de `STATE.md` | se muda entendimento | ✓ | ✓ | ✓ | ✓ | ✓ |
| Handoff ao encerrar com trabalho aberto | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| Consolidação em `docs/` | — | — | — | ✓ | ✓ | ✓ |
| Fases VLAEG obrigatórias | — | — | A | V, A | V, L, A, G | V, L, A, E, G |

RC e G14 preservam a **não-autocertificação**: o revisor da RC é distinto do autor, e o aceite é
**só humano** — agente nunca assina G14. Uma rodada de julgamento por workstream; correção de
achado crítico é verificada por G13, nunca por uma segunda rodada de julgamento.

## 3. Piso inegociável

Nenhum nível dispensa:

- **rastreabilidade** — todo evento aponta workstream, tarefa (ou `ad-hoc`) e commit;
- **evidência** — comando + saída para qualquer alegação de funcionamento;
- **segurança** — política de captura e limites de autonomia valem em nível 0;
- **atualização de estado** — o ledger recebe registro mesmo em consulta;
- **causa raiz** — vale a partir do nível 1, sem exceção por pressa;
- **gates aplicáveis** — pular um gate exige registro do motivo, não silêncio.

## 4. Nível 0 e o ledger

Consulta registra evento porque a próxima sessão precisa saber que a investigação já ocorreu — é o
que impede reexplorar o mesmo beco sem saída. Consulta **não** produz evidência nem atualiza tarefa.

## 5. Rebaixamento

Um nível só pode ser rebaixado por humano, com registro em decisão. **Agente pode elevar sozinho;
nunca reduzir.**
