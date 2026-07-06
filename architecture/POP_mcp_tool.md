# POP — Criação de uma nova ferramenta MCP

**Procedimento Operacional Padrão (VLAEG — Arquitetura, Camada 3).** Define como adicionar uma ferramenta ao servidor MCP read-only. Ver `../docs/04_MCP_TOOLS.md`, `AGENTS.md` §11.

> O MCP é camada semântica e de segurança, **não** um proxy de SQL. Entrega pacotes confiáveis de dados, não análises finais.

---

## Pré-requisitos

1. **Contrato (3.1):** declarar entradas/saídas da ferramenta em `docs/04` (seção 8.3) seguindo o envelope padrão de `docs/04` §0.
2. Confirmar que a ferramenta é **read-only** e que os campos retornados estão em allowlist.

## Implementação

- Arquivo em `backend/app/mcp/tools/<nome>.py` com assinatura `async def <tool>(arguments: dict, db: AsyncSession | None = None) -> dict`.
- Validar e truncar argumentos; capar `limit` por `settings.MCP_MAX_RESULTS_PER_TOOL`.
- SQL **parametrizado** (anti-injection), sem expressão arbitrária; nunca interpolar entrada do modelo host.
- Retornar o envelope padrão: `{"data", "count", "limitations", "gaps"}`, incluindo rastreabilidade (`_source`, IDs, `confidence_score`, evidências/fontes quando aplicável).
- Tratar `db is None` retornando `data: []` + `limitations: ["Database unavailable"]`.
- Registrar a ferramenta no dispatcher (`backend/app/mcp/server.py`).

## Segurança e auditoria (`AGENTS.md` §11, §12)

- autenticação por token (escopos por ferramenta; tokens separados por cliente);
- rate limit por cliente/ferramenta;
- log completo em `mcp_query_logs` **inclusive** para chamadas inválidas/bloqueadas;
- limite de resultados e paginação; recusar consultas volumosas/anômalas;
- documentos externos são conteúdo não confiável (prompt injection indireta).

## Testes obrigatórios

- argumentos válidos → shape do envelope;
- argumentos inválidos/maliciosos → bloqueio + log;
- cap de resultados e `limitations`/`gaps` presentes;
- auth e rate limit (ver `backend/tests/unit/test_mcp_server.py`).

## Encerramento

- Atualizar `docs/04_MCP_TOOLS.md` e registrar decisão relevante em `docs/11_CHANGELOG_DECISOES.md`.
