# 12 — Stack Tecnológica Refinada do MVP

**Status:** Aprovada  
**Data:** 09/06/2026  
**Natureza:** decisão arquitetural complementar aos documentos de contexto, arquitetura, segurança, testes e operação.

---

## 1. Decisão aprovada

A stack oficial do MVP da **GennomX AI** passa a ser uma evolução da stack original, mantendo o núcleo **Supabase/PostgreSQL + FastAPI + DuckDB + pgvector**, mas acrescentando separação clara entre frontend, API/MCP, workers assíncronos, processamento batch e gateway de LLMs.

A decisão aprovada é:

```txt
Frontend:
Next.js, preferencialmente hospedado em Vercel ou Netlify.

Backend/API/MCP:
FastAPI como camada de API interna, regras de negócio, administração operacional e servidor MCP.

Jobs assíncronos:
Celery com Redis no MVP.
RabbitMQ, SQS ou equivalente ficam reservados para fase posterior se houver necessidade real de maior durabilidade, roteamento avançado ou alto volume de filas.

Processamento batch:
DuckDB executado nos workers, para processar arquivos grandes, exports, JSON/CSV massivos, validações batch, deduplicação e normalização antes da persistência no banco principal.

Banco, Auth, Storage e busca:
Supabase/PostgreSQL como núcleo de dados, Supabase Auth para autenticação, Supabase Storage ou S3-compatible storage para arquivos e snapshots, PostgreSQL full-text search para busca textual inicial e pgvector para busca semântica no MVP avançado/Fase 2.

LLM Gateway:
Adaptador interno OPENCODE (MVP: DeepSeek V4 Pro), configurável por provedor via ``LLM_PROVIDER``, com validação por schema Pydantic, auditoria ``llm_call_logs`` e bloqueio de escrita direta por LLM.
```

Essa decisão não altera a premissa central do projeto: a GennomX AI continua sendo uma infraestrutura proprietária de dados e MCP, não um chatbot e não o gerador final de relatórios.

---

## 2. Arquitetura refinada

```txt
[Fontes externas]
APIs oficiais / exports / PDFs / uploads / scraping controlado
        │
        ▼
[FastAPI Admin/API]
Cria jobs, consulta status, expõe API segura, serve ferramentas MCP
        │
        ▼
[Celery Broker: Redis no MVP]
Fila de ingestão, parsing, embeddings, extração por IA e validações
        │
        ▼
[Workers Python]
Conectores + parsers + DuckDB + OPENCODE/LLM + validação por schema
        │
        ├── salva raw files / PDFs / snapshots
        │       ▼
        │   [Supabase Storage / S3-compatible storage]
        │
        └── grava dados limpos, evidências, logs e índices
                ▼
        [Supabase PostgreSQL + full-text search + pgvector]
                ▲
                │
[Next.js Dashboard] ←→ [FastAPI API] ←→ [MCP Server]
                │
                ▼
        Modelos host: ChatGPT / Claude / agentes privados
```

---

## 3. Responsabilidades por camada

## 3.1 Next.js

Responsável por:

- dashboard operacional;
- navegação por ativos, empresas, trials, indicações, targets e documentos;
- telas de ingestão, qualidade, segurança e testes;
- visualização de logs;
- edição corretiva com rastreabilidade;
- experiência visual e interação do usuário.

Não deve concentrar:

- regras críticas de segurança;
- processamento pesado;
- parsing de PDFs;
- lógica principal de MCP;
- escrita direta em tabelas sensíveis sem mediação de API e RLS.

## 3.2 FastAPI

Responsável por:

- API interna;
- endpoints usados pelo dashboard;
- criação e monitoramento de jobs;
- regras de negócio;
- validação de payloads;
- controle de permissões;
- documentação OpenAPI;
- integração com servidor MCP;
- endpoints administrativos protegidos;
- auditoria de chamadas.

## 3.3 Celery + Redis

Responsável por:

- executar ingestões assíncronas;
- processar arquivos grandes;
- acionar parsers;
- chamar rotinas de DuckDB;
- orquestrar extrações por IA;
- gerar embeddings;
- rodar validações de qualidade;
- registrar logs de jobs;
- evitar que API, dashboard e MCP fiquem lentos por processamento pesado.

Redis é o broker padrão do MVP por simplicidade. RabbitMQ ou SQS só devem ser adotados quando houver necessidade comprovada.

## 3.4 DuckDB

Responsável por:

- processar exports grandes localmente nos workers;
- transformar JSON/CSV/Parquet quando aplicável;
- fazer validações batch;
- deduplicar e normalizar dados antes da persistência;
- reduzir carga no Supabase/PostgreSQL;
- apoiar exploração analítica offline.

DuckDB não substitui o banco principal. Ele é motor de processamento local/batch.

## 3.5 Supabase/PostgreSQL

Responsável por:

- entidades canônicas;
- relacionamentos;
- logs;
- usuários e permissões;
- dados estruturados;
- evidências;
- metadados de fontes;
- histórico de ingestões;
- trilhas de auditoria;
- busca textual inicial;
- vetores com pgvector quando habilitado.

## 3.6 Supabase Storage ou S3-compatible storage

Responsável por:

- payloads brutos;
- PDFs originais;
- snapshots permitidos;
- arquivos processados;
- artefatos de testes;
- logs brutos volumosos;
- camadas `raw`, `processed`, `curated`, `evidence` e `archive`.

## 3.7 OPENCODE / LLM interno

Responsável por:

- encapsular chamadas HTTP ao provedor de LLM (OpenAI-compatible API);
- validar toda saída por schema Pydantic antes de entregar ao pipeline;
- registrar metadados operacionais (hashes, latency, tokens, schema_valid, status);
- garantir que o LLM interno não persiste dados diretamente no banco;
- manter o provedor trocável via ``LLM_PROVIDER`` (MVP: ``opencode``).

Regras obrigatórias:

- não fixar a arquitetura a um modelo específico;
- usar modelo premium configurável para extrações críticas;
- usar modelo econômico configurável para classificação, triagem e tarefas auxiliares;
- validar toda saída por schema;
- não permitir persistência de fatos sem evidência, confidence score e rastreabilidade;
- nunca permitir que LLM grave diretamente no banco.

---

## 4. Política de modelos de IA

A arquitetura deve escolher modelos por função, não por preferência fixa.

| Classe de tarefa | Classe de modelo recomendada | Observação |
|---|---|---|
| Extração de endpoints clínicos | Premium configurável | Exigir evidência e validação por schema |
| Interpretação regulatória sensível | Premium configurável | Usar somente como auxílio, não como fonte primária |
| Classificação de documentos | Econômico configurável | Baixo custo e alto volume |
| Triagem de PDFs | Econômico configurável | Usar depois da extração/OCR técnico |
| Deduplicação auxiliar | Econômico configurável | Não decidir merge automaticamente sem score e logs |
| Resumo operacional interno | Econômico ou intermediário | Deve manter links para evidências |
| Geração final de relatório | Fora da aplicação | Realizada por modelos host externos via MCP |

OCR e parsing documental devem ser tratados preferencialmente por ferramentas especializadas antes da etapa de LLM. O LLM deve interpretar texto extraído, classificar, estruturar ou enriquecer, mas não deve ser a primeira e única camada de OCR para documentos críticos.

---

## 5. Decisões de custo e manutenção

A arquitetura deve buscar baixo custo inicial, mas não deve depender da gratuidade de free tiers.

Princípios:

- começar simples;
- evitar OpenSearch, Pinecone, Kubernetes, Airflow ou data warehouse no MVP;
- centralizar banco, auth, storage, full-text search e vetores no Supabase enquanto for suficiente;
- isolar processamento pesado em workers;
- controlar custo de IA por job, fonte, modelo e tarefa;
- prever migração futura sem reescrita conceitual.

---

## 6. Riscos e mitigadores

| Risco | Mitigação |
|---|---|
| Supabase virar gargalo de processamento | Usar DuckDB nos workers e persistir apenas dados limpos |
| API/MCP ficarem lentos durante ingestão | Celery + Redis e workers separados |
| pgvector crescer além do ideal | Prever Qdrant/Weaviate/Pinecone em fase futura |
| Filas virarem caixa-preta | Registrar `IngestionJob`, métricas, status, erros e custos |
| LLM econômico gerar dado ruim | Usar apenas para tarefas auxiliares e validar por schema |
| LLM gravar fatos incorretos | Proibir gravação direta; exigir evidência e confidence score |
| Free tiers acabarem ou limitarem operação | Tratar baixo custo como benefício, não premissa permanente |
| Scraper travar ou gerar OOM | Executar em worker isolado com timeout, limites e logs |

---

## 7. Implicações para desenvolvimento

Ao criar ou alterar código, agentes devem respeitar:

- rotas FastAPI não devem executar processamento longo;
- tarefas longas devem ser jobs Celery;
- workers devem registrar início, fim, status, erro, volume e custo;
- DuckDB deve ser usado para batch pesado antes de persistir no Supabase;
- Next.js deve consumir API segura, não contornar regras do backend;
- MCP deve ser read-only no MVP;
- OPENCODE/LLM deve ser usado por serviço próprio (`app/services/llm/`), com logs, limites e validação;
- modelos devem ser configuráveis por ambiente;
- nenhuma chave de IA ou banco deve ser hardcoded;
- toda mudança de stack deve atualizar `AGENTS.md`, `docs/01_ARQUITETURA.md`, `docs/06_TESTES_E_QUALIDADE.md`, `docs/09_DEPLOY_E_OPERACAO.md` e `docs/11_CHANGELOG_DECISOES.md`.
