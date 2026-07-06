# 05 — Segurança, Autenticação, Governança e Compliance

## Controles operacionais implementados — 2026-06-21

- correção humana exige admin, motivo e `EvidenceSnippet`; aprovação encerra a assertion anterior
  e cria assertion curada/confirmada; rejeição preserva tudo;
- não existe UPDATE factual destrutivo pela API nem escrita de modelo host;
- legal holds bloqueiam seleção para arquivo e exclusão;
- RLS concede curadoria ao `gennomx_app` protegido por autorização administrativa e mantém escrita
  de ingestão/retenção no worker;
- scraper policy é fail-closed e o kill switch pode ser acionado no dashboard.

## Endurecimento de identidade e RLS — revisão de 2026-06-21

- produção exige `gennomx_app` em `DATABASE_URL`, `gennomx_worker` em
  `WORKER_DATABASE_URL` e `gennomx_migrator` em `DATABASE_URL_SYNC`;
- API e worker consultam `pg_roles` no runtime e recusam role inesperado, `rolsuper=true` ou
  `rolbypassrls=true`; o nome correto na URL, isoladamente, não basta;
- policies limitam leitura a `gennomx_app`/`gennomx_worker`/`gennomx_readonly`, escrita de domínio
  a `gennomx_worker` e INSERT de auditoria a `gennomx_app`; `postgres` e `service_role` foram
  removidos inclusive das policies legadas reaplicadas pela migração `0003`;
- a chave interna usa comparação constante e representa `service`, sem herdar privilégios admin;
- autenticação MCP duplicada e não utilizada foi removida;
- SSR usa o JWT Supabase do usuário, sem cache compartilhado e sem chave administrativa em
  produção; `API_INTERNAL_KEY` no frontend só é aceito no bypass E2E não produtivo.

## Política de edição, exclusão e correção factual — 2026-06-20

- Dado derivado de fonte externa não recebe edição destrutiva direta.
- Correção humana cria `manual_corrections` com autor, motivo, valor proposto e evidência.
- Aprovação gera nova `field_assertion`; a anterior torna-se `superseded` e permanece auditável.
- Exclusão lógica (`lifecycle_status`, `is_current`, tempos de encerramento) é o padrão.
- Exclusão física limita-se a obrigação legal/licença, malware, dado pessoal indevido, duplicata
  byte a byte sem referência exclusiva ou expiração formal de logs.
- Exclusão física exige job administrativo com dry-run, aprovação, contagem e audit log.
- Resultados clínicos, decisões regulatórias e evidências críticas não são resumidos como
  substituição do original nem apagados por housekeeping.

LLMs não aprovam correções, exclusões, merges ou fonte vencedora. A seleção de modelos permanece
adiada; candidatos futuros estarão sujeitos às mesmas regras determinísticas e de auditoria.

## RLS e menor privilégio — correção fase 4 (2026-06-20)

Todas as tabelas do domínio e auditoria passam a ter RLS habilitada pela migração `0002`.
Políticas bloqueiam acesso direto por padrão e reconhecem os papéis `gennomx_app`,
`gennomx_worker` e `gennomx_readonly`, além dos papéis administrativos controlados. O app lê o
domínio e insere logs; o worker pode mutar dados; readonly apenas consulta.

Os papéis locais agora são `NOLOGIN`: o repositório não cria usuários nem contém senhas fixas.
Credenciais de serviço são provisionadas externamente e recebem membership no grupo correto.
Redis exige senha; serviços administrativos ficam em loopback. Produção rejeita banco/Redis em
localhost, exige TLS em PostgreSQL/Redis e rejeita o backend S3 ainda não suportado.
`API_ALLOWED_HOSTS` configura explicitamente o `TrustedHostMiddleware` em produção; wildcard global
e localhost são recusados. O compose produtivo (`infra/docker-compose.prod.yml`) mantém Redis em
TLS (`rediss://`) com certificados fora do Git em `secrets/redis/`.

Este documento consolida os princípios, ameaças, controles e políticas de segurança da GennomX AI.

---

# 12. Segurança, autenticação e governança

## 12.1 Princípios de segurança

A segurança deve ser aplicada por design, não adicionada apenas ao final.

Princípios:

- menor privilégio;
- defesa em profundidade;
- zero trust entre componentes;
- separação de ambientes;
- validação de toda entrada;
- logs auditáveis;
- segredos protegidos;
- criptografia em trânsito e repouso;
- rate limiting;
- fail-safe defaults;
- bloqueio por padrão;
- exposição mínima de dados;
- segurança específica para MCP e IA.

## 12.2 Threat model inicial

A GennomX AI deve considerar ameaças como:

- vazamento de dados por API;
- vazamento de dados por MCP;
- extração massiva da base;
- abuso de tokens MCP;
- prompt injection indireta em documentos;
- SSRF em scrapers;
- upload de arquivos maliciosos;
- execução indevida de scripts em parsing;
- SQL injection;
- broken object level authorization;
- falhas de autenticação;
- exposição de segredos;
- dependências vulneráveis;
- manipulação de dados ingeridos;
- poisoning de evidências;
- falhas de backup;
- alterações não auditadas;
- DoS por consultas amplas;
- aumento de custo por abuso de IA interna.

## 12.3 Autenticação

MVP:

- Supabase Auth ou autenticação equivalente;
- login por e-mail/senha ou magic link;
- MFA opcional, recomendado para admin;
- sessão curta para áreas administrativas;
- tokens MCP separados da sessão web;
- API keys internas distintas por serviço.

Futuro:

- MFA obrigatório;
- SSO/OIDC/SAML;
- SCIM para provisionamento enterprise;
- políticas por organização;
- expiração e rotação obrigatória.

## 12.4 Autorização

MVP:

- papel admin;
- papel read-only interno;
- papel service para jobs;
- papel MCP read-only;
- papel API internal.

Futuro:

- RBAC granular;
- ABAC por fonte/licença;
- permissões por ferramenta MCP;
- permissões por tipo de dado;
- permissões por organização;
- isolamento por tenant.

## 12.5 Supabase/PostgreSQL e Row Level Security

Mesmo sem multiusuário completo no MVP, recomenda-se desenhar tabelas com preparo para RLS.

### Integração operacional com Supabase

O PostgreSQL da Supabase é o banco primário do MVP. A aplicação não deve usar a role `postgres`,
`anon`, `authenticated` ou `service_role` como usuário de conexão do backend. O bootstrap
operacional está em `infra/supabase/bootstrap_roles.sql` e cria quatro roles dedicadas:

| Role | Uso | Permissão esperada |
|---|---|---|
| `gennomx_migrator` | Alembic/migrações | criar schema, extensões permitidas e objetos versionados |
| `gennomx_worker` | Celery/ingestão | leitura e escrita nas tabelas operacionais |
| `gennomx_app` | FastAPI/dashboard/MCP HTTP | leitura ampla e inserts operacionais restritos, como logs MCP, eventos de segurança e correções manuais |
| `gennomx_readonly` | inspeção controlada | leitura sem escrita |

Variáveis obrigatórias para Supabase hospedado:

- `DATABASE_URL`: role `gennomx_app`, de preferência pelo pooler Supabase.
- `WORKER_DATABASE_URL`: role `gennomx_worker`, de preferência pelo pooler Supabase.
- `DATABASE_URL_SYNC`: role `gennomx_migrator`, de preferência por conexão direta para migrações.
- `SUPABASE_URL`, `SUPABASE_PROJECT_REF`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` e
  `SUPABASE_JWKS_URL`, mantidos apenas em variáveis protegidas. `SUPABASE_JWT_SECRET` permanece
  somente como fallback legado HS256 durante transição.

As URLs devem exigir TLS (`sslmode=require` ou `ssl=require`). O runtime normaliza URLs Supabase
com `sslmode=require` para o driver asyncpg, enquanto Alembic usa URL síncrona compatível com
psycopg2.

Fluxo de ativação:

1. Executar `infra/supabase/bootstrap_roles.sql` no Supabase SQL Editor com senhas reais fora do
   repositório.
2. Configurar `.env` a partir de `.env.example`.
3. Rodar `alembic upgrade head` no diretório `backend`.
4. Reexecutar o bloco final de grants do bootstrap após migrações que criem novas tabelas, se as
   permissões default não tiverem sido aplicadas pelo owner esperado.
5. Validar `/ready`; em produção o startup também verifica se a role ativa é `gennomx_app` e não
   possui `BYPASSRLS`.

Regras:

- não expor tabelas sensíveis diretamente;
- preferir views controladas;
- separar service role de usuário final;
- evitar uso de service key no frontend;
- habilitar RLS em tabelas expostas;
- testar políticas de RLS;
- criar testes específicos de autorização negativa.

## 12.6 Segurança de API

Requisitos:

- autenticação obrigatória;
- autorização por endpoint;
- validação de payload;
- paginação obrigatória;
- rate limit;
- CORS restritivo;
- headers de segurança;
- logs estruturados;
- respostas sem stack trace;
- sanitização de erro;
- versionamento;
- OpenAPI atualizado;
- testes contra OWASP API Security Top 10.

## 12.7 Segurança de frontend

Requisitos:

- proteção contra XSS;
- sanitização de conteúdo HTML externo;
- Content Security Policy;
- proteção contra clickjacking;
- cookies seguros quando aplicável;
- não armazenar tokens sensíveis em localStorage quando evitável;
- tratamento seguro de markdown e snippets;
- não renderizar HTML bruto de fontes externas;
- validação client-side complementar, nunca substitutiva da validação server-side.

## 12.8 Segurança de jobs e conectores

Requisitos:

- permissões mínimas;
- rede restrita;
- allowlist de domínios;
- logs por job;
- timeout obrigatório;
- limite de download;
- validação de certificado TLS;
- retries controlados;
- detecção de anomalias;
- não executar conteúdo baixado;
- parsing em sandbox para arquivos arriscados.

## 12.9 Gestão de segredos

Requisitos:

- nenhum segredo no código;
- nenhum segredo em logs;
- variáveis protegidas por ambiente;
- secret manager quando disponível;
- rotação programada;
- chaves diferentes por ambiente;
- revogação imediata;
- scanning automático de segredos em commits.

## 12.10 Backups e recuperação

Requisitos:

- backup automático do banco;
- backup do object storage crítico;
- teste periódico de restauração;
- documentação de RPO/RTO;
- retenção definida;
- isolamento de backups;
- monitoramento de falha de backup.

## 12.11 Auditoria

Registrar:

- logins;
- falhas de login;
- alterações de dados;
- execuções de jobs;
- alterações de conectores;
- criação/rotação de tokens;
- chamadas MCP;
- chamadas API sensíveis;
- falhas de segurança;
- exportações;
- downloads.

---

# 13. Segurança específica para MCP, IA e dados biomédicos

## 13.1 MCP como superfície crítica

O MCP será acessado por modelos host e agentes. Isso exige controles mais fortes do que uma API interna comum.

Riscos principais:

- agente automatizado fazendo consultas excessivas;
- modelo host pedindo volume maior do que o necessário;
- tentativa de inferir estrutura interna do banco;
- exfiltração incremental;
- uso de ferramenta com parâmetros amplos;
- prompt injection originada em documento externo;
- confusão entre evidência e instrução;
- retorno de dados sem licença futura.

## 13.2 Regras de exposição MCP

- ferramentas read-only no MVP;
- nenhuma ferramenta genérica de SQL;
- nenhuma ferramenta de administração;
- nenhuma ferramenta de escrita;
- limites de resultados por chamada;
- limite de chamadas por minuto;
- limite de profundidade de evidência;
- limitação por escopo de token;
- respostas estruturadas;
- campos sensíveis omitidos;
- logs completos.

### Estado implementado em 2026-06-12

O endpoint MCP registra chamadas em `mcp_query_logs` com ferramenta, cliente, hash de input, argumentos normalizados, contagem de resultados, latência, status, entidades acessadas e erro quando houver. A auditoria inclui chamadas aceitas, bloqueadas e inválidas. Os tokens são separados por cliente, possuem escopos explícitos e usam rate limit distribuído em Redis fora do desenvolvimento.

Pendências de segurança:

- revisão periódica dos escopos por token e ferramenta;
- persistência de entidades/fonte acessadas por chamada;
- rotação/expiração formal de tokens MCP;
- gateway TLS para transporte MCP remoto quando habilitado.

## 13.3 Segurança dos bundles

Bundles para relatórios externos devem:

- ter escopo explícito;
- evitar dump massivo;
- incluir apenas dados necessários;
- incluir evidências essenciais;
- indicar lacunas;
- bloquear fontes não permitidas;
- limitar número de snippets;
- preservar copyrights;
- registrar chamada e cliente.

## 13.4 Proteção contra dados contaminados

Dados externos podem conter:

- erros factuais;
- informações desatualizadas;
- duplicações;
- HTML malicioso;
- prompts embutidos;
- metadados manipulados;
- arquivos corrompidos.

Controles:

- armazenar fonte original;
- validar schema;
- sanitizar HTML;
- limitar tamanho;
- verificar hashes;
- comparar com outras fontes;
- usar confidence score;
- preservar conflitos.

---

# 16. Compliance e aspectos legais

## 16.1 Princípios

- usar fontes oficiais sempre que disponíveis;
- priorizar API/export oficial sobre scraping;
- respeitar termos de uso;
- respeitar robots.txt;
- registrar licença/status de cada fonte;
- bloquear fontes não aprovadas;
- preservar atribuição;
- evitar reprodução integral de conteúdo protegido sem permissão;
- manter rastreabilidade;
- permitir remoção de fonte quando necessário.

## 16.2 Scraping

Scraping deve seguir:

- análise prévia de termos;
- allowlist de domínios;
- rate limits;
- identificação de user agent quando apropriado;
- não contornar bloqueios técnicos;
- não burlar paywalls;
- armazenamento mínimo necessário;
- registro de logs.

## 16.3 Documentos e direitos autorais

Para documentos científicos, congressos e materiais corporativos:

- armazenar metadados e trechos necessários;
- evitar armazenamento integral se licença não permitir;
- registrar URL original;
- registrar data de acesso;
- permitir exclusão;
- controlar exibição de trechos;
- diferenciar conteúdo público, licenciado e interno.

## 16.4 Dados regulatórios e científicos

Mesmo usando dados públicos, a plataforma deve deixar claro:

- dados podem estar desatualizados;
- fontes podem divergir;
- dados não substituem parecer regulatório, médico, jurídico ou financeiro;
- modelos host devem citar evidências;
- decisões de investimento/P&D exigem revisão humana.

## 16.5 Fontes licenciadas futuras

Embora não haja previsão de bases pagas agora, a arquitetura deve permitir:

- marcar fonte como licenciada;
- limitar acesso por organização;
- bloquear export;
- bloquear uso em MCP externo;
- registrar uso por usuário;
- auditar consumo.

---

## 9. Riscos e pontos de atenção

### 9.1 Licenciamento de dados

Algumas fontes abertas permitem uso amplo, outras têm restrições. Bases comerciais exigem contrato. A arquitetura deve permitir bloquear dados por fonte e por licença.

### 9.2 Scraping e termos de uso

Scraping deve ser usado somente quando não houver API/export oficial. É necessário respeitar robots.txt, termos de uso, limites de acesso, cache responsável e atribuição.

### 9.3 Qualidade dos dados

Dados clínicos e regulatórios podem ser incompletos, divergentes ou desatualizados. O banco deve registrar conflitos em vez de sobrescrevê-los sem critério.

### 9.4 Dados conflitantes entre fontes

Um ensaio pode ter status diferente no ClinicalTrials.gov, press release e publicação. A GennomX AI deve preservar múltiplas versões e indicar a fonte mais recente ou mais autoritativa.

### 9.5 Hallucination de LLMs

Modelos host podem extrapolar ou interpretar mal. As ferramentas MCP devem reduzir esse risco retornando dados estruturados, citações e limites explícitos.

### 9.6 Rastreabilidade insuficiente

Sem `SourceDocument` e `EvidenceSnippet`, o sistema vira uma base não auditável. Rastreabilidade deve ser requisito de arquitetura, não funcionalidade opcional.

### 9.7 Custos de manutenção dos conectores

APIs mudam, sites alteram HTML, congressos reorganizam plataformas. É necessário monitoramento ativo e alertas.

### 9.8 Mudanças em APIs externas

ClinicalTrials.gov, openFDA, DailyMed, EMA, Open Targets e ANVISA podem alterar schemas, limites ou formatos. Os conectores devem ser versionados e testados.

### 9.9 Segurança do MCP

MCP expõe ferramentas a modelos externos. Deve haver autenticação, autorização, rate limit, logs, allowlist de ferramentas e bloqueio de queries perigosas.

---


## 12A. Segurança específica da stack refinada

### Next.js

- não armazenar segredos no frontend;
- não expor service role key do Supabase;
- usar apenas chaves públicas apropriadas ao cliente;
- operações sensíveis devem passar pela FastAPI;
- proteger rotas administrativas.

Estado em 2026-06-12:

- frontend atualizado para `next@15.5.18`, removendo vulnerabilidades high reportadas no `npm audit`;
- lockfile versionável criado para permitir `npm ci` no CI;
- permanecem 2 vulnerabilidades moderadas ligadas ao `postcss` transitivo embutido em Next; não foi aplicado `npm audit fix --force` porque a sugestão envolve caminho major/quebrável.

Estado em 2026-06-20:

- `npm audit` não reporta vulnerabilidades moderadas ou superiores; PostCSS usa override
  compatível e Playwright foi elevado à versão corrigida;
- `python-jose` foi removido e a validação JWT usa `PyJWT[crypto]`;
- pisos de FastAPI/Starlette, python-multipart, aiohttp, LiteLLM e python-dotenv foram
  elevados às versões com correções conhecidas; LiteLLM, ainda sem release corrigida
  disponível no índice, foi retirado do runtime principal e colocado no extra opcional `llm`
  com piso seguro `>=1.84.0`;
- endpoints `/api/v1/audit/*` exigem administrador e não retornam argumentos, IDs de ator,
  hashes de IP nem metadados brutos.

### FastAPI

- validar todos os payloads;
- aplicar autenticação e autorização;
- impor paginação e limites de resposta;
- não executar processamento pesado em rotas síncronas;
- registrar logs de endpoints administrativos, dashboard e MCP.

### Celery/Redis

- proteger broker e backend de resultados em rede privada ou credenciais fortes;
- não colocar segredos nos payloads das filas;
- limitar tamanho de mensagens;
- usar timeouts, retries e dead-letter/fila de falhas quando aplicável;
- registrar falhas e eventos anômalos como `SecurityEvent` quando houver indício de abuso.

### DuckDB nos workers

- processar arquivos em ambiente controlado;
- limitar memória e tamanho de arquivos;
- validar origem e hash antes do processamento;
- não tratar dados processados localmente como canônicos antes da persistência validada.

### OPENCODE / LLM interno

- chave `OPENCODE_API_KEY` deve ficar em `.env`/secret manager, nunca no frontend;
- `LLM_ENABLE_NETWORK_CALLS` controla ativação; em produção, falha fechada se key/base URL/modelo estiverem ausentes;
- logs de chamadas (`llm_call_logs`) registram hashes de prompt/input/response, schema validity, latency, tokens e status; nunca armazenam prompt completo, headers de autorização ou chaves;
- toda saída de LLM deve ser validada por schema Pydantic antes de qualquer persistência;
- documentos externos passados ao LLM são tratados como conteúdo não confiável;
- prompts do sistema instruem o modelo a extrair/classificar, não a executar instruções do texto-fonte;
- o LLM interno não decide fonte vencedora, merge, correção ou exclusão;
- provedor configurável via `LLM_PROVIDER` (MVP: `opencode`); adaptador permite troca futura.
# Correção fase 1 — identidade e configuração (2026-06-20)

- Segredos administrativos deixaram de possuir valores padrão utilizáveis.
- `ENVIRONMENT=production` falha no startup se banco, JWT, chave interna, token MCP ou CORS estiverem ausentes/inseguros.
- JWT Supabase valida assinatura via JWKS (`ES256`/`RS256`), `aud` e `iss`; o papel GennomX vem exclusivamente de `app_metadata.gennomx_role`. `SUPABASE_JWT_SECRET` fica apenas como fallback legado enquanto a chave HS256 não for desativada no Supabase.
- O dashboard usa sessão Supabase no navegador e chave interna apenas em renderização server-side; a chave não usa prefixo `NEXT_PUBLIC_`.
- Middleware protege as rotas do dashboard e renova cookies de sessão.
- `/health` é liveness; `/ready` verifica banco e retorna 503 quando indisponível.

# Correção fase 2 — revisão técnica sênior (2026-06-23)

- `.env.example` não contém mais chaves reais (`OPENCODE_API_KEY`, `NCBI_API_KEY` substituídas por
  placeholders); os valores reais ficam apenas em `.env` (ignorado pelo Git). Rotação dispensada por
  decisão do time, pois as chaves foram inseridas minutos antes e o repositório nunca teve commit.
- `validate_secure_production_settings` (`app/config.py`) passa a exigir `SUPABASE_JWKS_URL` ou
  `SUPABASE_URL` configurado quando `ENVIRONMENT=production`, impedindo subida silenciosa apenas
  com o fallback HS256 (`SUPABASE_JWT_SECRET`), mais frágil para rotação de chave.
- MCP: rate limit por IP agora roda **antes** da autenticação (`_check_pre_auth_rate_limit`), e
  requisições `401` (sem token/token inválido) não geram mais escrita em `mcp_query_logs` nem
  `commit` — eliminando o vetor de DoS por flood não autenticado. Ver `docs/04_MCP_TOOLS.md` §8.9.
- MCP tools (`search_drugs`, `find_trials`, etc.) sanitizam exceções de banco: o texto bruto vai
  para `structlog`, e o cliente host recebe apenas `"Query failed"`.
- Buckets em memória do rate limiter MCP (`_rate_buckets`, `_ip_rate_buckets`) removem entradas
  vazias imediatamente e passam por varredura periódica (5 min) para IPs efêmeros, limitando o
  crescimento de memória em desenvolvimento/processo único.
- Removida a variável morta `SECRET_KEY` de `tests/conftest.py` e `.github/workflows/ci.yml`
  (nunca era lida por `Settings`, que usa `API_SECRET_KEY`).
- `/ready` deixa de expor o detalhamento por componente (`checks: {database, redis}`) quando
  `ENVIRONMENT=production`, retornando apenas `{"status": "ready"|"not_ready"}` — evita divulgar
  topologia de infraestrutura a chamadas externas não autenticadas.
- `frontend/src/middleware.ts` passa a ler `app_metadata.gennomx_role` do usuário Supabase e
  redireciona não-admins que tentem acessar `/governance` ou `/security` para `/`, espelhando o
  `require_admin` do backend. Não é correção de uma falha de segurança (a API já retornava 403),
  apenas alinhamento de UX com a autorização real.

# Correção fase 3 — revisão técnica sênior (2026-07-02)

- **Segregação de funções em correções manuais (quatro olhos):** `CorrectionService.review`
  passa a recusar (`AuthorizationError`, HTTP 403) quando `reviewer == requested_by` — o mesmo
  admin não pode mais propor e aprovar a própria correção factual. Arquivo:
  `backend/app/services/correction_service.py`.
- **Handler global de exceções de domínio:** até esta correção, `NotFoundError`/
  `AuthorizationError`/`ValidationError` levantados pelos serviços não tinham handler
  registrado em `app/main.py` e viravam **500 Internal Server Error** genérico em qualquer rota
  (não só correções) — mascarando erros que deveriam ser 404/403/422. Registrado
  `@app.exception_handler(GennomXError)` que traduz `code` → status HTTP e retorna
  `{"success": false, "error": {"code", "message"}}`.
- **SSRF por DNS-rebinding no scraper controlado (feature ainda inativa em produção):**
  `validate_scrape_url` validava o IP público resolvido, mas o cliente HTTP re-resolvia o
  hostname ao conectar — uma resposta DNS de TTL curto entre a validação e a conexão podia
  apontar para um IP interno (TOCTOU). `ControlledScraper.fetch` agora conecta diretamente ao
  IP já validado, com header `Host` e SNI (`extensions={"sni_hostname": ...}`) fixados no
  hostname original, preservando validação de certificado TLS correta. Arquivo:
  `backend/workers/base/scraping_policy.py`.
- **Remoção de código morto de autorização:** `CurrentUser.can_write` e o papel HTTP `worker`
  nunca eram atribuídos por nenhum usuário Supabase real nem checados por nenhuma rota (toda
  escrita já usava `require_admin`). Removidos de `backend/app/auth/dependencies.py` para não
  sugerir um nível de autorização que não existe de fato.
- **XXE em parsing de XML de fontes externas (débito técnico pré-existente, corrigido nesta
  rodada):** `workers/connectors/pubmed/connector.py` usava `xml.etree.ElementTree.fromstring`
  na resposta do EFetch (bandit B314); trocado por `defusedxml.ElementTree.fromstring`,
  consistente com a diretriz de tratar documentos externos como conteúdo não confiável
  (`AGENTS.md` §12). Achado colateral: `query_key is None` não era checado antes de paginar a
  busca — corrigido junto.
