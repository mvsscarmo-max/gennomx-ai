<!-- validate-links: illustrative-paths -->
# 02 — Modelo de Dados Conceitual

## Implementação operacional da matriz — migração 0004

> Estado vigente em 2026-07-20: paths de raw, processed e evidence apontam para MinIO/S3-compatible. Cloudflare R2 é destino futuro, sem provisionamento nesta fase.

- `field_assertions` recebeu classe, tipo de fonte, prioridade, maturidade, novidade, impacto
  clínico, validação, expiração e arquivamento, com checks e índice de expiração;
- `data_policy.py` torna granularidade/freshness obrigatórias e falha fechado para campo sem
  política; resultados usam trial+braço+população+timepoint+medida, eventos adversos incluem
  termo/grau e decisões regulatórias incluem produto+indicação+região;
- endpoints, resultados, eventos adversos, aprovações e publicações receberam validade, tempo de
  sistema, `is_current` e lifecycle; índices únicos parciais impedem duas projeções correntes na
  mesma granularidade;
- tabelas próprias controlam retenção, legal hold, manifestos, itens arquivados, domínios de
  scraping e eventos de acesso.

## Governança temporal e estado canônico — ADR-001

O banco operacional mantém o estado canônico corrente; ele não é o repositório bruto nem o
histórico completo. A decisão normativa está em `architecture/ADR_001_temporalidade_precedencia.md`.

### Camadas lógicas

| Camada | Conteúdo | Regra |
|---|---|---|
| raw | payload original no object storage | imutável, hash e timestamp |
| assertions | afirmação por entidade/campo/fonte/validade | append-only; bitemporal |
| current | tabelas canônicas e relações `is_current` | somente vencedor determinístico |
| history/audit | versões, conflitos e correções | fora do caminho quente |

`field_assertions` diferencia `valid_from/valid_to` (tempo do fato) de
`system_from/system_to` (tempo de conhecimento), referencia a assertion substituída e guarda
versões do extrator, normalizador e regras. `data_conflicts` preserva divergências abertas;
`manual_corrections` registra proposta, motivo, evidência, revisão e assertion resultante. Edição
factual direta e destrutiva permanece proibida.

### Matriz de granularidade, autoridade e freshness

| Tipo | Unidade canônica | Autoridade primária | Revalidar após |
|---|---|---|---|
| trial em andamento | registro oficial + campo temporal | registro oficial | 7–14 dias |
| trial terminal | registro oficial + campo temporal | registro oficial | 90–180 dias |
| sponsor/ownership | relação com validade | registro/regulador; contrato oficial | 30 dias |
| aprovação regulatória | evento por produto/indicação/região | agência regulatória | diária/semanal |
| publicação | DOI/PMID/PMCID | publisher/PubMed | por errata/retração |
| endpoint/resultado | trial+braço+população+timepoint+medida | registro/publicação primária | não expira; pode ser substituído |
| adverse event | trial+braço+termo+grau+população | resultado/label oficial | não expira; pode ser substituído |
| pipeline corporativo | ativo+indicação+empresa+validade | empresa, secundária à fonte regulatória | 30–90 dias |
| ontologia/target | identificador + release | base oficial versionada | a cada release |

`stale` significa “requer revalidação”, não “falso”. Relevância nunca substitui autoridade ou
evidência. Scores (`authority`, `confidence`, `relevance`, `freshness`, `completeness`) permanecem
separados; não existe score único opaco.

### Ciclo de vida

`candidate → validated → active → disputed → superseded → archived`, com saídas adicionais
`rejected` e `quarantine`. Apenas `active` e `is_current=true` alimentam o canônico/MCP por padrão.

Relações trial↔ativo passam a possuir validade e tempo de sistema. Arrays legados permanecem
apenas como cache compatível até migração completa das demais relações.

## Camada de inteligência emergente — campos de scoring (2026-06-20)

Para sustentar o posicionamento de inteligência emergente (`docs/00` §14) sem misturar evidência
consolidada com preliminar, cada assertion/entidade relevante ganha campos de classificação,
**separados e não opacos** (somam-se a `authority`, `confidence`, `relevance`, `freshness`,
`completeness`):

| Campo | Tipo | Significado |
|---|---|---|
| `evidence_maturity` | enum | Nível de maturidade científica (8 tiers, ver `docs/03` §7A) |
| `novelty_score` | 0–1 | Quão nova é a informação (1ª aparição vs. recorrência) |
| `clinical_impact_score` | 0–1 | Impacto clínico potencial estimado |
| `validation_status` | enum | `unvalidated` → `preliminary` → `corroborated` → `confirmed` |

Regras:

- `confidence_score` (já existente) **não** é substituído; os novos campos o complementam.
- Checks de range 0–1 seguem o padrão da migração `0002` (scores fora de 0–1 falham).
- `evidence_maturity` rege, junto com a autoridade da fonte, a precedência no
  `PersistenceDecisionEngine`: itens `preprint`/`conference_abstract` não superseder evidência
  `peer_reviewed_primary`/`regulatory_action`.
- Implementação de migração/colunas reais é trabalho de código posterior; esta seção documenta o
  contrato conceitual.

## Integridade relacional — correção fase 4 (2026-06-20)

A migração `0002_integrity_rls.py` converte referências escalares legadas de `varchar` para UUID e
adiciona FKs entre fontes, documentos, evidências, trials, endpoints, resultados, ativos,
indicações, eventos adversos, decisões regulatórias e jobs. Exclusões usam `CASCADE` apenas para
filhos sem significado autônomo; referências históricas usam `SET NULL`.

`clinical_trial_assets` passa a ser a relação canônica trial↔ativo, com chave composta e FKs. O
array `clinical_trials.drug_asset_ids` permanece temporariamente como cache compatível e é
sincronizado pelo worker. Arrays de indicações/publicações devem migrar para tabelas associativas
quando esses conectores forem ativados.

Checks impedem scores fora de 0–1 e contadores negativos. A migração não apaga órfãos: UUID
inválido ou FK inconsistente faz o upgrade falhar para correção explícita.

## Rastreabilidade aplicada na correção 3 — 2026-06-20

- `SourceDocument.content_hash` identifica o JSON canônico recebido.
- `raw_storage_path` aponta para o objeto `.json.gz` endereçado por hash.
- `metadata` registra formato, bytes comprimidos, chaves de topo e versão do conector.
- `EvidenceSnippet.text_excerpt` contém JSON literal dos módulos oficiais de suporte.
- Evidências são idempotentes por documento, entidade e campo durante retries.
- Raw e dado normalizado permanecem separados para permitir reprocessamento auditável.

Este documento concentra a modelagem conceitual das entidades, seus campos, relacionamentos e requisitos de rastreabilidade.

---

## 5. Tipos de dados esperados

A GennomX AI deve lidar com dados em múltiplas camadas.

### 5.1 Entidades principais

- Drogas e ativos terapêuticos.
- Empresas.
- Indicações/doenças.
- Targets.
- Mecanismos de ação.
- Ensaios clínicos.
- Intervenções.
- Braços de estudo.
- Endpoints.
- Resultados.
- Eventos adversos.
- Status regulatórios.
- Aprovações.
- Publicações.
- Abstracts.
- Press releases.
- Investor decks.
- Documentos-fonte.
- Trechos de evidência.

### 5.2 Dados clínicos granulares

- NCT ID e outros identificadores.
- Fase.
- Status do estudo.
- Sponsor e collaborators.
- Indicação.
- População.
- Critérios de inclusão/exclusão.
- Intervenções.
- Comparator.
- Dose/regime.
- Endpoint primário.
- Endpoints secundários.
- Resultado por endpoint.
- Tempo de follow-up.
- N analisado.
- Hazard ratio, odds ratio, confidence interval, p-value quando disponível.
- Eventos adversos por grau.
- Eventos adversos graves.
- Discontinuações.
- Mortalidade.
- Fonte do resultado.

### 5.3 Dados regulatórios

- Agência.
- Região.
- Produto.
- Status.
- Data de aprovação.
- Indicação aprovada.
- Tipo de pathway.
- Designações especiais.
- Label/bula.
- Documento regulatório associado.
- Histórico de mudanças.

### 5.4 Dados competitivos e de mercado

- Pipeline por empresa.
- Landscape por indicação.
- Competidores por target.
- Catalysts clínicos/regulatórios.
- Press releases relevantes.
- Deals e parcerias quando disponíveis em fontes públicas.
- Eventos corporativos.
- Dados de mercado e comercialização apenas quando públicos/licenciados.

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
- DrugAsset pode aparecer em múltiplos ClinicalTrial; no MVP atual, `clinical_trials.drug_asset_ids` é preenchido inicialmente a partir das intervenções terapêuticas do ClinicalTrials.gov e sustentado por `EvidenceSnippet`.
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
