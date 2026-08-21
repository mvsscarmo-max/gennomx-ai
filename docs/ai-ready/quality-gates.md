<!-- validate-links: illustrative-paths -->

# Gates de qualidade e verificação

Um gate é uma condição **observável por terceiro**. Se só o agente consegue afirmar que passou,
não é gate — é opinião.

## 1. Gates mínimos de conclusão

Nenhuma tarefa que altera arquivos é concluída sem todos os aplicáveis ao seu nível de risco
([risk-levels.md](risk-levels.md)):

| Gate | Prova exigida |
|---|---|
| **G1 — Build/verificação** | comando declarado no `PROJECT.md`, executado, saída registrada |
| **G2 — Testes** | comando + saída; teste novo para comportamento novo; regressão vermelha antes / verde depois para correção de bug |
| **G3 — Lint / typecheck** | comando + saída, quando o projeto declara |
| **G4 — Causa raiz** | nenhum sinal silenciado sem a válvula de escape documentada |
| **G5 — Deslop** | bloco em `EVIDENCE.md` marcado com o gate e resumo de 1–3 frases |
| **G6 — Escopo** | o diff contém apenas o que a tarefa declarou; arquivo fora do escopo exige justificativa |
| **G7 — Estado** | `STATE.md`, ledger e `EVIDENCE.md` atualizados |
| **G8 — Rastreabilidade** | alteração ligada a tarefa; tarefa ligada a plano (nível ≥ 2) ou marcada `ad-hoc` |
| **G9 — Segredos** | nenhum segredo no diff nem no ledger |
| **G10 — Documentação** | doc afetado atualizado, ou finding registrado explicando por que não |
| **G11 · G12** | `aposentados` — identificadores reservados para sempre; artefatos selados sob eles permanecem como histórico, nunca como prova |
| **G13 — Verificação diferencial** | nível ≥ 2: detectores determinísticos sobre `base_commit..HEAD`, recomputáveis, saída registrada |
| **G14 — Aceite de fechamento** | nível ≥ 3: bloco assinado por humano em `EVIDENCE.md` — leu resumo do diff, G13 e RC; aceita ou nomeia findings com prazo. **Agente nunca assina** |

A fase **RC — Revisão de Ciclo** (risco ≥ 3) não é um número de gate: é a etapa de julgamento, com
**uma** invocação de revisor por workstream, bloqueante, cuja correção de achado crítico é
verificada por G13. Norma: [cycle-review.md](cycle-review.md).

### Por que os identificadores aposentados não são reaproveitados

Reaproveitar `G11` para outro significado tornaria ilegível todo artefato histórico que o cita: o
leitor não teria como saber qual regime estava em vigor. O custo de queimar dois números é
irrelevante perto do custo de um registro ambíguo.

## 2. Os oito detectores de G13

G13 é mecânica, não julgamento. Sobre a janela `base_commit..HEAD`:

| Detector | Reprova quando |
|---|---|
| `escopo` | arquivo no diff fora do escopo declarado pelas tarefas ou pelo plano |
| `teste-enfraquecido` | asserção removida, teste marcado como ignorado, tolerância afrouxada |
| `comportamento-sem-teste` | fonte com comportamento novo sem teste que o cubra |
| `sinal-silenciado` | erro suprimido, tipo calado, aviso desligado sem a válvula documentada |
| `ledger-append-only` | linha de ledger já gravada foi alterada ou removida |
| `paridade-de-contrato` | contrato mudou sem que consumidor ou schema acompanhasse |
| `evidência` | tarefa fechada citando evidência ausente, incompleta ou de commit anterior |
| `segredos` | padrão de segredo no diff |

**A lista cresce por finding, nunca por antecipação.** Um detector sem regressão vermelho→verde não
entra no validador — detector especulativo produz falso positivo, e falso positivo mata o gate por
desgaste.

## 3. Pré-voo da Revisão de Ciclo

Antes de gastar a invocação de revisor, todos devem passar:

1. **Gate verde** — validador (e G13, quando aplicável) executados com sucesso **agora**.
2. **Diff não vazio** — mudanças reais de código, teste, doc ou config.
3. **Sem artefatos locais** — nenhum build output, temporário, nota pessoal ou binário acidental.
4. **Sem marcadores de trabalho em andamento** — sem conflito de merge, depurador, print de debug ou pendência não justificada.
5. **Gerados co-embarcados** — se o diff toca fonte de geração de código, o gerado veio junto.
6. **Escopo revisável** — preferir ≤ 1500 linhas e ≤ 25 arquivos por invocação; acima disso, fatias que alimentam a **mesma** auditoria.

Marcador falho → **aborte** a RC e reporte qual falhou. Revisão sobre mudança quebrada produz
ruído, não sinal.

## 4. O que invalida uma alegação de conclusão

- Teste não executado descrito como aprovado.
- Teste enfraquecido, marcado como ignorado ou com asserção removida para passar.
- Evidência colada de execução anterior ao último commit.
- "Deve funcionar", "provavelmente passa", "não consegui rodar mas está correto".
- Resumo apresentado no lugar da saída do comando.
- Gate pulado sem registro do motivo.

Qualquer um destes é **falsificação de evidência** — proibido, não erro de forma.

## 5. O que **não** invalida

Simetricamente: **notação não é conclusão**. Seta ASCII no lugar de `→`, travessão simples, linha
em branco depois do heading, item de lista em vez de subtítulo e contador desalinhado são
normalizados na leitura e **não** reprovam rodada nem consomem orçamento.

Reabrir uma revisão por diferença de caractere não aumenta rigor: gasta o revisor que deveria estar
julgando o código.

## 6. Falha parcial

Quando parte do trabalho passa e parte não:

1. Conclua e registre o que passou, com evidência.
2. Declare explicitamente o que **não** foi validado, em `STATE.md` § Não validado e no handoff.
3. **Não** marque a tarefa como concluída — marque `parcial`, com o resto listado.
4. Gate falho vira bloqueio visível em `pending_gates`, não nota de rodapé.

## 7. O gate do próprio protocolo

```bash
python validators/validate.py --root .
```

Saída de erro é acionável: arquivo, linha quando aplicável, regra violada e o que fazer. **Validador
vermelho impede declarar qualquer trabalho concluído.**

Se o vermelho vem de fronteira mal declarada (projeto vizinho, dependência de terceiros), a
correção é **declarar a fronteira** em `validator-scope.yaml` — nunca silenciar a verificação nem
reescrever o vizinho.
