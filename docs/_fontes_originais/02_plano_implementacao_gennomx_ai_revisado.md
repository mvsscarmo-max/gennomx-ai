# 02 — Plano Detalhado de Implementação da GennomX AI

**Arquivo:** `02_plano_implementacao_gennomx_ai.md`  
**Versão:** 2.0 — revisão com reforço de segurança e testes automáticos  
**Data:** 04/06/2026  
**Projeto:** GennomX AI  
**Natureza do documento:** racional técnico e estratégico para orientar produto, engenharia, dados, IA, MCP, segurança, qualidade e futura codificação.  
**Escopo desta versão:** planejamento. Nenhum código deve ser implementado nesta etapa.

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

- **Supabase/PostgreSQL** como banco relacional principal.
- **Supabase Storage ou S3-compatible storage** para documentos brutos e arquivos processados.
- **PostgreSQL full-text search** para busca textual inicial.
- **pgvector** para embeddings em MVP avançado ou Fase 2.
- **DuckDB** para processamento local/analítico de arquivos grandes, validações batch e exploração offline.

### Escala futura

- PostgreSQL/Supabase para entidades canônicas, permissões, dashboard e API.
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

No futuro, a API poderá evoluir para:

- REST pública;
- GraphQL controlado;
- API keys por cliente;
- rate limits por organização;
- billing por uso;
- controle por fonte/licença;
- SDKs internos.

## 2.7 Camada de aplicação web

Dashboard para:

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

# 4. Modelo de dados conceitual

## 4.1 Princípios do modelo

O modelo deve priorizar:

- entidades canônicas;
- rastreabilidade;
- versionamento;
- fonte original preservada;
- separação entre dado bruto, dado processado e dado enriquecido;
- possibilidade de correção humana;
- logs de uso;
- suporte a ferramentas MCP.

## 4.2 Entidades centrais

### DrugAsset

Representa um ativo terapêutico.

Campos conceituais:

- internal_id;
- primary_name;
- aliases;
- modality;
- mechanism_of_action_id;
- targets;
- sponsors;
- indications;
- development_stage;
- regulatory_status;
- source_confidence;
- created_at;
- updated_at.

### Company

Representa empresa farmacêutica, biotech, universidade, sponsor, colaborador ou detentor de ativo.

Campos conceituais:

- internal_id;
- legal_name;
- aliases;
- company_type;
- country;
- website;
- investor_relations_url;
- pipeline_url;
- source_documents;
- created_at;
- updated_at.

### ClinicalTrial

Representa ensaio clínico.

Campos conceituais:

- internal_id;
- nct_id;
- title;
- brief_title;
- phase;
- status;
- sponsor;
- collaborators;
- indications;
- interventions;
- arms;
- enrollment;
- start_date;
- primary_completion_date;
- completion_date;
- countries;
- registry_source;
- source_documents;
- updated_at.

### Indication

Representa doença, condição clínica ou área terapêutica.

Campos conceituais:

- internal_id;
- preferred_name;
- aliases;
- ontology_ids;
- therapeutic_area;
- parent_indication;
- child_indications.

### Target

Representa alvo biológico.

Campos conceituais:

- internal_id;
- symbol;
- name;
- aliases;
- organism;
- external_ids;
- associated_indications;
- linked_assets.

### MechanismOfAction

Representa mecanismo de ação.

Campos conceituais:

- internal_id;
- name;
- description;
- target_id;
- modality;
- source_evidence.

### Endpoint

Representa endpoint clínico.

Campos conceituais:

- internal_id;
- endpoint_name;
- endpoint_type;
- category;
- timepoint;
- measurement_unit;
- trial_id;
- arm_id;
- source_evidence.

### TrialResult

Representa resultado associado a trial, endpoint e braço.

Campos conceituais:

- internal_id;
- trial_id;
- endpoint_id;
- arm_id;
- result_value;
- comparator_value;
- statistical_measure;
- p_value;
- confidence_interval;
- hazard_ratio;
- odds_ratio;
- timepoint;
- population;
- source_evidence;
- confidence_score.

### AdverseEvent

Representa evento adverso ou achado de segurança.

Campos conceituais:

- internal_id;
- drug_asset_id;
- trial_id;
- event_name;
- grade;
- seriousness;
- incidence;
- comparator_incidence;
- population;
- source_evidence.

### RegulatoryApproval

Representa decisão regulatória ou status em determinada região.

Campos conceituais:

- internal_id;
- drug_asset_id;
- region;
- agency;
- approval_status;
- approval_date;
- indication;
- label_url;
- regulatory_document_id;
- source_evidence.

### Publication

Representa artigo científico.

Campos conceituais:

- internal_id;
- title;
- journal;
- publication_date;
- doi;
- pmid;
- pmcid;
- abstract;
- linked_trials;
- linked_assets;
- source_url;
- evidence_snippets.

### ConferenceAbstract

Representa abstract de congresso.

Campos conceituais:

- internal_id;
- congress_name;
- year;
- abstract_number;
- title;
- authors;
- session;
- linked_assets;
- linked_trials;
- linked_results;
- source_url;
- access_status.

### PressRelease

Representa comunicado corporativo.

Campos conceituais:

- internal_id;
- company_id;
- title;
- publication_date;
- url;
- linked_assets;
- linked_trials;
- extracted_claims;
- source_evidence.

### InvestorDeck

Representa apresentação corporativa ou deck de investidores.

Campos conceituais:

- internal_id;
- company_id;
- title;
- document_date;
- url;
- file_hash;
- linked_assets;
- linked_trials;
- evidence_snippets.

### SourceDocument

Representa documento-fonte preservado ou referência de fonte.

Campos conceituais:

- internal_id;
- source_id;
- source_type;
- title;
- url;
- file_path;
- hash;
- retrieved_at;
- license_status;
- raw_storage_path;
- parsed_storage_path.

### EvidenceSnippet

Representa trecho ou fragmento de evidência extraído de uma fonte.

Campos conceituais:

- internal_id;
- source_document_id;
- entity_type;
- entity_id;
- text_excerpt;
- page_number;
- section;
- extraction_method;
- confidence_score;
- created_at.

### DataSource

Representa fonte de dados.

Campos conceituais:

- internal_id;
- name;
- category;
- access_method;
- official_url;
- api_url;
- license_status;
- update_frequency;
- connector_status;
- compliance_notes;
- owner;
- last_successful_run;
- last_failed_run.

### IngestionJob

Representa execução de ingestão.

Campos conceituais:

- internal_id;
- data_source_id;
- job_type;
- started_at;
- finished_at;
- status;
- records_fetched;
- records_inserted;
- records_updated;
- records_rejected;
- error_summary;
- test_status;
- raw_log_path.

### User

Representa usuário interno ou futuro usuário externo.

Campos conceituais:

- internal_id;
- email;
- name;
- role;
- organization_id;
- status;
- last_login;
- mfa_enabled.

### Organization

Representa organização interna ou futura cliente.

No MVP pode existir apenas uma organização interna. O modelo deve ser preparado para futuro SaaS.

### Report

Representa artefato externo ou referência de relatório gerado por modelo host.

Importante: a GennomX AI não gera o relatório final, mas pode registrar metadados sobre relatórios produzidos externamente.

Campos conceituais:

- internal_id;
- title;
- report_type;
- generated_by_host_model;
- generated_at;
- query_bundle_id;
- related_entities;
- evidence_set;
- status.

### MCPQueryLog

Representa log de consulta MCP.

Campos conceituais:

- internal_id;
- timestamp;
- tool_name;
- requesting_client;
- user_id;
- organization_id;
- input_hash;
- normalized_arguments;
- result_count;
- latency_ms;
- status;
- error_type;
- source_entities_accessed;
- safety_flags.

### SecurityEvent

Nova entidade recomendada para registrar eventos de segurança.

Campos conceituais:

- internal_id;
- timestamp;
- event_type;
- severity;
- actor_type;
- actor_id;
- source_ip_hash;
- endpoint_or_tool;
- description;
- action_taken;
- status.

### TestRun

Nova entidade recomendada para registrar execuções de testes automáticos relevantes à operação.

Campos conceituais:

- internal_id;
- test_suite;
- environment;
- started_at;
- finished_at;
- status;
- failed_tests;
- coverage_summary;
- related_deployment;
- related_connector;
- artifact_url.

## 4.3 Relacionamentos principais

- DrugAsset pode estar associado a múltiplas Company.
- DrugAsset pode ter múltiplas Indication.
- DrugAsset pode ter múltiplos Target.
- DrugAsset pode aparecer em múltiplos ClinicalTrial.
- ClinicalTrial pode ter múltiplos Endpoint.
- Endpoint pode ter múltiplos TrialResult.
- TrialResult deve estar ligado a EvidenceSnippet.
- EvidenceSnippet deve estar ligado a SourceDocument.
- SourceDocument deve estar ligado a DataSource.
- RegulatoryApproval deve estar ligado a DrugAsset, Indication e SourceDocument.
- Publication pode estar ligada a DrugAsset, ClinicalTrial, Target e Indication.
- ConferenceAbstract pode estar ligado a TrialResult.
- MCPQueryLog deve registrar quais entidades foram acessadas.
- SecurityEvent pode estar ligado a User, API key, MCP token ou job.
- TestRun pode estar ligado a deploy, conector, pipeline ou ambiente.

## 4.4 Rastreabilidade entre dado estruturado e fonte original

Cada dado crítico deve permitir responder:

- Qual fonte originou a informação?
- Quando foi coletada?
- Qual conector coletou?
- Qual documento ou endpoint externo foi usado?
- Qual trecho sustenta a informação?
- A extração foi automática, por IA ou corrigida por humano?
- Qual é o score de confiança?
- Houve conflito com outra fonte?
- Qual versão anterior existia?
- Quem editou manualmente, se houve edição?

---

# 5. Estratégia de banco de dados

## 5.1 Recomendação para MVP

A recomendação inicial é utilizar **Supabase/PostgreSQL** como núcleo, por combinar:

- banco relacional maduro;
- autenticação integrada;
- APIs automáticas quando úteis;
- storage integrado;
- suporte a Row Level Security;
- extensões PostgreSQL;
- pgvector;
- bom equilíbrio entre velocidade de MVP e robustez.

## 5.2 Por que PostgreSQL/Supabase no MVP

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

# 6. Pipeline de ingestão

## 6.1 Fluxo padrão

1. **Descoberta da fonte**  
   Identificar fonte, escopo, formato, licença, método de acesso e frequência.

2. **Registro da fonte**  
   Cadastrar em `DataSource` com status de compliance e metadados.

3. **Extração**  
   Coletar dados via API, export, upload, MCP externo ou scraping autorizado.

4. **Armazenamento bruto**  
   Salvar payload original em raw storage com hash e timestamp.

5. **Parsing**  
   Converter dados para formato intermediário estruturado.

6. **Validação inicial**  
   Validar schema, campos obrigatórios, formatos e integridade.

7. **Normalização**  
   Padronizar nomes, fases, status, unidades, datas e aliases.

8. **Deduplicação**  
   Identificar equivalências e conflitos.

9. **Enriquecimento**  
   Adicionar relações, taxonomias, embeddings, summaries internos e classificações.

10. **Validação automática**  
    Rodar regras de qualidade, testes de consistência e checks de plausibilidade.

11. **Persistência**  
    Gravar entidades canônicas e relacionamentos.

12. **Indexação**  
    Atualizar índices textuais, vetoriais e views MCP.

13. **Auditoria**  
    Registrar job, erros, métricas, deltas e evidências.

14. **Monitoramento**  
    Acionar alertas em caso de falha, queda de volume, mudança de schema ou anomalia.

## 6.2 Ingestão via API

Prioritária sempre que disponível.

Requisitos:

- autenticação segura quando necessária;
- paginação;
- rate limits;
- retries;
- backoff;
- armazenamento do payload bruto;
- validação de schema;
- testes de contrato;
- monitoramento de mudanças;
- logs por execução.

## 6.3 Ingestão via export oficial

Deve ser usada quando API não existir, mas houver CSV, Excel, XML, ZIP ou JSON oficial.

Requisitos:

- checar atualização do arquivo;
- baixar versão completa;
- calcular hash;
- comparar com versão anterior;
- processar incrementalmente quando possível;
- preservar arquivo original;
- validar colunas e tipos;
- gerar alerta se schema mudar.

## 6.4 Upload manual

Deve permitir ingestão interna controlada.

Exemplos:

- listas internas;
- planilhas de curadoria;
- documentos de pipeline;
- PDFs de congresso;
- arquivos regulatórios baixados manualmente.

## 6.5 Ingestão via MCP externo

Pode ser usada em fase posterior, mas deve ser tratada com cautela.

Requisitos:

- MCP externo deve ser fonte registrada;
- ferramentas externas devem ser allowlisted;
- respostas devem ser salvas como dado intermediário, não como verdade final;
- todo dado deve ser rastreado até fonte original quando possível;
- outputs de modelos não devem ser usados como fonte primária sem evidência.

## 6.6 Scraping

Será necessário para congressos, páginas corporativas, press releases, investor decks e fontes sem API.

Regras:

- usar API/export oficial sempre que disponível;
- usar scraping apenas com salvaguardas legais;
- respeitar robots.txt e termos de uso;
- aplicar rate limits;
- identificar claramente a fonte;
- registrar data de acesso;
- não contornar autenticação, paywall ou medidas técnicas;
- não copiar conteúdo integral protegido quando não houver permissão;
- armazenar preferencialmente metadados e trechos de evidência necessários;
- permitir remoção/bloqueio de fonte.

## 6.7 Testes no pipeline de ingestão

Cada pipeline deve ter:

- teste de disponibilidade da fonte;
- teste de contrato de schema;
- teste de parser;
- teste de transformação;
- teste de deduplicação;
- teste de idempotência;
- teste de carga mínima;
- teste de amostra contra valores esperados;
- teste de rollback;
- teste de reprocessamento.

---

# 7. Priorização de fontes para o MVP

## 7.1 Critérios de prioridade

- valor analítico;
- disponibilidade de API/export oficial;
- estabilidade técnica;
- licença clara;
- dados estruturados;
- cobertura global;
- relação direta com ativos, trials, resultados e status;
- complexidade de implementação;
- risco jurídico.

## 7.2 Tabela de prioridade

| Fonte | Tipo de dado | Método recomendado | Complexidade | Valor | Prioridade |
|---|---|---:|---:|---:|---:|
| ClinicalTrials.gov | Ensaios, fases, status, endpoints declarados | API oficial | Baixa/Média | Muito alto | MVP 1 |
| PubMed/PMC | Literatura, abstracts, artigos OA | APIs NCBI/PMC | Média | Muito alto | MVP 1 |
| openFDA | Eventos adversos, labels, recalls, approvals | API/bulk | Média | Muito alto | MVP 1 |
| DailyMed | Labels SPL | API/ZIP | Média | Alto | MVP 1 |
| EMA | Medicamentos, EPAR/ePI/exports | API/export | Média | Alto | MVP 1 |
| Open Targets | Targets, doenças, associações | GraphQL/downloads | Média | Muito alto | MVP 1 |
| ANVISA | Bulário, registros, dados regulatórios | APIs/exports oficiais quando disponíveis; scraping controlado se necessário | Média/Alta | Alto para Brasil | MVP 1+ |
| ASCO/ESMO/AACR/ASH | Abstracts de congresso | scraping/exports quando disponíveis | Alta | Muito alto | MVP+ |
| Press releases | Resultados e eventos corporativos | scraping controlado/RSS quando disponível | Alta | Alto | Fase 2 |
| Investor decks | Pipeline e dados corporativos | scraping/download controlado | Alta | Alto | Fase 2 |
| DrugBank | Drogas, targets, interações | API licenciada | Média | Alto | Futuro, sem integração agora |
| Evaluate/Citeline/GlobalData/IQVIA | Mercado/pipeline comercial | Licença/API/export | Alta | Alto | Futuro, sem integração agora |

## 7.3 MVP de dados estruturados

Priorizar:

1. ClinicalTrials.gov;
2. PubMed/PMC;
3. openFDA;
4. DailyMed;
5. EMA;
6. Open Targets;
7. ANVISA.

## 7.4 MVP+ congressos

Adicionar:

- ASCO;
- ESMO;
- AACR;
- ASH;
- congressos específicos por área terapêutica.

## 7.5 Atualização por fonte

A frequência deve ser configurável por fonte.

- Fontes com atualização diária: preferir execução diária.
- Fontes com atualização semanal: execução semanal.
- Congressos: execução intensiva em janelas pré, durante e pós-congresso.
- Press releases: execução diária ou várias vezes ao dia em fase futura.
- Fontes estáveis: execução sob demanda ou semanal.

---

# 8. Estratégia MCP

## 8.1 Função do servidor MCP

O servidor MCP da GennomX AI deve ser a camada nativa para modelos host consultarem dados do banco proprietário.

Ele deve:

- expor ferramentas de alto nível;
- validar argumentos;
- controlar permissões;
- limitar resultados;
- retornar dados estruturados;
- retornar evidências;
- registrar logs;
- impedir consultas genéricas perigosas;
- evitar exposição de SQL;
- proteger fontes licenciadas futuras;
- permitir uso por ChatGPT, Claude e agentes privados.

## 8.2 Princípio fundamental

O MCP deve entregar **pacotes confiáveis de dados**, não análises finais.

O modelo host poderá usar esses pacotes para redigir relatórios, mas a GennomX AI deve entregar:

- registros estruturados;
- evidências;
- citações;
- metadados;
- limitações;
- conflitos;
- timestamps;
- lacunas.

## 8.3 Ferramentas MCP iniciais

### search_drugs

Busca ativos terapêuticos.

Entradas:

- query;
- indication;
- target;
- modality;
- phase;
- company;
- region;
- limit.

Saídas:

- lista de DrugAsset;
- aliases;
- fase mais avançada;
- indicações;
- targets;
- empresas;
- status regulatório;
- fontes principais;
- last_updated.

### find_trials

Busca ensaios clínicos.

Entradas:

- drug_asset;
- indication;
- phase;
- status;
- sponsor;
- country;
- date_range;
- limit.

Saídas:

- trials;
- NCT ID quando disponível;
- fase;
- status;
- sponsor;
- intervenções;
- endpoints;
- datas;
- fonte.

### compare_assets

Retorna dados estruturados para comparação entre ativos.

Entradas:

- assets;
- indication;
- endpoints de interesse;
- population;
- phase;
- source_priority.

Saídas:

- tabela comparativa;
- trials associados;
- endpoints;
- resultados;
- safety resumido;
- evidências;
- limitações.

### get_company_pipeline

Retorna pipeline de empresa.

Entradas:

- company_name;
- indication;
- phase;
- modality;
- include_discontinued.

Saídas:

- ativos;
- fases;
- indicações;
- targets;
- trials;
- eventos recentes;
- fontes.

### get_trial_results

Retorna resultados de um ensaio.

Entradas:

- trial_id;
- nct_id;
- endpoint_type;
- population.

Saídas:

- endpoints;
- resultados;
- braços;
- timepoints;
- estatísticas;
- adverse events;
- evidence snippets.

### search_publications

Busca publicações relacionadas.

Entradas:

- asset;
- target;
- indication;
- trial_id;
- date_range;
- publication_type.

Saídas:

- publicações;
- DOI/PMID/PMCID;
- abstract;
- linked entities;
- evidências.

### get_regulatory_status

Retorna status regulatório.

Entradas:

- asset;
- indication;
- region;
- agency.

Saídas:

- status;
- agência;
- data;
- indicação;
- label/documento;
- evidências.

### build_report_data_bundle

Prepara pacote de dados para relatório externo por IA host.

Entradas:

- report_type;
- entity_ids;
- therapeutic_area;
- indication;
- date_range;
- evidence_depth;
- include_limitations.

Saídas:

- dados estruturados;
- tabelas prontas;
- evidências;
- lacunas;
- conflitos;
- avisos de qualidade;
- metadados de atualização.

### fetch_source_evidence

Recupera evidências específicas.

Entradas:

- evidence_id;
- source_document_id;
- entity_id.

Saídas:

- trecho;
- documento;
- URL;
- página/seção;
- data de coleta;
- licença/status de uso.

## 8.4 Segurança MCP

Requisitos obrigatórios:

- autenticação por token interno no MVP;
- tokens diferentes para ChatGPT, Claude e agentes privados;
- escopos por ferramenta;
- expiração e rotação de tokens;
- rate limit por cliente;
- limite de resultados por ferramenta;
- paginação obrigatória;
- bloqueio de consulta SQL ou expressão arbitrária;
- validação rígida de argumentos;
- logs completos;
- bloqueio de ferramentas administrativas para modelos host;
- modo read-only para ferramentas usadas por modelos host;
- denylist de parâmetros perigosos;
- allowlist de campos retornáveis;
- auditoria de entidades acessadas;
- alertas para consultas volumosas/anômalas.

## 8.5 Proteções contra abuso de ferramenta

O servidor MCP deve impedir:

- extração massiva de base completa;
- enumeração não controlada de entidades;
- consultas sem limite;
- acesso a segredos;
- acesso a logs sensíveis;
- acesso a dados de fontes futuras sem licença;
- execução de comandos;
- acesso direto a banco;
- escrita no banco por modelo host no MVP.

## 8.6 Proteção contra prompt injection indireta

Como documentos externos podem conter instruções maliciosas, o sistema deve:

- tratar conteúdo de documentos como dado, não como instrução;
- separar prompts internos de conteúdo extraído;
- validar saídas de extração por schema;
- impedir que trechos de documentos alterem comportamento de ferramentas;
- sinalizar documentos com conteúdo suspeito;
- registrar origem de todo texto retornado;
- aplicar limites de tamanho e contexto.

## 8.7 Logging MCP

Cada chamada MCP deve registrar:

- cliente;
- usuário/token;
- ferramenta;
- argumentos normalizados;
- hash de input;
- quantidade de resultados;
- entidades acessadas;
- fontes acessadas;
- latência;
- status;
- erro;
- safety flags;
- custo estimado quando houver IA interna.

---

# 9. Camada de IA e preparação para modelos host

## 9.1 Uso interno de IA

A IA interna pode ser usada para:

- extração estruturada;
- classificação;
- enriquecimento;
- sumarização técnica interna;
- identificação de relações;
- sugestão de aliases;
- identificação de endpoints;
- detecção de inconsistências;
- geração de embeddings.

## 9.2 O que a IA interna não deve fazer como produto principal

A IA interna não deve ser tratada como camada principal de geração de relatórios finais.

Não deve:

- produzir memorandos finais para clientes como núcleo da aplicação;
- tomar decisões sem evidência;
- criar claims sem fonte;
- substituir validações estruturadas;
- sobrescrever dados sem versionamento;
- ocultar incerteza.

## 9.3 Diferença entre tarefas de IA

### Extração estruturada

Transformar texto em campos estruturados, com schema validado.

### Classificação

Classificar documento, endpoint, modalidade, área terapêutica ou tipo de evidência.

### Enriquecimento

Sugerir relações entre entidades, aliases e taxonomias.

### Sumarização interna

Criar resumos operacionais vinculados a evidências.

### Geração de relatório externo

Realizada por modelos host fora da GennomX AI, consumindo ferramentas MCP.

### Consulta em linguagem natural

Realizada pelos modelos host, mas ancorada nas ferramentas MCP.

## 9.4 Requisitos para respostas com evidência

Ferramentas MCP devem retornar:

- IDs internos;
- IDs externos;
- fonte;
- data de coleta;
- evidência;
- confidence score;
- conflitos;
- limitações;
- lacunas.

## 9.5 Estratégias contra hallucination

- priorizar dados estruturados;
- retornar evidências junto com dados;
- usar respostas restritas por schema;
- evitar texto livre quando tabela bastar;
- indicar ausência de dado;
- diferenciar dado observado de inferência;
- incluir timestamps;
- limitar escopo da resposta MCP;
- usar validação de schema para saídas de IA interna;
- não permitir que modelo host altere banco diretamente.

---

# 10. Painel de controle e experiência do usuário

## 10.1 Princípio visual

O dashboard deve combinar:

- visual premium;
- profundidade analítica;
- clareza executiva;
- densidade técnica quando necessário;
- navegação rápida;
- filtros avançados;
- rastreabilidade visível;
- indicadores de qualidade e segurança.

## 10.2 Aplicação do Design System GennomX

Usar os princípios do Design System GennomX identificados no projeto:

- visual sofisticado e limpo;
- fundo claro com superfícies bem definidas;
- slate institucional como cor base;
- rose/gold como acento premium;
- cards com bordas suaves;
- sombras discretas;
- raios arredondados;
- tipografia display em Montserrat;
- tipografia de corpo em Inter;
- tabelas refinadas;
- hierarquia visual clara;
- áreas analíticas sem poluição visual.

## 10.3 Áreas do dashboard

### Visão geral

- total de ativos;
- total de empresas;
- total de trials;
- fontes ativas;
- últimas ingestões;
- alertas de qualidade;
- alertas de segurança;
- falhas de testes.

### Busca global

- busca por ativo;
- empresa;
- indicação;
- target;
- trial;
- publicação;
- aprovação;
- documento.

### Página de ativo terapêutico

- resumo estruturado;
- aliases;
- modalidade;
- mecanismo;
- targets;
- indicações;
- trials;
- endpoints;
- resultados;
- safety;
- status regulatório;
- evidências;
- histórico de atualização.

### Página de empresa

- pipeline;
- ativos;
- áreas terapêuticas;
- trials;
- press releases;
- investor decks;
- eventos recentes.

### Página de ensaio clínico

- metadados;
- desenho;
- braços;
- endpoints;
- status;
- resultados;
- publicações;
- abstracts;
- evidências.

### Página de indicação

- ativos relacionados;
- empresas;
- targets;
- ensaios;
- status por fase;
- eventos recentes.

### Página de target

- biologia resumida;
- indicações associadas;
- ativos;
- empresas;
- evidências Open Targets;
- publicações.

### Bundles de dados para relatórios externos

- criação de pacote estruturado;
- seleção de entidades;
- profundidade de evidência;
- exportação para modelo host;
- logs de uso.

### Monitoramento de fontes

- status de conector;
- última execução;
- próxima execução;
- falhas;
- volume;
- mudança de schema;
- compliance/licença.

### Logs de ingestão

- job;
- fonte;
- status;
- registros;
- erros;
- testes associados;
- reprocessamento.

### Logs MCP

- ferramenta;
- cliente;
- argumentos;
- entidades acessadas;
- latência;
- status;
- alertas.

### Segurança operacional

- tokens ativos;
- tentativas falhas;
- eventos anômalos;
- consultas volumosas;
- alertas de rate limit;
- status de secrets;
- recomendações de hardening.

### Testes automáticos

- última execução de CI;
- testes unitários;
- integração;
- e2e;
- data quality;
- segurança;
- conectores;
- cobertura;
- falhas recentes.

### Admin

- usuários;
- fontes;
- conectores;
- tokens;
- jobs;
- permissões futuras;
- configurações.

## 10.4 Modo claro e escuro

O MVP pode priorizar modo claro, seguindo o Design System. Modo escuro pode ser planejado para fase posterior, especialmente para usuários analíticos que utilizam dashboards por longos períodos.

---

# 11. Relatórios e análises como consumo externo via modelos host

A GennomX AI não deve gerar relatórios finais como função principal. Em vez disso, deve fornecer **dados estruturados e evidências** para que modelos host gerem os relatórios.

## 11.1 Tipos de bundles prioritários

### Competitive landscape data bundle

Objetivo:

- fornecer panorama estruturado de ativos, empresas, fases, targets, endpoints e evidências em uma indicação ou área terapêutica.

Dados necessários:

- DrugAsset;
- Company;
- ClinicalTrial;
- Indication;
- Target;
- Endpoint;
- TrialResult;
- RegulatoryApproval;
- Publication;
- ConferenceAbstract.

### Asset profile data bundle

Objetivo:

- fornecer dados completos sobre um ativo terapêutico.

Dados necessários:

- mecanismo;
- target;
- indicações;
- sponsor;
- trials;
- endpoints;
- resultados;
- safety;
- status regulatório;
- publicações;
- evidências.

### Company pipeline data bundle

Objetivo:

- estruturar pipeline de uma empresa.

Dados necessários:

- ativos;
- fases;
- indicações;
- modalidades;
- trials;
- eventos recentes;
- fontes corporativas.

### Clinical trial benchmark data bundle

Objetivo:

- comparar desenho, endpoints e resultados de trials relacionados.

Dados necessários:

- trials;
- critérios;
- endpoints;
- braços;
- população;
- resultados;
- comparadores;
- evidências.

### Regulatory history data bundle

Objetivo:

- organizar histórico regulatório por ativo, indicação e região.

Dados necessários:

- agência;
- status;
- aprovações;
- labels;
- documentos;
- datas;
- evidências.

### Safety overview data bundle

Objetivo:

- estruturar dados de segurança por ativo.

Dados necessários:

- eventos adversos;
- incidência;
- gravidade;
- trials;
- FAERS/openFDA;
- labels;
- evidências.

### Target landscape data bundle

Objetivo:

- estruturar evidências sobre target, ativos, indicações e empresas.

Dados necessários:

- Open Targets;
- publicações;
- ativos;
- mecanismos;
- trials;
- evidências.

### Weekly intelligence briefing data bundle

Objetivo:

- fornecer atualização estruturada para relatório periódico externo.

Dados necessários:

- novas publicações;
- novos trials;
- mudanças de status;
- novos resultados;
- aprovações;
- congressos;
- press releases.

## 11.2 Formato dos bundles

Cada bundle deve incluir:

- escopo;
- timestamp;
- filtros usados;
- entidades incluídas;
- tabelas estruturadas;
- evidências;
- fontes;
- limitações;
- lacunas;
- conflitos;
- qualidade dos dados;
- sugestão de uso por modelo host.

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

# 14. Estratégia de testes automáticos

## 14.1 Princípio geral

A GennomX AI deve ser construída com uma estratégia de testes automáticos desde o MVP. O objetivo é reduzir risco de:

- quebra de conectores;
- ingestão incorreta;
- dados duplicados;
- resultados clínicos mal extraídos;
- vazamento de dados;
- falhas de permissões;
- regressões no dashboard;
- ferramentas MCP retornando dados errados;
- deploys instáveis.

## 14.2 Pirâmide de testes recomendada

### Base: testes unitários

Cobrem:

- parsers;
- normalizadores;
- deduplicadores;
- validadores;
- formatadores;
- funções de score;
- builders de resposta MCP;
- validação de argumentos;
- regras de segurança.

### Meio: testes de integração

Cobrem:

- conector + raw storage;
- parser + banco;
- API + banco;
- MCP + API/banco;
- auth + permissões;
- jobs + logs;
- upload + quarentena + parsing.

### Meio: testes de contrato

Cobrem:

- schemas de APIs externas;
- schemas internos da API;
- contratos MCP;
- payloads de fontes;
- estrutura de bundles.

### Topo: testes end-to-end

Cobrem fluxos completos:

- usuário faz login;
- pesquisa ativo;
- abre página de ativo;
- visualiza trials;
- consulta evidência;
- executa bundle;
- verifica logs;
- edita dado incorreto;
- reprocessa entidade.

## 14.3 Testes por módulo

### Conectores

- teste de autenticação da fonte;
- teste de endpoint disponível;
- teste de paginação;
- teste de payload mínimo;
- teste de schema esperado;
- teste de timeout;
- teste de retry;
- teste de idempotência;
- teste de transformação.

### Scrapers

- teste de robots/allowlist;
- teste de bloqueio de domínio não aprovado;
- teste de HTML inesperado;
- teste de parser com fixture;
- teste de rate limit;
- teste de redirecionamento;
- teste de bloqueio de arquivo excessivo;
- teste de sanitização.

### Uploads

- teste de tipo de arquivo;
- teste de tamanho máximo;
- teste de arquivo corrompido;
- teste de nome malicioso;
- teste de macro/arquivo arriscado;
- teste de quarentena;
- teste de hash.

### Normalização

- teste de fase clínica;
- teste de status;
- teste de aliases;
- teste de unidades;
- teste de datas;
- teste de nomes de empresas;
- teste de indicações.

### Deduplicação

- teste de match exato;
- teste de match por ID externo;
- teste de match fuzzy;
- teste de falso positivo;
- teste de falso negativo;
- teste de rollback de merge.

### MCP

- teste de cada ferramenta;
- teste de input inválido;
- teste de limite de resultados;
- teste de autorização;
- teste de token inválido;
- teste de rate limit;
- teste de paginação;
- teste de evidências retornadas;
- teste de ausência de dado;
- teste de logs;
- teste de bloqueio de consulta ampla;
- teste de resposta em schema esperado.

### API

- teste de autenticação;
- teste de autorização;
- teste de paginação;
- teste de validação de payload;
- teste de erros seguros;
- teste de CORS;
- teste de rate limit;
- teste de OpenAPI/contrato.

### Dashboard

- teste de login;
- teste de busca;
- teste de páginas de entidade;
- teste de filtros;
- teste de tabelas;
- teste de edição corretiva;
- teste de logs;
- teste de responsividade;
- teste de estados vazios;
- teste de erro.

## 14.4 Testes de qualidade de dados

Devem validar:

- campos obrigatórios;
- unicidade de IDs;
- integridade referencial;
- formatos de data;
- ranges plausíveis;
- fases permitidas;
- status permitidos;
- endpoints sem resultado;
- resultados sem evidência;
- evidência sem documento;
- trials sem sponsor;
- ativos sem alias principal;
- entidades duplicadas;
- queda abrupta de volume por fonte;
- aumento anômalo de registros rejeitados.

## 14.5 Testes de segurança

Automatizar:

- SAST;
- dependency scanning;
- secret scanning;
- IaC scanning;
- container scanning;
- testes de headers;
- testes básicos de DAST;
- testes de autorização negativa;
- testes de RLS;
- testes de rate limit;
- testes contra payloads de XSS;
- testes contra SQL injection;
- testes contra SSRF em scrapers;
- testes de upload malicioso;
- testes de exposição de stack trace.

## 14.6 Testes de regressão de conectores

Cada conector deve ter fixtures versionadas com payloads reais ou representativos.

Quando uma fonte externa mudar:

- teste de contrato deve falhar;
- alerta deve ser gerado;
- ingestão deve ser pausada ou marcada como degraded;
- dados antigos devem permanecer disponíveis;
- correção deve ser validada com fixture nova.

## 14.7 Testes de performance

Validar:

- tempo de busca global;
- tempo de página de ativo;
- tempo de ferramentas MCP;
- ingestão por lote;
- consulta com filtros;
- geração de bundles;
- latência de API;
- tempo de indexação;
- comportamento sob concorrência.

Critérios iniciais sugeridos:

- busca global simples abaixo de 2 segundos no MVP;
- ferramenta MCP comum abaixo de 5 segundos para consultas limitadas;
- página de ativo abaixo de 3 segundos para ativos moderados;
- jobs longos assíncronos com progresso/logs;
- nenhuma ferramenta MCP sem limite.

## 14.8 Testes de aceitação

Antes de considerar o MVP funcional:

- carregar ao menos um conjunto representativo por fonte prioritária;
- buscar ativos por nome, indicação e target;
- abrir página de ativo com trials e evidências;
- consultar MCP com ferramenta `search_drugs`;
- consultar MCP com ferramenta `find_trials`;
- gerar bundle externo de asset profile;
- visualizar logs;
- corrigir um dado manualmente;
- verificar versionamento;
- recuperar evidência de um resultado;
- passar testes críticos de segurança.

## 14.9 Ferramentas sugeridas para testes

Recomendação inicial:

- pytest para backend Python;
- Playwright para end-to-end web;
- Schemathesis ou equivalente para testes OpenAPI;
- Great Expectations, Soda ou dbt tests para qualidade de dados;
- Ruff/mypy ou equivalentes para qualidade estática Python;
- Bandit/Semgrep para SAST;
- Trivy ou equivalente para containers/dependências;
- GitHub Actions ou GitLab CI para CI/CD;
- Supabase local/staging para testes de banco;
- fixtures versionadas para conectores.

A escolha final pode variar conforme stack definitiva.

---

# 15. CI/CD, ambientes e gates de release

## 15.1 Ambientes

Recomenda-se:

- **local**: desenvolvimento;
- **test**: execução automática de testes;
- **staging**: ambiente semelhante ao production;
- **production**: ambiente estável;
- **sandbox MCP**: ambiente para testes de ferramentas por modelos host.

## 15.2 Gates mínimos antes de deploy

Nenhum deploy para produção deve ocorrer se falharem:

- testes unitários críticos;
- testes de integração essenciais;
- testes MCP essenciais;
- testes de migração de banco;
- secret scanning;
- dependency scanning crítico;
- lint/type checks mínimos;
- build do frontend;
- testes end-to-end essenciais;
- testes de segurança de autorização.

## 15.3 Estratégia de migração

- migrações versionadas;
- rollback planejado;
- backup antes de migração crítica;
- testes de migração em staging;
- validação de dados após migração;
- não apagar colunas críticas sem fase de depreciação.

## 15.4 Estratégia de releases

MVP interno:

- releases frequentes;
- changelog simples;
- validação manual final;
- monitoramento pós-deploy.

Futuro comercial:

- versionamento semântico;
- release notes;
- feature flags;
- canary deploy;
- rollback automático;
- SLAs internos.

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

# 17. Observabilidade e manutenção

## 17.1 Monitoramento de jobs

Métricas:

- jobs executados;
- jobs com sucesso;
- jobs com falha;
- duração;
- registros coletados;
- registros rejeitados;
- deltas por fonte;
- erros por tipo;
- última execução bem-sucedida.

## 17.2 APIs externas

Monitorar:

- disponibilidade;
- latência;
- erros HTTP;
- mudanças de schema;
- rate limit;
- mudanças de autenticação;
- queda de volume.

## 17.3 Scrapers

Monitorar:

- falha de parsing;
- alteração de layout;
- bloqueio de acesso;
- aumento de redirects;
- aumento de captchas;
- mudanças em robots/termos;
- aumento de rejeições.

## 17.4 MCP

Monitorar:

- chamadas por ferramenta;
- latência;
- erros;
- consultas sem resultado;
- volume por cliente;
- tokens mais usados;
- tentativas não autorizadas;
- consultas amplas;
- custo indireto.

## 17.5 Custos de IA

Monitorar:

- chamadas de extração;
- tokens consumidos;
- custo por fonte;
- custo por documento;
- taxa de erro;
- custo por entidade enriquecida;
- modelos utilizados.

## 17.6 Qualidade dos dados

Monitorar:

- completude;
- duplicidade;
- conflitos;
- evidência ausente;
- campos obrigatórios vazios;
- freshness;
- entidades órfãs;
- confidence score médio;
- campos editados manualmente.

## 17.7 Segurança

Monitorar:

- falhas de login;
- tokens expirados ou abusados;
- chamadas bloqueadas;
- rate limits acionados;
- uploads rejeitados;
- alertas de SAST/dependency scanning;
- segredos expostos;
- alterações administrativas;
- eventos MCP anômalos.

## 17.8 Alertas recomendados

- fonte crítica sem atualização por mais de X dias;
- queda abrupta de registros;
- aumento abrupto de registros;
- falha repetida em conector;
- mudança de schema;
- teste de segurança falhou;
- token MCP com uso anômalo;
- consulta MCP muito ampla;
- erro 5xx recorrente;
- backup falhou;
- parsing de PDF com erro alto;
- custo de IA acima do limite.

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
- criar testes de conectores.

Fontes:

- ClinicalTrials.gov;
- PubMed/PMC;
- openFDA;
- DailyMed;
- EMA;
- Open Targets;
- ANVISA inicial.

Entregáveis:

- banco Supabase/PostgreSQL;
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
- sandbox MCP.

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

- conectores ASCO/ESMO/AACR/ASH quando viável;
- parsers PDF;
- extração de tabelas;
- extração de endpoints;
- sandbox de arquivos;
- testes de regressão com fixtures.

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
- criar sandbox.

## 19.6 Infraestrutura

- definir Supabase cloud vs self-host;
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

## 20.1 Supabase Cloud vs self-host em VPS

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

Recomendação inicial:

- **Supabase Cloud para MVP**, pela velocidade e menor carga operacional.

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
16. Supabase é preferência inicial, sujeita a validação técnica.
17. Atualização dos dados deve ser diária quando a fonte permitir.
18. Scraping deve ser agressivo quando necessário, mas com salvaguardas legais e técnicas.

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

1. Banco Supabase/PostgreSQL com entidades centrais.
2. Raw storage com versionamento e hash.
3. Conectores para ClinicalTrials.gov, PubMed/PMC, openFDA, DailyMed, EMA, Open Targets e ANVISA inicial.
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

# 24. Referências técnicas recomendadas

Estas referências não substituem requisitos próprios da GennomX AI, mas devem orientar as decisões de segurança e testes:

1. OWASP Application Security Verification Standard — referência para requisitos de segurança de aplicações.
2. OWASP API Security Top 10 — referência para riscos em APIs e, por extensão, ferramentas MCP expostas como interface programática.
3. OWASP Web Security Testing Guide — referência para testes de segurança em aplicações web e serviços.
4. Supabase Row Level Security — referência para autorização granular no PostgreSQL/Supabase.
5. Playwright — referência para testes end-to-end no dashboard web.

