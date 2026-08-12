# 01 — Arquitetura da GennomX AI

## Estado arquitetural vigente — 2026-07-20

O alvo de banco é PostgreSQL/pgvector na VPS. O runtime de autenticação usa JWT local próprio e,
quando `PLATFORM_AUTH_ENABLED=true`, também aceita o contrato administrativo RS256 da Plataforma.
O runtime de object storage usa MinIO pela API S3-compatible nos buckets exclusivos
`gennomx-ai-{raw,processed,evidence}`. Cloudflare R2 é evolução futura por trás do mesmo contrato e
não foi provisionado. Supabase permanece somente no histórico de migração.

O Platform Auth não substitui JWT local, chave interna nem os tokens/scopes próprios do MCP.
## Governança operacional pré-gravação — 2026-06-21

O caminho executável passa a ser: conector → raw imutável → normalização → staging/deduplicação
DuckDB quando houver chaves repetidas no lote → quality gates → `PersistenceDecisionEngine` →
assertion bitemporal → projeção corrente. `AssertionService` aplica política por entidade/campo,
granularidade obrigatória, evidência, autoridade, confiança, freshness e ação determinística. LLM
interno (OPENCODE) executa apenas tarefas auxiliares de classificação, extração e triagem, nunca
decide fonte vencedora, merge, correção ou exclusão.

Workers marcam assertions vencidas para revalidação; retenção produz manifesto/checksum, arquiva
em object storage e só então permite exclusão. Legal hold bloqueia arquivo/exclusão. Coleta web
futura deve usar `ControlledScraper`.

Este documento descreve a arquitetura conceitual e técnica da aplicação, seus módulos principais, stack recomendada e diretrizes de armazenamento.

---

## 0. Premissa central do plano

A **GennomX AI** deve ser concebida como uma aplicação empresarial composta por dois núcleos principais:

1. **Banco de dados proprietário de inteligência biomédica e competitiva**  
   Estruturação, ingestão, normalização, deduplicação, enriquecimento, versionamento e disponibilização de dados sobre ativos terapêuticos, empresas, indicações, targets, ensaios clínicos, endpoints, resultados, aprovações, literatura, abstracts de congressos, safety e fontes regulatórias globais.

2. **Servidor MCP e ferramentas MCP seguras**  
   Camada de acesso inteligente que permite que modelos de IA host — como ChatGPT, Claude e agentes privados — consultem o banco proprietário por meio de ferramentas controladas, auditáveis e rastreáveis.

A **geração final de análises, relatórios de inteligência, competitive landscapes, due diligence memos e insights estratégicos não faz parte da aplicação GennomX AI em si**. Essa etapa será executada por **modelos de IA host externos ou agentes privados**, que acessarão a GennomX AI por meio do MCP.

A aplicação deve, portanto, entregar **dados estruturados, evidências, contexto, rastreabilidade e ferramentas de consulta**. Ela não deve depender de respostas generativas internas como produto principal.

### 0.1 Consequências arquiteturais dessa premissa

- O valor principal da GennomX AI está no **data asset proprietário**, não no chatbot.
- O MCP é a ponte entre os dados estruturados e os modelos host.
- Toda informação retornada ao modelo host deve ter, sempre que possível, ligação com fonte, documento, evidência, timestamp e grau de confiança.
- A segurança deve tratar o MCP como uma superfície crítica, pois ele permitirá consultas automatizadas por agentes.
- O dashboard é ferramenta operacional para explorar, monitorar, corrigir e auditar a base, não o único canal de consumo.
- O plano deve priorizar confiabilidade, teste automatizado, rastreabilidade, logs e governança desde o MVP.

---

# 1. Visão geral da arquitetura

A arquitetura deve ser organizada em camadas independentes, com baixo acoplamento, alta rastreabilidade e controles de segurança incorporados desde o início.

# 1. Visão geral da arquitetura

A arquitetura deve ser organizada em camadas independentes, com baixo acoplamento, alta rastreabilidade e controles de segurança incorporados desde o início.

## 1.1 Fluxo conceitual

**Fontes externas → Conectores → Raw storage → Parsing → Normalização → Deduplicação → Enriquecimento → Validação automática → Banco estruturado → Índices textuais/vetoriais → API/Dashboard/MCP → Modelos host → Relatórios externos.**

O ponto crítico é que os modelos host **não devem acessar diretamente dados crus, banco SQL, documentos sensíveis ou conectores externos**. Eles devem acessar ferramentas MCP projetadas para retornar dados estruturados, seguros, limitados e rastreáveis.

## 1.2 Camadas principais

1. **Fontes externas**  
   APIs públicas, exports oficiais, arquivos CSV/Excel/JSON/XML/PDF, registros clínicos, literatura científica, bases regulatórias, abstracts de congressos, press releases, investor decks, uploads internos e fontes sem API que exigem scraping controlado.

2. **Camada de ingestão**  
   Conectores especializados extraem dados de cada fonte respeitando método de acesso, frequência, limites, termos de uso, formato e política de atualização.

3. **Camada de processamento**  
   Parsing, limpeza, normalização, deduplicação, resolução de entidades, enriquecimento, classificação e validação automática.

4. **Camada de armazenamento**  
   Banco relacional, object storage/data lake, busca textual, embeddings e, futuramente, camada analítica escalável.

5. **Camada semântica**  
   Modelo de entidades, aliases, ontologias, taxonomias, mapeamentos externos e relações entre ativos, empresas, indicações, targets, ensaios e evidências.

6. **Camada MCP**  
   Servidor MCP com ferramentas orientadas a tarefas. O MCP deve atuar como uma camada de segurança e semântica, não como um túnel genérico para o banco.

7. **Camada de API**  
   API interna para dashboard, integrações e futura comercialização. Deve ser protegida por autenticação, autorização, rate limits e logs.

8. **Camada de aplicação web**  
   Dashboard para consulta, exploração, monitoramento, correção manual, administração de fontes, logs de ingestão e logs MCP.

9. **Camada de autenticação, autorização e governança**  
   Inicialmente simples, mas já preparada para evolução comercial por organizações, papéis, API keys, tokens MCP, escopos e auditoria.

10. **Camada de segurança aplicada**  
    Threat modeling, validação de entrada, proteção de segredos, isolamento de permissões, proteção contra abuso de ferramentas MCP, hardening de APIs, criptografia, backups e trilhas de auditoria.

11. **Camada de testes automáticos e qualidade**  
    Testes unitários, integração, contrato, end-to-end, regressão de conectores, data quality, segurança, performance e validação de ferramentas MCP.

12. **Camada de observabilidade**  
    Logs estruturados, métricas, rastreamento de jobs, alertas, custos, falhas de ingestão, mudanças de schema e uso do MCP.

---

# 2. Arquitetura sugerida em alto nível

## 2.1 Camada de ingestão

A camada de ingestão deve capturar dados de:

- ClinicalTrials.gov API v2;
- PubMed/PMC via NCBI E-utilities e APIs PMC;
- openFDA;
- DailyMed;
- EMA ePI/API/exports;
- Open Targets GraphQL/data downloads;
- ANVISA, incluindo fontes oficiais disponíveis, dados abertos, Bulário e consultas regulatórias;
- abstracts de grandes congressos;
- uploads internos;
- press releases;
- investor decks;
- fontes futuras.

Cada conector deve possuir:

- identificador único da fonte;
- método de acesso;
- tipo de dado;
- frequência de atualização;
- schema esperado;
- limites de uso;
- estratégia de paginação;
- política de retry;
- política de backoff;
- política de atualização incremental;
- parser associado;
- status de compliance/licença;
- owner técnico;
- testes mínimos de integridade;
- indicadores de saúde.

## 2.2 Camada de processamento

Responsável por:

- parsing de JSON, XML, CSV, Excel, HTML e PDF;
- extração de entidades;
- normalização de campos;
- padronização de fases clínicas;
- padronização de status regulatórios;
- identificação de endpoints;
- extração de resultados;
- extração de eventos adversos quando disponível;
- mapeamento de drogas, empresas, targets e indicações;
- deduplicação;
- resolução de aliases;
- geração de `EvidenceSnippet`;
- cálculo de confidence score;
- classificação de fonte;
- preparação para indexação textual e semântica;
- validação automática antes da persistência final.

## 2.3 Camada de armazenamento

### MVP recomendado

- **PostgreSQL/pgvector na VPS** como banco relacional principal.
- **JWT local próprio + Platform Auth RS256 por flag** para a API administrativa.
- **MinIO/S3-compatible** para documentos brutos e processados; R2 é alvo futuro.
- **PostgreSQL full-text search** para busca textual inicial.
- **pgvector** para embeddings em MVP avançado ou Fase 2.
- **DuckDB nos workers** para processamento local/analítico de arquivos grandes, validações batch e exploração offline.
- **Celery + Redis** para filas e execução assíncrona de ingestão e processamento.
- **OPENCODE (adaptador interno configurável)** com DeepSeek V4 Pro como motor de IA auxiliar para classificação, extração estruturada, sugestão de normalização e triagem.

### Escala futura

- PostgreSQL para entidades canônicas, permissões, dashboard e API.
- Object storage para data lake bruto e processado.
- OpenSearch/Elasticsearch para busca textual robusta.
- BigQuery/Snowflake para analytics em larga escala, se o volume justificar.
- pgvector, Qdrant, Weaviate ou Pinecone para busca semântica, conforme necessidade.

## 2.4 Camada semântica

A camada semântica deve padronizar:

- entidades canônicas;
- aliases;
- identificadores externos;
- relacionamentos;
- ontologias;
- vocabulários controlados;
- taxonomias de endpoints;
- normalização de fases;
- normalização de status regulatório;
- normalização de regiões;
- mapeamento entre fontes e entidades;
- confiança por fonte;
- regras de conflito entre fontes.

## 2.5 Camada MCP

A camada MCP deve expor ferramentas semânticas, não consultas SQL genéricas.

Exemplos de capacidades:

- buscar ativos por indicação;
- listar trials de um ativo;
- recuperar endpoints e resultados;
- comparar ativos com base em dados estruturados;
- recuperar evidências de uma afirmação;
- listar pipeline de empresa;
- recuperar status regulatório por região;
- consultar publicações associadas a um ativo;
- consultar histórico de atualizações de uma entidade;
- retornar pacotes de dados para relatórios externos por IA host.

## 2.6 Camada de API

A API deve servir ao dashboard, ao MCP e a futuras integrações.

No MVP, recomenda-se:

- API REST interna com FastAPI;
- endpoints protegidos por autenticação;
- validação forte de payloads;
- respostas versionadas;
- paginação obrigatória;
- limites de tamanho de resposta;
- logs por endpoint;
- documentação OpenAPI;
- testes de contrato.


Regras adicionais:

- rotas da API não devem executar jobs longos de ingestão, parsing, OCR, embeddings ou extração por IA;
- operações longas devem criar jobs Celery e retornar status rastreável;
- a API deve expor status, erros, métricas e logs dos workers;
- MCP e dashboard devem continuar responsivos durante ingestões pesadas.

No futuro, a API poderá evoluir para:

- REST pública;
- GraphQL controlado;
- API keys por cliente;
- rate limits por organização;
- billing por uso;
- controle por fonte/licença;
- SDKs internos.

## 2.7 Camada de aplicação web

Dashboard preferencialmente em **Next.js**, hospedado inicialmente em Vercel ou Netlify, para:

- explorar ativos;
- navegar por empresas;
- visualizar ensaios;
- consultar endpoints e resultados;
- monitorar fontes;
- revisar logs de ingestão;
- editar dados incorretos;
- acompanhar qualidade da base;
- configurar fontes e jobs;
- consultar logs MCP;
- monitorar testes de conectores;
- visualizar alertas de segurança e falhas operacionais.

## 2.8 Camada de autenticação e permissões

MVP:

- login simples;
- usuário administrador;
- token MCP interno;
- API key interna;
- logs de acesso;
- segregação mínima entre frontend, backend, banco e jobs.

Futuro:

- organizações;
- papéis;
- permissões granulares;
- isolamento de dados;
- fonte licenciada por cliente;
- SSO/SAML/OIDC;
- auditoria enterprise;
- rotação automática de chaves;
- segregação de ambientes por cliente enterprise.

## 2.9 Camada de observabilidade

Deve monitorar:

- ingestões;
- falhas de APIs;
- latência;
- volume de dados ingeridos;
- mudanças de schema;
- quebras de scrapers;
- falhas de parsing;
- falhas de deduplicação;
- conflitos entre fontes;
- uso do MCP;
- custo de IA;
- alertas de segurança;
- falhas de testes automáticos;
- qualidade dos dados.

---

# 3. Módulos principais da aplicação

## 3.1 Módulo de conectores

Responsável por conectar a GennomX AI às fontes oficiais e estruturadas.

### Funções

- executar chamadas de API;
- baixar exports oficiais;
- controlar paginação;
- detectar atualizações incrementais;
- registrar metadados de execução;
- armazenar raw payload;
- sinalizar falhas;
- acionar testes de contrato;
- controlar limites de acesso por fonte.

### Requisitos de segurança

- segredos nunca devem estar hardcoded;
- tokens/API keys devem estar em secret manager ou variáveis protegidas;
- cada conector deve operar com menor privilégio possível;
- domínios permitidos devem estar em allowlist;
- respostas externas devem ser tratadas como não confiáveis;
- payloads devem ser validados antes de processamento.

### Requisitos de teste

- testes unitários do parser;
- testes de contrato com payloads reais salvos;
- smoke tests controlados contra fonte externa;
- testes de regressão para mudanças de schema;
- testes de idempotência.

## 3.2 Módulo de scraping

Usado apenas quando não houver API, export oficial ou mecanismo estruturado aceitável.

### Funções

- acessar páginas públicas permitidas;
- respeitar robots.txt e termos de uso;
- aplicar rate limits conservadores;
- coletar HTML/PDF quando permitido;
- extrair metadados;
- registrar URL, data de acesso e método de extração;
- armazenar snapshot da fonte quando juridicamente permitido.

### Requisitos de segurança e compliance

- scraping deve ter allowlist de domínios;
- bloqueio de domínios não aprovados;
- prevenção contra SSRF;
- limitação de redirecionamentos;
- sanitização de HTML;
- bloqueio de execução de scripts de página;
- registro de termos de uso analisados;
- logs de volume por domínio;
- possibilidade de desativar fonte imediatamente.

## 3.3 Módulo de ingestão de arquivos

Responsável por uploads manuais e imports de arquivos.

### Formatos

- CSV;
- Excel;
- JSON;
- XML;
- PDF;
- ZIP;
- TXT;
- HTML.

### Segurança

- verificação de tipo MIME;
- limite de tamanho;
- antivírus/anti-malware quando aplicável;
- armazenamento inicial em área de quarentena;
- parsing em sandbox;
- rejeição de arquivos com macros ativas;
- sanitização de nomes de arquivos;
- controle de permissões;
- hash do arquivo original;
- versionamento.

### Testes

- testes com arquivos válidos;
- testes com arquivos corrompidos;
- testes com formatos inesperados;
- testes com arquivos grandes;
- testes de limites de upload;
- testes de segurança para payloads maliciosos conhecidos.

## 3.4 Módulo de normalização

Transforma dados heterogêneos em formatos canônicos.

### Funções

- padronizar nomes de drogas;
- padronizar empresas;
- padronizar indicações;
- normalizar fases clínicas;
- normalizar status de trial;
- normalizar status regulatório;
- mapear sinônimos;
- converter unidades;
- registrar transformações;
- manter campo original e campo normalizado.

### Testes

- golden tests para normalizações críticas;
- testes de equivalência de aliases;
- testes de unidades;
- testes de regressão para drogas conhecidas;
- validação de preservação do valor original.

## 3.5 Módulo de deduplicação

Responsável por identificar registros equivalentes vindos de múltiplas fontes.

### Estratégias

- chaves externas quando disponíveis;
- NCT ID para ensaios clínicos;
- DOI/PMID/PMCID para publicações;
- identificadores regulatórios;
- normalização textual;
- matching probabilístico;
- revisão posterior de conflitos.

### Segurança e qualidade

Deduplicação incorreta é risco técnico relevante porque pode fundir ativos diferentes ou separar evidências de um mesmo ativo. O sistema deve preservar:

- registros originais;
- motivo da fusão;
- score de confiança;
- fonte vencedora;
- fontes alternativas;
- possibilidade de desfazer merge.

## 3.6 Módulo de enriquecimento por IA

Uso interno da IA para:

- classificar tipo de documento;
- extrair endpoints;
- identificar resultados;
- sugerir entidade canônica;
- gerar resumos internos de documentos;
- classificar relevância;
- detectar inconsistências;
- sugerir evidências relacionadas.

### Limites

A IA interna não deve:

- criar fatos sem evidência;
- substituir fonte primária;
- gerar relatório final como produto principal da aplicação;
- sobrescrever dado estruturado sem versionamento;
- alimentar o banco sem confidence score e rastreabilidade.

### Segurança específica de IA

- documentos externos devem ser tratados como conteúdo não confiável;
- prompts internos devem instruir o modelo a ignorar instruções contidas em documentos-fonte;
- saídas devem passar por schema validation;
- respostas sem evidência devem ser marcadas como não persistíveis;
- extrações por IA devem ser auditáveis.

## 3.7 Módulo de validação e edição corretiva

O MVP será 100% automatizado, mas deve permitir edição humana quando erro for identificado.

### Funções

- editar campo estruturado;
- registrar quem editou;
- registrar motivo;
- preservar valor anterior;
- vincular correção a fonte/evidência;
- marcar campo como revisado;
- sinalizar entidade como conflituosa;
- permitir rollback.

## 3.8 Módulo de banco de dados

Responsável por:

- entidades canônicas;
- tabelas de relacionamento;
- histórico de versões;
- evidências;
- logs;
- usuários;
- permissões;
- metadados de fontes;
- jobs de ingestão;
- logs MCP;
- resultados de testes de ingestão.

## 3.9 Módulo MCP

Responsável por:

- expor ferramentas para modelos host;
- validar argumentos;
- aplicar permissões;
- aplicar limites de resposta;
- registrar logs;
- retornar evidências;
- recusar consultas inseguras;
- reduzir risco de hallucination do modelo host por meio de respostas estruturadas.

## 3.10 Módulo de bundles para relatórios externos

Este módulo não gera relatórios finais. Ele prepara **pacotes estruturados de dados e evidências** para que modelos host produzam relatórios fora da aplicação.

Exemplos:

- bundle de asset profile;
- bundle de company pipeline;
- bundle de competitive landscape;
- bundle de safety overview;
- bundle de regulatory history;
- bundle de target landscape;
- bundle de trial benchmark.

Cada bundle deve conter:

- dados estruturados;
- evidências;
- fontes;
- datas de atualização;
- lacunas conhecidas;
- conflitos entre fontes;
- nível de confiança;
- limitações de uso.

## 3.11 Módulo de dashboard

Interface premium e analítica para:

- busca global;
- páginas de entidades;
- painéis de ingestão;
- painéis de qualidade;
- logs MCP;
- logs de API;
- edição corretiva;
- monitoramento de fontes;
- painel de segurança operacional;
- painel de testes automáticos.

## 3.12 Módulo administrativo

Responsável por:

- cadastro de fontes;
- configuração de jobs;
- ativação/desativação de conectores;
- gerenciamento de tokens internos;
- visualização de logs;
- políticas de retenção;
- configuração de limites do MCP;
- revisão de falhas de teste;
- revisão de alertas de segurança.

---

# 5. Estratégia de banco de dados

## 5.1 Recomendação para MVP

A recomendação inicial foi Supabase/PostgreSQL. A arquitetura vigente concluiu sua remoção do
runtime: PostgreSQL/pgvector vive na VPS, auth é próprio/federado por flag e storage é
S3-compatible. A escolha de PostgreSQL como núcleo permanece por combinar:

- banco relacional maduro;
- autenticação integrada;
- APIs automáticas quando úteis;
- storage integrado;
- suporte a Row Level Security;
- extensões PostgreSQL;
- pgvector;
- bom equilíbrio entre velocidade de MVP e robustez.

## 5.2 Por que PostgreSQL no MVP

Vantagens:

- modelagem relacional adequada para entidades biomédicas;
- suporte a JSONB para payloads semiestruturados;
- full-text search inicial;
- integridade referencial;
- possibilidade de versionamento;
- controle transacional;
- boa experiência de desenvolvimento;
- integração com dashboard e API.

Riscos:

- grandes volumes analíticos podem exigir camada complementar;
- busca textual complexa pode ficar limitada;
- embeddings em larga escala podem demandar vector DB dedicado;
- configuração incorreta de RLS pode gerar risco de vazamento.

## 5.3 Uso de object storage/data lake

O data lake deve armazenar:

- payloads brutos de API;
- exports originais;
- PDFs baixados;
- HTML snapshots permitidos;
- arquivos enviados manualmente;
- documentos parseados;
- logs brutos;
- artefatos de testes.

Separar camadas:

- **raw**: dado original sem transformação;
- **processed**: dado parseado e limpo;
- **curated**: dado validado e pronto para entidade canônica;
- **evidence**: trechos usados para sustentação;
- **archive**: versões antigas.

## 5.4 Uso de DuckDB

DuckDB deve ser utilizado para:

- análise local de grandes arquivos;
- validações batch;
- exploração de exports;
- testes de qualidade de dados;
- comparação entre snapshots;
- prototipagem de transformações.

## 5.5 Uso de BigQuery/Snowflake

Não é obrigatório no MVP. Deve ser considerado quando:

- volume de dados crescer muito;
- houver necessidade de analytics complexa;
- múltiplos usuários consultarem grandes datasets;
- relatórios externos exigirem agregações pesadas;
- logs MCP/API se tornarem volumosos.

## 5.6 Uso de OpenSearch/Elasticsearch

Deve ser considerado após o MVP se:

- a busca textual do PostgreSQL for insuficiente;
- houver necessidade de ranking avançado;
- queries textuais ficarem lentas;
- busca em documentos longos se tornar central;
- filtros facetados ficarem complexos.

## 5.7 Uso de banco vetorial

No MVP, pgvector pode ser suficiente para:

- busca semântica de snippets;
- similaridade de documentos;
- recuperação de trechos de evidência;
- apoio a modelos host.

Vector DB dedicado deve ser considerado se:

- houver milhões de embeddings;
- baixa latência for necessária;
- filtros vetoriais complexos forem críticos;
- embeddings passarem a ser componente central do produto.

## 5.8 Segurança no banco

Requisitos mínimos:

- criptografia em repouso quando disponível;
- TLS em trânsito;
- roles segregadas para aplicação, jobs e leitura analítica;
- nenhuma credencial de administrador usada por aplicação web;
- Row Level Security preparada desde o início, mesmo que permissões sejam simples no MVP;
- views seguras para exposição via API/MCP;
- migrações versionadas;
- backups automáticos;
- testes de restauração;
- logs de queries administrativas;
- mascaramento ou hashing de dados sensíveis operacionais.

---

## Integração com a Plataforma GennomX

O backend aceita autenticação administrativa da Plataforma GennomX por feature flag e scopes
`ai:*`. Essa camada não substitui tokens MCP de ChatGPT/Claude/agentes, não concede acesso direto
ao SQL e não relaxa RLS/roles do PostgreSQL.
