# 03 — Fontes, Conectores e Ingestão

## Pipeline executável consolidado — 2026-06-21

- páginas com NCT repetido passam pelo staging DuckDB e preservam somente a versão mais nova antes
  de qualquer escrita canônica;
- campos críticos CT.gov usam `registry=clinicaltrials.gov`, evidência por campo, expiração de
  14–180 dias e metadados de fonte/maturidade/prioridade;
- versão atrasada é arquivada sem regredir o canônico; equivalente é NOOP; divergência abre
  conflito; complemento parcial só aceita objeto/lista e nunca apaga valor existente;
- `ControlledScraper` exige policy ativa, robots aprovado, HTTPS/host allowlist, IP público,
  redirects limitados, rate/concorrência distribuídos, `Retry-After`, kill switch, limite de bytes,
  sanitização HTML e log por URL hash. Nenhum domínio é habilitado por padrão.

## Remediação de persistência — revisão externa de 2026-06-21

- `SourceDocument` retorna obrigatoriamente seu ID também no caminho de INSERT.
- Evidência por campo só é criada depois de existir `trial_id`.
- Se todos os registros parseados de uma página falharem na persistência, o job falha e é
  reexecutado; não pode terminar verde com zero inserções por erro sistêmico.
- `record_limit_reached` representa paginação incompleta esperada: não é falha fatal nem provoca
  retry do mesmo lote.
- Documentos são deduplicados por fonte + ID externo + hash, preservando proveniência de payloads
  iguais associados a registros diferentes.
- Relações trial↔ativo encerradas são copiadas para `clinical_trial_asset_history` antes da troca da
  projeção corrente.
- Deduplicação de ativos aceita somente identidade exata (INN/cross-ID) como candidato e abre
  conflito auditável; merge fuzzy automático permanece proibido.

## Política normativa de decisão pré-persistência — 2026-06-20

Todo conector passa por: raw imutável → parser → schema → normalização → staging/DuckDB → quality
gates → resolução de identidade → `PersistenceDecisionEngine` → assertions → projeção canônica.

| Ação | Critério objetivo |
|---|---|
| `insert` | identidade nova, schema/evidência válidos |
| `replace` | versão efetiva mais nova ou fonte materialmente mais autoritativa |
| `enrich` | complemento não contraditório e não destrutivo |
| `noop` | mesmo fingerprint canônico |
| `reject` | inválido, fora do escopo ou sem identidade obrigatória |
| `supersede` | novo vencedor encerra validade da assertion anterior |
| `archive` | versão atrasada/correta, mas não corrente |
| `conflict` | fontes confiáveis divergem sem precedência conclusiva |
| `quarantine` | fato crítico sem evidência ou confiança insuficiente |

Recência de coleta não equivale a recência do fato. A comparação usa `source_updated_at`; payload
fora de ordem é preservado no raw, mas não pode regredir o canônico. Campo omitido em payload
parcial não apaga valor conhecido. Toda decisão registra `reason_code` e `rule_set_version`.

No ClinicalTrials.gov, `nct_id` continua sendo a chave natural; status, fase, enrollment e sponsor
ganham assertions e evidências por campo. Relações trial↔ativo são encerradas temporalmente em vez
de apagadas. `current_development_stage`, `max_historical_stage` e `development_status` deixam de
tratar “maior fase já observada” como sinônimo de estado atual.

## Política formal de scraping e compliance

Scraping só é autorizado quando API, export ou upload controlado não atendem. Cada domínio exige
registro de owner, finalidade, base legal/licença, termos avaliados, limites, allowlist, kill switch
e retenção. O comportamento normativo é:

- respeitar termos de uso, controles de acesso e robots.txt aplicável;
- não contornar captcha, autenticação, paywall ou bloqueio técnico;
- não usar proxies residenciais/rotação de identidade para evasão;
- aplicar rate limit conservador, backoff com jitter e `Retry-After`;
- bloquear IPs privados, metadata endpoints e redirecionamentos fora da allowlist;
- executar HTML/PDF em sandbox sem scripts remotos;
- preservar URL, hash, timestamp, versão do scraper e licença;
- suspender automaticamente em 401/403/429 persistente, mudança de termos ou incidente.

Qualquer orientação anterior sobre ignorar robots.txt, resolver captcha ou contornar bloqueios fica
revogada por esta política. Exceção exige aprovação jurídica/documentada e implementação específica,
nunca um comportamento genérico do conector.

## Correção técnica CT.gov — 2026-06-20

O incremental usa `data_sources.last_successful_run` como cursor e recua
`CLINICALTRIALS_INCREMENTAL_LOOKBACK_DAYS` para absorver alterações na borda temporal. Cada página
é persistida antes da próxima requisição. Se `CLINICALTRIALS_MAX_RECORDS_PER_RUN` for atingido com
páginas pendentes, o job recebe `record_limit_reached` e não avança o cursor.

Cada estudo usa savepoint; falhas sistêmicas de fetch/storage acionam retry Celery. O JSON bruto
canônico é comprimido e salvo no storage S3-compatible ativo (MinIO no runtime atual) por
fonte/data/NCT/hash. Caminho, hash, tamanho, timestamp e versão ficam em `SourceDocument`.
Evidências são fragmentos JSON literais da resposta oficial.

Antes de qualquer escrita, um `dry_run=true` percorre connector, parser e normalizer, registra um
`IngestionJob` auditável com contagens em `metadata`, mas não grava raw, `SourceDocument`,
`EvidenceSnippet`, assertions, entidades canônicas ou cursor. Uma fonte desabilitada só pode ser
executada nesse modo por rota administrativa; execuções reais e o Beat respeitam
`data_sources.is_enabled`.

Este documento reúne as fontes prioritárias, regras de ingestão, pipelines, scraping, uploads e critérios de priorização.

> **VLAEG:** este documento materializa o Princípio 3.1 (Dados primeiro / contrato de dados) e a fase **L — Link** (validação de conectividade). Ver `docs/13_PROTOCOLO_VLAEG.md`.

---

# 0. Contratos de dados por conector (VLAEG 3.1)

Todo conector deve declarar seu contrato `{input, processamento, output}` antes de evoluir a lógica. O contrato é a fonte da verdade do que entra, como é processado e o que é persistido.

## 0.1 Modelo de contrato (preencher por conector)

```json
{
  "input": {
    "fonte": "<slug da DataSource>",
    "metodo": "api | export | upload | mcp_externo | scraping",
    "endpoint": "<URL/base ou caminho>",
    "campos_obrigatorios": [],
    "campos_opcionais": [],
    "formato": "json | csv | xml | pdf | html"
  },
  "processamento": {
    "regras": ["parsing", "normalização", "deduplicação", "evidência", "confidence"],
    "validacoes": ["schema", "campos obrigatórios", "idempotência"],
    "transformacoes": ["fase", "status", "datas", "aliases"]
  },
  "output": {
    "destino": "<tabelas canônicas + evidências + IngestionJob>",
    "formato": "entidades PostgreSQL + EvidenceSnippet + SourceDocument",
    "criterio_de_sucesso": "<condição objetiva>"
  }
}
```

## 0.2 Contrato — `clinicaltrials_gov` (implementado)

```json
{
  "input": {
    "fonte": "clinicaltrials_gov",
    "metodo": "api",
    "endpoint": "https://clinicaltrials.gov/api/v2/studies",
    "campos_obrigatorios": ["protocolSection.identificationModule.nctId"],
    "campos_opcionais": ["phase", "overallStatus", "interventions", "sponsor", "conditions", "protocolSection.outcomesModule", "resultsSection.outcomeMeasuresModule", "resultsSection.adverseEventsModule"],
    "formato": "json"
  },
  "processamento": {
    "regras": ["paginação", "retry/backoff", "parsing protocolSection/resultsSection", "normalização fase/status", "linking DrugAsset", "evidência literal"],
    "validacoes": ["NCT ID presente", "idempotência por NCT ID", "JSON de erro/metadados válido"],
    "transformacoes": ["PHASE_MAP", "STATUS_MAP", "extract_drug_names", "datas"]
  },
  "output": {
    "destino": "clinical_trials, drug_assets, endpoints, trial_results, adverse_events, source_documents, evidence_snippets, ingestion_jobs",
    "formato": "entidades PostgreSQL + EvidenceSnippet + SourceDocument",
    "criterio_de_sucesso": "trials upsertados com NCT ID único, SourceDocument e EvidenceSnippet vinculados, IngestionJob registrado com data_source_id"
  }
}
```

> Conectores futuros (ANVISA) devem declarar seu contrato nesta seção **antes** da implementação, seguindo o modelo 0.1.

## 0.2B Contrato — `pubmed` (implementado)

```json
{
  "input": {
    "fonte": "pubmed",
    "metodo": "api",
    "endpoint": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
    "campos_obrigatorios": ["PMID"],
    "campos_opcionais": ["DOI", "PMCID", "title", "abstract", "journal", "authors", "keywords", "NCT"],
    "formato": "xml"
  },
  "processamento": {
    "regras": ["ESearch com usehistory", "paginação EFetch via WebEnv+query_key", "parsing XML PubMed", "extração DataBank NCT", "dedup por PMID/DOI", "evidência"],
    "validacoes": ["PMID e title obrigatórios", "idempotência por PMID", "publication_type controlado"],
    "transformacoes": ["abstract estruturado", "datas parciais", "NCT linking contra clinical_trials"]
  },
  "output": {
    "destino": "publications, source_documents, evidence_snippets, ingestion_jobs",
    "formato": "entidades PostgreSQL + EvidenceSnippet + SourceDocument",
    "criterio_de_sucesso": "publications upsertadas com PMID único, SourceDocument e EvidenceSnippet vinculados, linked_trial_ids populado, IngestionJob registrado"
  }
}
```

## 0.2C Contrato — `openfda` (implementado)

```json
{
  "input": {
    "fonte": "openfda",
    "metodo": "api",
    "endpoint": "https://api.fda.gov/drug/drugsfda.json",
    "campos_obrigatorios": ["application_number", "products[].brand_name|active_ingredients"],
    "campos_opcionais": ["submissions[]", "openfda.generic_name", "openfda.brand_name"],
    "formato": "json"
  },
  "processamento": {
    "regras": ["paginação skip/limit", "retry/backoff", "resolução da submission mais recente", "match por nome contra drug_assets"],
    "validacoes": ["asset_name e agency obrigatórios (quality gate)", "idempotência por application_number"],
    "transformacoes": ["SUBMISSION_STATUS_MAP (AP/TA/AN/WD)", "review_priority → priority_review"]
  },
  "output": {
    "destino": "regulatory_approvals, source_documents, evidence_snippets, ingestion_jobs",
    "formato": "entidades PostgreSQL + EvidenceSnippet + SourceDocument",
    "criterio_de_sucesso": "aprovações upsertadas com application_number único por (drug_asset, agency, region), evidência vinculada; registros sem drug_asset correspondente são pulados (records_skipped), não rejeitados"
  }
}
```

Limitação conhecida: `drugsfda.json` não expõe um filtro de delta confiável; execuções `incremental` são limitadas por `OPENFDA_MAX_RECORDS_PER_RUN` e dependem de upserts idempotentes (mesmo padrão adotado para DailyMed e EMA abaixo).

## 0.2D Contrato — `dailymed` (implementado)

```json
{
  "input": {
    "fonte": "dailymed",
    "metodo": "api",
    "endpoint": "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json",
    "campos_obrigatorios": ["setid", "title"],
    "campos_opcionais": ["published_date"],
    "formato": "json"
  },
  "processamento": {
    "regras": ["paginação page/pagesize", "parsing heurístico do título SPL", "match por nome contra drug_assets"],
    "validacoes": ["asset_name e agency obrigatórios (quality gate)", "idempotência por setid"],
    "transformacoes": ["extração de nome do medicamento a partir do título", "aliases a partir do texto após o separador"]
  },
  "output": {
    "destino": "regulatory_approvals (label_url, agency=FDA), source_documents, evidence_snippets, ingestion_jobs",
    "formato": "entidades PostgreSQL + EvidenceSnippet + SourceDocument",
    "criterio_de_sucesso": "label mais recente por (drug_asset, FDA, US) upsertada com label_url e evidência vinculada; sem application_number (SPL não expõe), chave corrente é por asset+agência+região"
  }
}
```

## 0.2E Contrato — `open_targets` (implementado)

```json
{
  "input": {
    "fonte": "open_targets",
    "metodo": "api (GraphQL)",
    "endpoint": "https://api.platform.opentargets.org/api/v4/graphql",
    "campos_obrigatorios": ["target.id", "target.approvedSymbol"],
    "campos_opcionais": ["target.synonyms", "target.proteinIds", "associatedTargets.score"],
    "formato": "json (graphql)"
  },
  "processamento": {
    "regras": ["busca de doença por termo semente (OPEN_TARGETS_SEED_DISEASE_TERMS)", "query associatedTargets por efoId", "resolução de indication_id por nome"],
    "validacoes": ["symbol obrigatório (quality gate)", "idempotência por symbol", "score entre 0 e 1"],
    "transformacoes": ["biotype → target_type (protein_coding→protein)", "synonyms → aliases", "uniprot_swissprot → external_ids.uniprot"]
  },
  "output": {
    "destino": "targets, source_documents, evidence_snippets, ingestion_jobs",
    "formato": "entidades PostgreSQL + EvidenceSnippet + SourceDocument",
    "criterio_de_sucesso": "targets upsertados por symbol único, aliases/indicações mescladas (não sobrescritas) em atualizações, evidência vinculada"
  }
}
```

Limitação conhecida: descoberta é guiada por uma lista semente de termos de doença configurável (não é um crawl completo do grafo Open Targets); ampliar a lista ou usar EFO IDs de `indications.ontology_ids` quando essa coluna estiver populada por outros conectores.

## 0.2F Contrato — `ema` (implementado)

```json
{
  "input": {
    "fonte": "ema",
    "metodo": "export oficial (XLSX)",
    "endpoint": "EMA_MEDICINES_EXPORT_URL (documento oficial 'Medicines output')",
    "campos_obrigatorios": ["Medicine name"],
    "campos_opcionais": ["INN", "Active substance", "Authorisation status", "Marketing authorisation date", "Product number", "Orphan medicine", "URL"],
    "formato": "xlsx"
  },
  "processamento": {
    "regras": ["download com limite de tamanho (100MB)", "parsing via openpyxl com resolução de colunas por substring normalizada", "match por nome contra drug_assets"],
    "validacoes": ["asset_name e agency obrigatórios (quality gate)", "idempotência por product_number", "limite de download (fail-closed acima do cap)"],
    "transformacoes": ["Authorised/Withdrawn/Refused/Suspended → approved/withdrawn/rejected/withdrawn", "Orphan medicine=Yes → special_designations=[orphan_drug]"]
  },
  "output": {
    "destino": "regulatory_approvals (agency=EMA, region=EU), source_documents, evidence_snippets, ingestion_jobs",
    "formato": "entidades PostgreSQL + EvidenceSnippet + SourceDocument",
    "criterio_de_sucesso": "registro upsertado por (drug_asset, EMA, EU, product_number), evidência vinculada"
  }
}
```

Classificação de ingestão (`AGENTS.md` §10): export oficial (tier 2, abaixo de API dedicada) — download de documento fixo publicado pela EMA, não scraping de HTML; portanto não está sujeito às salvaguardas de scraping agressivo (allowlist de domínio, robots.txt, kill switch), apenas ao limite de tamanho e timeout já implementados.

---

# 0B. Matriz Link — validação de conectividade (VLAEG fase L)

Antes de desenvolver/operar a lógica de um conector, sua conectividade deve ser validada por handshake (`tools/handshake.py`, que executa `BaseConnector.healthcheck()`). A matriz abaixo registra o estado das fontes.

| Fonte (slug) | Método | Handshake | Credencial | Status | Observação |
|---|---|---|---|---|---|
| `clinicaltrials_gov` | API v2 | `healthcheck()` ✅ | Não requer | Operacional | Leitura simples de 1 estudo + timeout |
| `pubmed` | API E-utilities | `healthcheck()` ✅ | API key opcional | Operacional | PubMed via ESearch/EFetch/ELink, dedup PMID/DOI |
| `pubmed_pmc` | API NCBI | Pendente | API key opcional | Inativo (legado) | Substituído por slug `pubmed`; PMC full-text pendente (ordem 3) |
| `openfda` | API (drugsfda) | `healthcheck()` ✅ | API key opcional | Operacional | Leitura de 1 registro + timeout; sem filtro de delta confiável |
| `dailymed` | API (spls.json) | `healthcheck()` ✅ | Não requer | Operacional | Leitura de 1 registro + timeout |
| `ema` | Export oficial (XLSX) | `healthcheck()` ✅ | Não requer | Operacional | HEAD/Range probe no documento oficial; parsing via openpyxl |
| `open_targets` | GraphQL | `healthcheck()` ✅ | Não requer | Operacional | Query `meta.apiVersion`; descoberta por termos-semente de doença |
| `anvisa` | API/export/scraping | Pendente | Não requer | Não implementado | Preparar healthcheck |

> **Regra VLAEG (fase L):** não desenvolver lógica final sobre integração não testada. Rodar `make handshake` (ou `python tools/handshake.py`) e atualizar esta matriz ao adicionar/alterar conectores.

---

## 4. Fontes de dados prioritárias

> **Fonte da verdade:** a lista completa de fontes candidatas e sua ordem vive em **`project_state/fontes_priorizacao.xlsx`**. O roadmap de novos conectores (`docs/08_ROADMAP.md`, `project_state/TASKS.md`) segue a coluna `Prioridade` e os bloqueios vigentes.

### 4.1 Fontes regulatórias

FDA/openFDA, DailyMed, EMA e ANVISA são as fontes regulatórias centrais do MVP; Health Canada DPD, TGA, HSA, MFDS, NMPA, PMDA, CDSCO e Israel MoH compõem a fase de expansão global. Ver planilha para URL, tipo de acesso e status de cada uma.

### 4.2 Fontes científicas

PubMed/MEDLINE, PubMed Central, bioRxiv e medRxiv via API; journals de alto impacto (NEJM, The Lancet, JAMA, BMJ, Nature Medicine, JCO, Annals of Oncology, etc.) ficam fora da planilha individual por ora — exigem avaliação de licença caso a caso. A Cochrane Library (revisões sistemáticas/metanálises) é candidata posterior (P3): é evidência **consolidada** — alto rigor, mas baixa aderência ao recorte "emergente" — e exige avaliação de acesso/licença.

### 4.3 Ensaios clínicos

ClinicalTrials.gov é a fonte global prioritária e já operacional. EU CTR/CTIS, ISRCTN e ReBEC (Brasil) estão mapeados na planilha como candidatos seguintes (P3) — complementam o CT.gov com menor valor marginal e dados mais ruidosos no MVP.

### 4.4 Drogas e targets

Open Targets é a fonte prioritária de target-disease associations (API GraphQL + downloads). DrugBank e bases pagas seguem fora do escopo inicial — listadas na planilha como bloqueadas por licença.

### 4.5 Congressos

ASCO, ESMO, AACR, ASH e demais (AHA, ADA, EASD, ESC, AAN, ATS) tendem a exigir scraping estruturado, parsing de HTML/PDF, monitoramento de termos de uso e controle de acesso por fonte — ver planilha.

### 4.6 Press releases e investor decks

Sites oficiais de empresas, investor relations e SEC/EDGAR (este com API pública). Ver planilha para detalhes por fonte.

### 4.7 Bases comerciais/licenciadas

Evaluate Pharma, Citeline/Trialtrove/Pharmaprojects, GlobalData Healthcare, IQVIA, Clarivate Cortellis e DrugBank licenciado **não serão integradas no MVP** por decisão do projeto — previstas apenas como conectores futuros bloqueados por licença (ver planilha, categoria `Comercial-licenciada`).

### 4.8 Fontes que exigem scraping

Congressos sem API pública, investor relations, press releases, PDFs regulatórios (EPARs, pareceres, bulas) e páginas de pipelines corporativos. O princípio operacional permanece: **usar API/export oficial sempre que existir; usar scraping apenas quando não houver alternativa estruturada e mantendo salvaguardas legais**.

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

## 6.8 Estado implementado em 2026-06-12 — ClinicalTrials.gov

O conector `clinicaltrials_gov` já executa:

- coleta pela API oficial ClinicalTrials.gov v2;
- paginação e retry com backoff;
- parsing para representação intermediária;
- normalização de fase, status e campos principais;
- upsert em `clinical_trials`;
- criação/reuso de `SourceDocument` por hash de payload;
- criação de `EvidenceSnippet` básico vinculado ao trial, contendo NCT ID, título, status, fase e sponsor;
- vínculo `clinical_trials.source_document_id` para rastreabilidade mínima;
- criação/atualização inicial de `DrugAsset` a partir de intervenções terapêuticas (`DRUG`, `BIOLOGICAL`, `GENETIC`);
- preenchimento de `clinical_trials.drug_asset_ids` durante a ingestão;
- criação de `EvidenceSnippet` vinculado ao `DrugAsset` indicando a intervenção do trial que sustenta o ativo;
- tarefa Celery `link_trials_to_assets` para backfill de trials já ingeridos sem vínculo com ativos;
- registro de `IngestionJob` com `data_source_id`, contadores de inserção, atualização, rejeição e erro em JSON válido.

Incremento DRY-7 por fixtures (2026-07-20):

- endpoints planejados de `protocolSection.outcomesModule` são projetados em `endpoints`;
- medidas postadas de `resultsSection.outcomeMeasuresModule` alimentam `endpoints` e
  `trial_results` por grupo, preservando valores negativos e inconclusivos no literal/raw;
- `resultsSection.adverseEventsModule` alimenta contagens sérias e não sérias quando presentes;
- projeções usam fingerprint, current/superseded e `source_evidence_id`; reexecução idêntica não
  duplica registros;
- trial sem resultados continua válido e é retornado pelo MCP com gaps, não como erro.

Limitações atuais:

- o incremento é deliberadamente limitado ao schema literal da fixture CT.gov; não infere eficácia;
- evidência granular cobre os três módulos implementados, não todos os campos clínicos;
- o linking atual usa correspondência exata case-insensitive por `primary_name`; deduplicação fuzzy, INN, cross-IDs e resolução de conflitos ainda dependem de processamento posterior;
- confidence scoring avançado ainda depende das tarefas de processamento posteriores.

---

## 6.8B Estado implementado em 2026-06-23 — PubMed

O conector `pubmed` executa:

- coleta via E-utilities NCBI (ESearch com history → EFetch paginado via WebEnv/query_key);
- parsing XML PubMed com ElementTree (stdlib) — PMID, DOI, PMCID, title, abstract estruturado, journal, authors, mesh keywords, NCT via DataBank;
- normalização com `publication_type` controlado (`article|preprint|review|abstract|letter`), `evidence_maturity=peer_reviewed_primary`, `registry_source=pubmed`;
- upsert em `publications` com `PersistenceDecisionEngine` chaveado por PMID;
- `SourceDocument` com `source_type=scientific_publication` e URL `https://pubmed.ncbi.nlm.nih.gov/<pmid>/`;
- `EvidenceSnippet` com entity_type `publication` e fragmento literal (title + abstract + journal + pmid + doi);
- linking NCT: extração de `<DataBankName>ClinicalTrials.gov</…><AccessionNumber>` do EFetch, resolvido contra `clinical_trials.nct_id`; NCTs não resolvidos registrados em `ingestion_metadata` para backfill;
- raw payload (XML+gzip) imutável no storage S3-compatible ativo;
- qualidade mínima: PMID obrigatório, title obrigatório;
- rate limit via `asyncio.sleep(1/PUBMED_RATE_LIMIT_REQUESTS_PER_SECOND)`, retry com `tenacity`;
- beat schedule diário (`pubmed-daily-incremental`) com incremental por `EDAT` e lookback de 2 dias.

Limitações atuais:

- PubMed Central full-text / OA subset + controle de licença artigo-a-artigo não implementado (ordem 3 — próxima);
- deduplicação fuzzy de autores/afiliações e enriquecimento semântico avançado por MeSH fora do escopo;
- `open_access` permanece `false` por padrão (sem verificação de licença PMC individual);
- sem uso de LLM para extração/validação (passo 11 adiado).

---

## 6.8C Estado implementado em 2026-07-02 — openFDA, DailyMed, Open Targets, EMA

Os quatro conectores P1 regulatórios/target restantes (`project_state/fontes_priorizacao.xlsx`)
foram implementados seguindo o padrão VLAEG do conector `pubmed`, com persistência compartilhada
em `workers/persistence/regulatory.py` (openFDA/DailyMed/EMA) e `workers/persistence/targets.py`
(Open Targets):

- **openFDA** (`workers/connectors/openfda/`): coleta `GET /drug/drugsfda.json` com paginação
  skip/limit; resolve a submissão mais recente por `submission_status_date` para status/data de
  aprovação; mapeia `review_priority=PRIORITY` para `special_designations=[priority_review]`;
  associa ao `DrugAsset` existente por nome/alias (case-insensitive) — sem correspondência, o
  registro é contado em `records_skipped`, não rejeitado. Popula `regulatory_approvals` e
  destrava `get_regulatory_status`/`search_drugs` com dados reais de aprovação FDA.
- **DailyMed** (`workers/connectors/dailymed/`): coleta `GET /services/v2/spls.json` paginado;
  extrai nome do medicamento do título SPL por heurística de separador; popula
  `regulatory_approvals.label_url` (chave corrente por asset+agência+região, sem
  `application_number` — SPL não expõe número de aplicação).
- **Open Targets** (`workers/connectors/opentargets/`): GraphQL `search`+`disease.associatedTargets`
  por termos-semente de doença (`OPEN_TARGETS_SEED_DISEASE_TERMS`, não é um crawl completo);
  popula `targets` (symbol, aliases via synonyms, external_ids ensembl/uniprot, open_targets_score,
  associação a `indications` por nome).
- **EMA** (`workers/connectors/ema/`): download do export oficial "Medicines output" (XLSX) via
  `EMA_MEDICINES_EXPORT_URL`, parsing por `openpyxl` com resolução de colunas por substring
  normalizada (robusto a pequenas variações de cabeçalho entre releases); popula
  `regulatory_approvals` com `agency=EMA`, `region=EU`, `special_designations=[orphan_drug]`
  quando aplicável. Classificado como export oficial (`AGENTS.md` §10, tier 2), não scraping.

Todos os quatro: quality gate mínimo (`asset_name`/`symbol` + `agency` obrigatórios via
`workers/base/staging.py`), `PersistenceDecisionEngine` para insert/replace/noop/conflict,
`SourceDocument` + `EvidenceSnippet` por registro, raw payload imutável no storage S3-compatible,
registrados em `tools/handshake.py` e no `beat_schedule` do Celery (`openfda-daily-incremental`,
`dailymed-daily-incremental`, `opentargets-weekly`, `ema-weekly`).

Limitações atuais:

- openFDA/DailyMed/EMA não expõem um filtro de delta confiável; execuções `incremental` são
  limitadas por `*_MAX_RECORDS_PER_RUN` e dependem de upserts idempotentes, não de um cursor real;
- resolução de `DrugAsset` é por nome/alias exato (case-insensitive), sem fuzzy matching — ativos
  regulatórios sem correspondência ficam pendentes até o ativo existir (via CT.gov ou correção manual);
- Open Targets é guiado por lista semente de doenças, não por todo o grafo da plataforma;
- sem uso de LLM para extração/validação (passo 11 segue como decisão à parte).

---



# 6A. Execução assíncrona de ingestão e processamento

A ingestão e o processamento pesado devem ser executados por **Celery + Redis** no MVP, com workers Python separados da API principal.

Regras:

- rotas FastAPI apenas criam jobs, consultam status ou disparam reprocessamento;
- parsing de PDF, processamento de exports grandes, embeddings, chamadas LLM, normalização em lote e deduplicação pesada devem ocorrer em workers;
- cada job deve registrar `IngestionJob` com status, fonte, início, fim, erro, volume, hash de arquivos, registros inseridos/atualizados/rejeitados e custo estimado de IA;
- workers devem usar timeouts, retries, backoff e limites de memória;
- scrapers devem rodar isolados, com allowlist, rate limit e possibilidade de desativação imediata.

## Uso de DuckDB nos workers

DuckDB deve processar dados brutos localmente nos workers antes da persistência no PostgreSQL.

Usos prioritários:

- leitura e transformação de CSV/JSON/Parquet grandes;
- validações batch;
- deduplicação preliminar;
- comparação entre snapshots;
- preparação de tabelas intermediárias;
- redução de carga no banco principal.

DuckDB não deve ser usado como banco canônico da aplicação.


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

# 7A. Taxonomia de maturidade da evidência — 2026-06-20

Todo dado ingerido recebe um nível de maturidade científica (`evidence_maturity`, ver
`docs/02`), do mais preliminar ao mais consolidado. Dados de níveis diferentes **nunca são
misturados sem rótulo** em bundles MCP.

| Ordem | `evidence_maturity` | Descrição |
|---:|---|---|
| 1 | `preprint` | Não revisado por pares (bioRxiv/medRxiv) |
| 2 | `conference_abstract` / `conference_preliminary` | Abstract/comunicação de congresso |
| 3 | `trial_registered` | Ensaio registrado, sem resultados |
| 4 | `trial_results_posted` | Resultados postados no registro |
| 5 | `peer_reviewed_primary` | Artigo primário revisado por pares |
| 6 | `regulatory_action` | Aprovação, label, recall, designação |
| 7 | `systematic_review` / `meta_analysis` | Síntese de evidência |
| 8 | `guideline` / `consolidated` | Diretriz/evidência consolidada |

Regras:

- Cada assertion carrega `evidence_maturity` + `confidence_score` + fonte + datas
  (`valid_from/valid_to`, `system_from/system_to`).
- A precedência continua regida pelo `PersistenceDecisionEngine` (autoridade da fonte):
  preprint/abstract **não podem superseder** evidência `peer_reviewed_primary`/`regulatory_action`.
- Bundles e ferramentas MCP **separam visualmente** evidência consolidada de evidência emergente.

---

# 7B. Política de congressos médicos — 2026-06-20

- **Primeira onda (MVP+):** apenas **ASCO, ESMO, ASH** (maior densidade de biomarcadores
  acionáveis e novidade clínica).
- **Ondas seguintes (P3/P4):** AACR → neuro (AAN/AAIC) → endócrino (ADA/ENDO) → gene/cell
  (ASGCT/ESGCT) → imuno (EAACI). Congressos de ciência básica com baixa acionabilidade clínica
  (AAI, CIS, FOCIS) ficam **fora do MVP** (P4).
- **Classificação obrigatória de cada item:** alto impacto vs. preliminar; fase 1/2 vs. fase 3;
  endpoint primário vs. subanálise/exploratório; dados de segurança; dados negativos/inconclusivos.
- **Linking temporal:** abstract de congresso → NCT do trial → publicação posterior. Quando o paper
  revisado chega, ele supersede o abstract sem apagar histórico (`supersede`/`archive`).
- **Compliance:** coleta apenas com as salvaguardas da "Política formal de scraping" (robots,
  sem evasão de captcha/paywall, raw em storage, allowlist, kill switch).

---

# 7C. Política de preprints — 2026-06-20

- **bioRxiv e medRxiv entram no MVP** (API barata), mas como **trilha sinalizada e opt-out por
  padrão**: `evidence_maturity = preprint`, confiança mínima, marcação explícita "não revisado por
  pares", **excluídos por default** de bundles consolidados.
- **Reconciliação obrigatória:** ao surgir DOI/artigo publicado, ligar o preprint à `Publication` e
  rebaixar/superseder o preprint.
- Preprints **nunca** são evidência primária para afirmações clínicas/regulatórias.

---

# 7D. Recorte temporal por fonte — 2026-06-20

Princípio: **recorte por novidade + impacto; data é filtro, não verdade**. A ingestão preserva todo
o histórico no raw/assertions; as *views* default focam recência.

| Tipo de fonte | Janela default | Racional |
|---|---|---|
| Registros de ensaios (CT.gov) | sem corte rígido; incremental por `source_updated_at` | "ativo/recém-atualizado" > data de publicação |
| Regulatório (openFDA/EMA/DailyMed/ANVISA) | rolling 24m em views; histórico preservado | aprovações/recalls recentes = sinal emergente |
| PubMed | rolling 24 meses (configurável) | atualidade × cobertura × ruído |
| Congressos | últimos 2 ciclos/edições | novidade concentrada nas últimas edições |
| Preprints | rolling 12 meses + reconciliação ao publicar | preliminar e volátil |

Trade-off: janela curta reduz custo/ruído mas perde contexto comparativo — mitigado mantendo o
histórico no banco e expondo-o sob demanda.

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
