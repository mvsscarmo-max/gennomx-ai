# PLAN-001 - Platform Auth, DRY-7 e reconciliação VLAEG

**Data:** 2026-07-20
**Status:** concluído
**Origem:** especificação raiz, seção 6, e contrato `PLATFORM_AUTH_CONTRACT.md`

## Objetivo

Concluir o consumo local de Platform Auth no backend, entregar o menor incremento útil de resultados
ClinicalTrials.gov por fixtures, reconciliar runtime/documentação e migrar o projeto para VLAEG 2.0.

## Escopo

- principal normalizado e scopes `ai:*` por ação;
- JWT local/chave interna preservados quando a flag está desligada;
- MCP com autenticador próprio;
- outcomes planejados, outcome measures e adverse events CT.gov por fixture;
- idempotência, evidência, literais negativos/inconclusivos e gaps;
- SUPA-4 e estado AI-P1/P2/P4 reconciliados;
- arquivo v1 e estado VLAEG 2.0 vivo;
- testes backend e gates frontend locais.

## Fora de escopo

- deploy, ingestão real, produção, segredos ou provisionamento;
- DRY-6 antes da validação do backbone;
- ANVISA, normalização de indicações, resolução de empresas e PMC;
- provisionamento ou adoção runtime de R2;
- alteração ampla de schema clínico.

## Riscos

- confundir sessão admin com MCP: mitigado por autenticadores e teste separados;
- sobreinterpretar resultado clínico: mitigado por persistência literal e raw;
- duplicação em retry: mitigada por fingerprint e granularidade corrente;
- docs divergirem do código: mitigado por decisão VLAEG e buscas de reconciliação.

## Validação

- unit/integration backend para auth, scopes, MCP, parser, persistência e MCP gaps;
- Ruff, format, mypy, pytest backend e scans locais disponíveis;
- lint, typecheck, build e E2E frontend quando o ambiente permitir;
- nenhum comando de rede externa/ingestão/deploy.

## Critérios de conclusão

- comportamento da flag e scopes provado;
- MCP não aceita sessão admin;
- fixtures DRY-7 persistem sem duplicação e preservam incerteza;
- trial sem resultado retorna gaps;
- documentação e VLAEG refletem o runtime real;
- bloqueios ambientais registrados sem declarar sucesso indevido.

## Resultado

Concluído localmente em 2026-07-20. Platform Auth, separação MCP, DRY-7, reconciliação de runtime,
arquivo v1 e VLAEG 2.0 foram validados. Gates finais: pytest `282 passed, 1 skipped`, 7 E2E e
lint, format, tipos, build, Bandit e auditorias de dependências aprovados. A validação real de
PostgreSQL/MinIO/Celery na VPS permanece fora do plano e bloqueada por ambiente/autorização.
