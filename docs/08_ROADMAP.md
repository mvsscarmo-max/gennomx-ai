<!-- validate-links: illustrative-paths -->
# 08 — Roadmap, Backlog e Critérios de Sucesso

> Estado vigente em 2026-07-20: PostgreSQL/pgvector na VPS, JWT local + Platform Auth por flag e
> MinIO/S3-compatible substituem o runtime Supabase. As seções antigas abaixo preservam a evolução
> histórica. DRY-7 avançou somente por fixtures; ANVISA, indicação, empresas e PMC seguem bloqueados
> até validação real do backbone.

Este documento reúne as fases de implementação, backlog técnico inicial, decisões em aberto, suposições e critérios de sucesso do MVP.

---

# 18. Roadmap de implementação

## Fase 0 — Definição estratégica e requisitos

Objetivos:

- consolidar escopo;
- definir stack;
- mapear fontes;
- definir modelo de dados inicial;
- definir padrões de segurança;
- definir estratégia de testes;
- definir critérios de MVP.

Entregáveis:

- documentação de requisitos;
- modelo conceitual;
- threat model inicial;
- backlog técnico;
- matriz de fontes;
- plano de testes;
- definição de ambientes.

Critérios de sucesso:

- escopo aprovado;
- fontes priorizadas;
- arquitetura aprovada;
- riscos mapeados.

## Fase 1 — MVP de dados estruturados

Objetivos:

- criar banco inicial;
- implementar ingestão das fontes prioritárias;
- criar entidades principais;
- preservar evidências;
- criar logs de jobs;
- criar testes de conectores;
- **implementar a camada de inteligência emergente: scoring de `evidence_maturity`, `novelty_score`, `clinical_impact_score` e `validation_status`** (complementando `confidence_score`), conforme `docs/00` §14, `docs/02` e `docs/03` §7A–7D.

Fontes:

- ClinicalTrials.gov;
- PubMed/PMC;
- openFDA;
- DailyMed;
- EMA;
- Open Targets;
- ANVISA inicial.

> Ordem de implementação dos próximos conectores: planilha `project_state/fontes_priorizacao.xlsx` (coluna `Prioridade`, definida manualmente).

Entregáveis:

- banco PostgreSQL/pgvector;
- conectores iniciais;
- raw storage;
- parsers;
- testes unitários;
- testes de contrato;
- data quality checks;
- painel básico de ingestão.

Critérios de sucesso:

- dados carregados;
- evidências preservadas;
- ingestão reexecutável;
- testes críticos passando;
- logs operacionais.

## Fase 2 — Dashboard inicial

Objetivos:

- criar interface operacional;
- permitir busca global;
- criar páginas de ativo, empresa e trial;
- exibir evidências;
- permitir edição corretiva;
- exibir qualidade dos dados.

Entregáveis:

- dashboard web;
- login;
- busca global;
- páginas principais;
- tela de logs;
- tela de qualidade;
- testes e2e essenciais.

Critérios de sucesso:

- usuário interno consegue pesquisar e auditar ativos;
- dados incorretos podem ser corrigidos;
- alterações ficam versionadas;
- testes e2e essenciais passam.

## Fase 3 — MCP funcional

Objetivos:

- criar servidor MCP;
- expor ferramentas iniciais;
- autenticar clientes internos;
- registrar logs;
- retornar evidências;
- limitar respostas.

Ferramentas iniciais:

- search_drugs;
- find_trials;
- get_trial_results;
- get_company_pipeline;
- get_regulatory_status;
- fetch_source_evidence;
- build_report_data_bundle.

Entregáveis:

- servidor MCP interno;
- tokens por cliente;
- logs MCP;
- testes MCP;
- documentação de ferramentas;
- sandbox MCP. Sandbox de agente, ai-jail e YOLO estão excluídos por D-044; a menção neste parágrafo é isolamento de produto, histórico ou finding, não adoção.

Critérios de sucesso:

- ChatGPT/Claude/agente privado consegue consultar dados;
- ferramentas retornam schema estável;
- evidências são retornadas;
- logs registram chamadas;
- testes de segurança passam.

## Fase 4 — Bundles para relatórios por IA host

Objetivos:

- estruturar pacotes de dados para modelos host;
- criar templates de bundle;
- validar completude e evidência;
- permitir export ou chamada MCP.

Entregáveis:

- bundle de asset profile;
- bundle de company pipeline;
- bundle de competitive landscape;
- bundle de regulatory history;
- bundle de safety overview;
- validações automáticas.

Critérios de sucesso:

- modelos host conseguem gerar relatórios usando apenas dados MCP;
- bundles incluem evidências e lacunas;
- dados são rastreáveis.

## Fase 5 — Congressos, scraping avançado e PDFs

Objetivos:

- integrar abstracts de grandes congressos;
- extrair documentos PDF;
- estruturar resultados de apresentações;
- reforçar compliance.

Entregáveis:

- conectores de congresso em ondas (ver `docs/03` §7B): **primeira onda ASCO/ESMO/ASH**, depois AACR e demais por área terapêutica; congressos de ciência básica de baixa acionabilidade clínica (AAI/CIS/FOCIS) ficam fora;
- trilha de **preprints (bioRxiv/medRxiv)** sinalizada como preliminar e opt-out por padrão (ver `docs/03` §7C);
- parsers PDF;
- extração de tabelas;
- extração de endpoints;
- sandbox de arquivos;
- testes de regressão com fixtures. Sandbox de agente, ai-jail e YOLO estão excluídos por D-044; a menção neste parágrafo é isolamento de produto, histórico ou finding, não adoção.

Critérios de sucesso:

- abstracts relevantes ingeridos;
- resultados extraídos com evidência;
- falhas de parser detectadas automaticamente;
- scraping dentro das salvaguardas legais.

## Fase 6 — Curadoria humana e workflows

Objetivos:

- melhorar edição corretiva;
- criar fila de revisão;
- aprovar merges;
- revisar conflitos;
- criar workflows de qualidade.

Entregáveis:

- fila de revisão;
- status de curadoria;
- comentários;
- histórico;
- aprovação/rejeição;
- métricas de qualidade.

Critérios de sucesso:

- erros percebidos podem ser corrigidos com governança;
- conflitos são rastreados;
- curadoria não quebra rastreabilidade.

## Fase 7 — Escala enterprise/API-MCP comercial

Objetivos:

- preparar monetização híbrida;
- multiusuário;
- organizações;
- permissões;
- billing;
- SLA;
- API/MCP externos.

Entregáveis:

- RBAC/ABAC;
- tenants;
- API keys externas;
- rate limits por plano;
- billing usage;
- SSO;
- auditoria enterprise;
- documentação pública.

Critérios de sucesso:

- produto pode ser oferecido por API/MCP;
- uso é controlado por cliente;
- fontes licenciadas podem ser bloqueadas;
- segurança enterprise atende requisitos básicos.

---

# 19. Backlog técnico inicial

## 19.1 Backend

- definir arquitetura FastAPI ou alternativa;
- criar camada de serviços;
- criar endpoints internos;
- criar validação de payload;
- criar logs estruturados;
- criar autenticação;
- criar rate limits;
- criar documentação OpenAPI;
- criar testes unitários e integração.

## 19.2 Frontend

- implementar dashboard base;
- aplicar Design System GennomX;
- criar login;
- criar busca global;
- criar páginas de entidade;
- criar tabelas refinadas;
- criar filtros;
- criar tela de logs;
- criar tela de testes;
- criar testes e2e.

## 19.3 Dados

- criar schema inicial;
- criar entidades canônicas;
- criar tabelas de evidência;
- criar tabelas de logs;
- criar versionamento;
- criar raw storage;
- criar data quality checks;
- criar fixtures;
- criar testes de migração.

## 19.4 IA interna

- definir tarefas permitidas;
- criar extração estruturada com schema;
- criar classificação de documentos;
- criar geração de embeddings;
- criar validação de saída;
- criar logs de custo;
- criar proteção contra prompt injection indireta;
- criar testes com documentos adversariais.

## 19.5 MCP

- definir servidor MCP;
- criar ferramentas iniciais;
- definir schemas de entrada/saída;
- criar autenticação;
- criar tokens;
- criar rate limits;
- criar logs;
- criar testes por ferramenta;
- criar documentação;
- criar sandbox. Sandbox de agente, ai-jail e YOLO estão excluídos por D-044; a menção neste parágrafo é isolamento de produto, histórico ou finding, não adoção.

## 19.6 Infraestrutura

- manter PostgreSQL VPS, auth e storage segregados operacionalmente;
- configurar ambientes;
- configurar CI/CD;
- configurar secret management;
- configurar backups;
- configurar monitoramento;
- configurar logs;
- configurar storage;
- configurar deploy.

## 19.7 Segurança

- criar threat model inicial;
- definir papéis;
- ativar RLS onde aplicável;
- criar políticas de CORS;
- configurar headers;
- configurar secret scanning;
- configurar dependency scanning;
- configurar SAST;
- configurar container scanning;
- criar testes de autorização;
- criar plano de resposta a incidentes.

## 19.8 Testes e qualidade

- definir matriz de testes;
- configurar pytest;
- configurar Playwright;
- configurar testes de contrato;
- configurar data quality checks;
- configurar coverage mínimo;
- criar fixtures por fonte;
- criar testes MCP;
- criar testes de upload;
- criar testes de segurança;
- criar painel de status de testes.

## 19.9 Produto

- priorizar fluxos internos;
- definir personas;
- definir KPIs;
- definir telas do MVP;
- definir bundles prioritários;
- definir critérios de aceite;
- definir roadmap comercial futuro.

---

# 20. Decisões técnicas em aberto

## 20.1 Banco e serviços antes agrupados na Supabase — decisão encerrada

### Opção A — Supabase Cloud

Prós:

- menor esforço operacional;
- backups gerenciados;
- autenticação pronta;
- storage integrado;
- velocidade de MVP;
- menor complexidade inicial.

Contras:

- custo pode crescer;
- menor controle fino de infraestrutura;
- dependência de fornecedor;
- limitações conforme plano.

Recomendação inicial histórica: Supabase Cloud. Decisão vigente: PostgreSQL/pgvector na VPS,
JWT próprio/federado por flag e storage MinIO/S3-compatible.

### Opção B — Supabase self-host/VPS

Prós:

- maior controle;
- potencial economia em escala inicial;
- flexibilidade.

Contras:

- maior responsabilidade operacional;
- backup, segurança e updates sob responsabilidade própria;
- maior risco para MVP.

Recomendação:

- avaliar apenas se houver restrição de custo, privacidade ou controle.

## 20.2 FastAPI vs Node/Next API routes

### FastAPI

Prós:

- excelente para dados/IA;
- tipagem com Pydantic;
- OpenAPI automático;
- ecossistema Python;
- natural para conectores e pipelines.

Contras:

- exige manter backend separado do frontend.

### Node/Next API routes

Prós:

- integração com frontend;
- simplicidade para MVP web.

Contras:

- menos natural para pipelines de dados biomédicos;
- pode misturar responsabilidades.

Recomendação:

- **FastAPI para backend/API/MCP adjacente e Next.js para frontend**.

## 20.3 PostgreSQL full-text vs OpenSearch

Recomendação:

- começar com PostgreSQL full-text;
- migrar/adicionar OpenSearch se busca ficar central ou lenta.

## 20.4 pgvector vs vector DB dedicado

Recomendação:

- começar com pgvector;
- avaliar vector DB dedicado se embeddings crescerem muito.

## 20.5 Scraping próprio vs serviços externos

Recomendação:

- começar com scrapers próprios controlados para fontes essenciais;
- usar serviços externos apenas quando houver ganho claro e compliance aceitável.

## 20.6 API REST vs GraphQL

Recomendação:

- REST no MVP;
- GraphQL apenas se o consumo por frontend e clientes exigir composição flexível.

## 20.7 Ferramenta de data quality

Opções:

- Great Expectations;
- Soda;
- dbt tests;
- checks customizados.

Recomendação:

- começar com checks customizados + dbt/Great Expectations conforme maturidade.

## 20.8 Ferramenta de testes end-to-end

Recomendação:

- Playwright, pela maturidade para testes web modernos e suporte multi-browser.

## 20.9 Framework de segurança

Recomendação:

- usar OWASP ASVS como referência de requisitos;
- usar OWASP API Security Top 10 para API/MCP;
- usar OWASP WSTG como guia para testes de segurança;
- adaptar escopo ao MVP interno.

---

# 21. Suposições adotadas

1. A GennomX AI será multiárea desde o início.
2. O MVP será interno primeiro, mas desenhado para API/MCP comercial futuro.
3. O MCP será inicialmente usado por ChatGPT, Claude e agentes privados.
4. A aplicação não gerará relatórios finais como produto principal.
5. Modelos host externos gerarão relatórios consumindo dados via MCP.
6. O MVP incluirá dados de alto nível e dados granulares de endpoints/resultados.
7. A automação inicial será 100%, com edição corretiva humana quando erro for percebido.
8. A revisão humana ocorrerá após o relatório produzido pelo modelo host, não como etapa obrigatória antes de todo dado entrar na base.
9. Fontes prioritárias: ClinicalTrials.gov, PubMed/PMC, openFDA, DailyMed, EMA, Open Targets, ANVISA e abstracts de grandes congressos.
10. Não haverá integração com bases pagas no momento.
11. Banco e taxonomia devem ser preferencialmente em inglês.
12. Interface e relatórios externos podem ser bilíngues.
13. Dashboard deve seguir Design System GennomX.
14. Não haverá multiusuário enterprise no MVP, mas o modelo deve estar preparado.
15. Segurança e testes automáticos devem ser considerados requisitos de primeira classe.
16. Supabase foi preferência inicial e hoje é apenas histórico de migração.
17. Atualização dos dados deve ser diária quando a fonte permitir.
18. Scraping deve ser agressivo quando necessário, mas com salvaguardas legais e técnicas.

> Nota (item 9): a lista de fontes prioritárias acima é histórica. A ordem de implementação efetiva de novos conectores passa a ser definida manualmente pelo usuário na coluna `Prioridade` da planilha Excel `project_state/fontes_priorizacao.xlsx`, que também traz URL, tipo de acesso, API/export/scraping, complexidade e status de cada fonte candidata.

---

# 22. Critérios de sucesso do MVP

## 22.1 Dados

- fontes prioritárias integradas;
- entidades canônicas criadas;
- endpoints e resultados armazenados;
- evidências vinculadas;
- rastreabilidade funcional;
- atualização diária quando disponível;
- dados brutos preservados.

## 22.2 Usabilidade

- dashboard permite busca global;
- página de ativo é útil;
- página de trial é útil;
- evidências são fáceis de acessar;
- logs são compreensíveis;
- edição corretiva é simples;
- visual segue padrão premium GennomX.

## 22.3 MCP

- modelos host conseguem consultar dados;
- ferramentas retornam schemas estáveis;
- limites são aplicados;
- evidências são retornadas;
- logs são completos;
- tokens funcionam por cliente;
- consultas amplas são bloqueadas ou paginadas.

## 22.4 Segurança

- autenticação funcional;
- tokens protegidos;
- nenhum segredo no código;
- RLS/políticas preparadas;
- API sem endpoints abertos indevidos;
- MCP sem ferramenta administrativa;
- uploads protegidos;
- logs de auditoria ativos;
- backups configurados;
- testes críticos de segurança passando.

## 22.5 Testes automáticos

- cobertura unitária mínima definida;
- testes de conectores prioritários passando;
- testes de contrato criados;
- testes MCP essenciais passando;
- testes e2e essenciais passando;
- data quality checks executados;
- CI bloqueia deploy com falhas críticas;
- security scanning integrado.

## 22.6 Confiabilidade

- jobs reexecutáveis;
- falhas visíveis;
- retry/backoff configurados;
- alteração de schema detectada;
- dados antigos preservados;
- rollback possível;
- staging funcional.

## 22.7 Performance

- busca global responsiva;
- páginas principais carregam em tempo aceitável;
- ferramentas MCP respondem em tempo previsível;
- jobs longos assíncronos;
- limites impedem DoS acidental.

## 22.8 Valor analítico

- modelo host consegue gerar relatório útil a partir de bundle MCP;
- dados possuem evidência;
- lacunas são explícitas;
- comparação entre ativos é possível;
- pipeline de empresa é possível;
- histórico regulatório básico é possível.

## 22.9 Adoção

- uso interno recorrente;
- redução de tempo de coleta manual;
- confiança nas evidências;
- identificação de erros corrigíveis;
- base útil para relatórios externos.

---

# 23. Resumo final para orientar a codificação futura

## 23.1 Construir primeiro

1. Banco PostgreSQL/pgvector com entidades centrais.
2. Raw storage com versionamento e hash.
3. Conectores para ClinicalTrials.gov, PubMed/PMC, openFDA, DailyMed, EMA, Open Targets e ANVISA inicial — ordem real seguindo `Prioridade` em `project_state/fontes_priorizacao.xlsx`.
4. Pipeline de parsing, normalização, deduplicação e evidências.
5. Data quality checks mínimos.
6. Dashboard inicial com busca, páginas de entidade, logs e edição corretiva.
7. API interna segura.
8. Servidor MCP interno read-only.
9. Ferramentas MCP essenciais.
10. Logs MCP e API.
11. Testes unitários, integração, contrato, MCP, e2e e segurança.
12. CI/CD com gates mínimos.
13. Backups e monitoramento.

## 23.2 Por que essa ordem

Essa ordem cria primeiro o ativo central da GennomX AI: **dados proprietários estruturados, rastreáveis e seguros**. Em seguida, cria as interfaces operacionais e o MCP, que permitirão aos modelos host gerar análises externas com base em evidências.

O reforço de segurança e testes automáticos deve entrar desde o início porque a GennomX AI terá três características de risco:

1. conectores com múltiplas fontes externas;
2. dados biomédicos complexos sujeitos a erro de interpretação;
3. acesso por modelos host e agentes via MCP.

Sem testes automáticos e controles de segurança, o risco de regressão, vazamento, ingestão incorreta, tool abuse e perda de confiança aumenta rapidamente.

A prioridade do MVP não é construir um chatbot ou gerador interno de relatórios. A prioridade é construir uma **infraestrutura confiável de dados + MCP**, capaz de alimentar com segurança ChatGPT, Claude e agentes privados para análises externas, mantendo rastreabilidade, governança e qualidade.

---
