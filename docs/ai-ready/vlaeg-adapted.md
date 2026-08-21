<!-- validate-links: illustrative-paths -->

# Método VLAEG adaptado

V-L-A-E-G é a identidade do protocolo — e deixou de ser um funil obrigatório. Aqui ele funciona
como **lente**: dimensão de análise, classificação de tarefa, estágio de maturidade e organizador
de entregáveis.

As fases não competem com as skills. **Skill é *como se faz*; fase é *sobre o que se está
falando*.**

## 1. As cinco lentes

| Fase | Pergunta | Entregáveis típicos |
|---|---|---|
| **V — Visão** | Que problema, para quem, com que critério de sucesso? | requisitos, escopo, fora de escopo, métricas, contrato de dados |
| **L — Link** | As conexões existem e respondem? | handshake testado, exemplo de configuração, limites de taxa registrados |
| **A — Arquitetura** | Quais módulos, responsabilidades, dados e fluxos? | módulos, modelo de dados, decisões |
| **E — Estilo** | O usuário entende, decide e age? | UX, acessibilidade, mensagens de erro, apresentação |
| **G — Gatilho** | Opera de forma confiável e observável? | automação, deploy, logs, monitoramento, rollback |

## 2. Aplicabilidade

Toda tarefa declara, no `STATE.md`, o estado de cada fase:

| Estado | Significa |
|---|---|
| `aplicável` | a fase tem entregável nesta tarefa |
| `parcial` | só parte da fase é relevante |
| `não aplicável` | a fase não toca esta tarefa — e isso é **registrado**, não presumido |
| `obrigatória por risco` | o nível de risco força a fase, mesmo que pareça dispensável |

Fases obrigatórias por nível:

```text
nível 0-1  → nenhuma fase obrigatória
nível 2    → A
nível 3    → V, A
nível 4    → V, L, A, G
nível 5    → V, L, A, E, G
```

Declarar `não aplicável` é resposta legítima e esperada. **Percorrer as cinco fases numa correção
de typo é o anti-pattern que esta adaptação existe para eliminar.**

## 3. Princípios do VLAEG preservados

Seguem normativos porque nenhuma prioridade superior os contradiz:

- **Dados primeiro** — entrada, origem, fonte da verdade, campos obrigatórios, validações e payload de saída **antes** de construir.
- **Lógica determinística** — IA sugere, classifica e auxilia; código determinístico valida, calcula, registra e executa. Cálculo financeiro, autorização, integração oficial e atualização de registro produtivo **nunca** dependem de inferência.
- **Fonte única da verdade** — o projeto declara sua fonte primária e a precedência entre fontes concorrentes.
- **Autocorreção estruturada** — analisar → isolar → corrigir → testar → documentar → prevenir recorrência.
- **Segurança desde o início** — não é fase final; entra na Visão.

O segundo princípio é o mais valioso do VLAEG para trabalho assistido por IA, e o mais fácil de
erodir: a tentação de deixar o modelo "só calcular esta parte" reaparece a cada tarefa.

## 4. O que mudou em relação ao VLAEG 2.0

| Antes | Agora | Por quê |
|---|---|---|
| Fases percorridas em toda iniciativa | Fases por aplicabilidade e risco | contexto e tempo são caros; ritual uniforme não é gate |
| Checklists longos residentes no protocolo | Convertidos em skills e referências sob demanda | contexto residente dilui regra |
| Inicialização obrigatória com 12 arquivos | Quatro arquivos mínimos, crescimento por necessidade | adoção gradual sem perder garantias |
| Estado documentado > código | **Código > estado documentado** | o código é o que o sistema é |
| Fase Link como etapa cronológica | Fase Link como lente, obrigatória a partir do nível 4 | nem toda mudança toca integração |
| "Somente planos aprovados geram tarefas", como regra universal | Rito proporcional ao risco | burocracia desproporcional nos níveis 0 e 1 |

## 5. Diretriz

Planeje pela Visão, valide pelo Link, construa pela Arquitetura, refine pelo Estilo, automatize
pelo Gatilho — **na medida do risco** — e mantenha o estado do projeto legível o bastante para que
qualquer agente continue de onde o anterior parou, com evidência do que já foi provado.
