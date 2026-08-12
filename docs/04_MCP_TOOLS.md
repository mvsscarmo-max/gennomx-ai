# 04 — Servidor MCP e Ferramentas

## Projeção corrente e freshness — 2026-06-21

`find_trials`, `get_trial_results`, `get_regulatory_status` e `search_publications` filtram
`is_current=true`; versões superseded/archived não são entregues ao modelo host. Trials retornam
`source_updated_at` e `freshness_status`, permitindo distinguir dado corrente de informação que
requer revalidação sem apagar o histórico auditável.

## Estado implementado — correção fase 2 (2026-06-20)

- Transporte MCP interoperável em processo isolado (`pip install -e '.[mcp]'` e `python -m app.mcp.stdio_server`), com FastMCP e nove ferramentas read-only; `/api/mcp/call` permanece como adaptador HTTP legado. O SDK MCP é extra opcional para não acoplar o ciclo de dependências Starlette do FastMCP ao runtime FastAPI.
- Allowlist explícita por cliente via `MCP_SCOPES_CHATGPT`, `MCP_SCOPES_CLAUDE` e `MCP_SCOPES_PRIVATE_AGENT`.
- Rate limit atômico no Redis fora de desenvolvimento; memória apenas para desenvolvimento/testes.
- Corpo HTTP limitado por `MCP_MAX_REQUEST_BYTES`; JSON e `Content-Length` inválidos são recusados.
- Tokens usam comparação em tempo constante; respostas 500 não expõem exceções internas.
- Auditoria registra no máximo 100 identificadores e tipos de entidades, sem copiar a resposta completa.

Este documento especifica a estratégia MCP da GennomX AI, suas ferramentas iniciais, limites, logs, segurança e uso por modelos host.

> **VLAEG:** este documento materializa o Princípio 3.1 (contrato de dados) aplicado a cada ferramenta MCP. Ver `docs/13_PROTOCOLO_VLAEG.md`.

---

# 0. Contrato de dados das ferramentas MCP (VLAEG 3.1)

Toda ferramenta MCP tem um contrato `{input, processamento, output}`. A validação de argumentos é feita por código (`backend/app/mcp/tools/*` + dispatcher), e a saída segue um **envelope padrão** auditável.

## 0.1 Envelope de saída padrão

```json
{
  "data": [],
  "count": 0,
  "limitations": ["mensagens sobre cobertura, cap de resultados, dados ausentes"],
  "gaps": ["lacunas conhecidas: dados limitados às fontes ingeridas, não exaustivo"]
}
```

Quando aplicável, os itens de `data` carregam rastreabilidade (`_source`, IDs, `confidence_score`, `last_updated`) e a ferramenta pode retornar evidências/fontes. Exemplo real em `backend/app/mcp/tools/search_drugs.py`.

## 0.2 Regras de contrato comuns a todas as ferramentas

- **input:** argumentos validados e truncados (limites de tamanho), `limit` capado por `MCP_MAX_RESULTS_PER_TOOL`;
- **processamento:** SQL parametrizado (anti-injection), allowlist de campos retornáveis, read-only;
- **output:** envelope padrão acima, com `limitations`/`gaps` sempre presentes quando houver cap ou ausência de resultados;
- **auditoria:** cada chamada (inclusive inválida/bloqueada) é registrada em `mcp_query_logs`.

As entradas e saídas específicas de cada ferramenta estão detalhadas na seção 8.3 a seguir.

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

> **DRY-7 (2026-07-20):** a ferramenta retorna endpoints planejados/postados, resultados por
> grupo e eventos adversos projetados da fixture ClinicalTrials.gov, todos com `evidence_id`.
> Ausência de resultados ou safety gera `gaps`; valores negativos/inconclusivos não são filtrados.

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

> **Fonte ativa (2026-06-23):** `search_publications` consome dados reais do conector `pubmed` (PubMed E-utilities via ESearch/EFetch), com rastreabilidade completa até `SourceDocument` e `EvidenceSnippet`. Resultados incluem `pmid`, `doi`, `journal`, `publication_date`, `publication_type`, `abstract` truncado em 500 chars e `authors` (top 5).

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

> **Fonte ativa (2026-07-02):** consome `regulatory_approvals`, populada pelos conectores
> `openfda` (FDA, `drugsfda.json`), `dailymed` (FDA, SPL — apenas `label_url`, sem
> `application_number`) e `ema` (EMA/EU, export oficial "Medicines output"). Retorno inclui
> `special_designations` (ex.: `priority_review`, `orphan_drug`) e `pathway` quando disponível.
> Ativos regulatórios sem `DrugAsset` correspondente (por nome/alias exato) ainda não aparecem —
> ver limitações em `docs/03` §6.8C.

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

## 8.8 Estado implementado em 2026-06-12

Implementado no backend FastAPI:

- `POST /api/mcp/call` recebe `AsyncSession` via `Depends(get_db)`;
- ferramentas MCP são despachadas com sessão de banco explícita, sem depender de `request.state`;
- chamadas bem-sucedidas gravam `mcp_query_logs` com cliente, ferramenta, hash de input, argumentos normalizados, contagem de resultados, latência e status;
- chamadas com argumentos inválidos, ferramentas desconhecidas ou ferramentas bloqueadas também geram log com status de erro/bloqueio antes da resposta HTTP ser propagada;
- chamadas **não autenticadas (401)** são a exceção deliberada: não geram escrita em `mcp_query_logs` nem `commit`, apenas log estruturado (`mcp_call_unauthenticated`) — ver 8.9;
- corpo da chamada e `arguments` devem ser objetos JSON;
- o endpoint continua read-only do ponto de vista das ferramentas host; a única escrita feita pelo endpoint é o log de auditoria.

Pendências:

- persistir `source_entities_accessed` e `entity_types_accessed` por ferramenta;
- manter e revisar escopos granulares por token/ferramenta;
- adicionar testes de contrato para cada ferramenta MCP;
- garantir que todas as respostas retornem evidências quando houver dado crítico.

## 8.9 Mitigação de DoS pré-autenticação (2026-06-23)

O caminho de falha de autenticação (token ausente/inválido) é o vetor de ataque mais barato e,
por isso, recebe tratamento dedicado em `app/mcp/server.py`:

- `_check_pre_auth_rate_limit` aplica limite por IP de cliente **antes** de `_authenticate_mcp` ser
  chamado (30 requisições/60s por IP); em produção via contador Redis com TTL, em
  desenvolvimento/teste via bucket em memória (`_ip_rate_buckets`);
- buckets de IP vazios são removidos imediatamente após filtragem; uma varredura periódica
  (`_sweep_stale_ip_buckets`, a cada 5 minutos) remove IPs cujo bucket expirou totalmente, evitando
  crescimento de memória por IPs forjados/efêmeros que nunca retornam para serem refiltrados;
- no `except HTTPException` de `mcp_call`, respostas `401` **não** chamam `_persist_mcp_log`/`commit`
  — apenas `logger.warning("mcp_call_unauthenticated", ...)`. Demais status (403/404/erro) continuam
  sendo auditados normalmente em `mcp_query_logs`;
- erros internos de ferramenta (`search_drugs`, `find_trials`, etc.) logam a exceção via `structlog`
  e retornam apenas `"Query failed"` ao cliente host, nunca o texto bruto da exceção.

Testes de regressão: `backend/tests/integration/test_mcp_http_flow.py`
(`test_mcp_http_call_without_token_rejects_without_db_write`) e
`backend/tests/unit/test_mcp_tools_error_handling.py`.

---



## 8A. Integração com a stack refinada

No MVP, o servidor MCP deve estar integrado ao backend FastAPI ou a um serviço Python equivalente, mantendo as seguintes regras:

- ferramentas MCP devem ser read-only no MVP;
- ferramentas MCP não devem disparar processamento pesado síncrono;
- quando uma ferramenta exigir bundle complexo, ela pode consultar dados pré-processados ou criar job assíncrono com status controlado;
- o MCP não deve acessar diretamente dados brutos, segredos, arquivos sensíveis ou SQL arbitrário;
- chamadas a LLMs internos via LiteLLM não devem ocorrer dentro do caminho crítico de ferramentas MCP sem limite, timeout e logging;
- respostas devem priorizar dados estruturados e evidências já persistidas.


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
