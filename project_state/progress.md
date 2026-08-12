# PROGRESS - GennomX AI

## 2026-07-20 - Platform Auth, DRY-7 e VLAEG 2.0

- `CurrentUser` passou a expor origem, subject de plataforma, tenant e scopes.
- Platform Auth RS256 foi ligado à API por flag com validação integral de claims e autorização por ação.
- JWT local e chave interna foram preservados; autenticação MCP permaneceu separada.
- DRY-7 foi implementado com duas fixtures CT.gov, projeções idempotentes, evidência e gaps MCP.
- SUPA-4 e AI-P1/P2/P4 foram reconciliados com o código real.
- Documentação viva passou a declarar PostgreSQL VPS + JWT local/Platform Auth + MinIO; R2 futuro.
- Estado v1 foi preservado em `archive/v1/`; VLAEG 2.0 criado.
- Gates focados iniciais: 31 testes aprovados; Ruff focado e mypy (`app workers`) aprovados.
- O bootstrap de testes passou a fixar MinIO antes da coleta, sem depender de valor legado do ambiente local.
- A cobertura do warehouse foi alinhada ao contrato administrativo (`ai:admin`).
- O lock Python foi regenerado sem Supabase/PyPDF2 e com MCP corrigido; auditoria Python sem vulnerabilidades conhecidas.
- O lock npm recebeu correções transitivas; auditoria npm sem vulnerabilidades conhecidas.
- Gates finais: pytest `282 passed, 1 skipped`; Ruff lint/format, mypy, Bandit, pip-audit,
  ESLint, TypeScript, base-path, build Next.js, npm audit e 7 E2E Playwright aprovados.
- PLAN-001 concluído localmente. Validação do backbone na VPS permanece bloqueada por ambiente/autorização.
