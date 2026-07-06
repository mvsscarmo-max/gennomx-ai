# ADR-001 — Temporalidade, precedência e estado canônico

**Status:** Aprovada  
**Data:** 2026-06-20  
**Escopo:** ingestão, pré-persistência, banco canônico, auditoria e MCP

## Contexto

Upserts simples não distinguem quando um fato era válido no mundo (`valid time`) de quando o
sistema o conheceu (`system time`). Também não preservam, por campo, fontes concorrentes,
substituições e correções humanas.

## Decisão

1. Tabelas de domínio representam o **estado canônico corrente** e permanecem pequenas.
2. `field_assertions` preserva afirmações por entidade, campo, valor, fonte e intervalo bitemporal.
3. Apenas uma assertion pode ser corrente por entidade/campo/granularidade; versões anteriores são
   encerradas, nunca sobrescritas.
4. `data_conflicts` registra divergências não resolvidas. Conflito não é resolvido por recência
   isolada nem por LLM.
5. `manual_corrections` é append-only e exige motivo; aprovação gera nova assertion e referência
   explícita à anterior.
6. A precedência é determinística: validade temporal, autoridade da fonte, completude/evidência e
   regras específicas do domínio.
7. Payload atrasado pode ser preservado no raw/assertion histórica, mas não pode regredir o
   canônico.
8. Dados clínicos e regulatórios críticos não são fisicamente apagados como rotina operacional.

## Ações do motor de decisão

`insert`, `replace`, `enrich`, `noop`, `reject`, `supersede`, `archive`, `conflict` e `quarantine`.
Toda decisão contém códigos de razão reproduzíveis e versão do conjunto de regras.

## Consequências

- Consultas normais continuam lendo tabelas canônicas ou views `is_current`.
- Auditoria e replay ficam possíveis sem carregar o caminho quente com payloads brutos.
- A ingestão custa mais escrita e exige particionamento/arquivamento das assertions.
- LLMs podem sugerir candidatos, mas não executam a decisão de persistência.

## Critério de sucesso

Reprocessar, receber versões fora de ordem, corrigir manualmente ou detectar fontes divergentes não
deve apagar evidência nem produzir regressão silenciosa no estado canônico.
