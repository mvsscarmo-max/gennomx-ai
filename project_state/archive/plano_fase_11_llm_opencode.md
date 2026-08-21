<!-- validate-links: illustrative-paths -->
# Plano de implementação — Fase 11: motor LLM via OPENCODE

**Data:** 2026-06-23  
**Status:** Planejado para execução por outro agente de codificação  
**Decisão do usuário:** não haverá benchmark comparativo. O MVP deve usar uma chave API do
OPENCODE como motor inicial de LLM, começando pelo modelo DeepSeek V4 Pro.

---

## 1. Visão

Implementar a Fase 11 como uma camada interna de chamadas LLM controladas, auditáveis e
configuráveis, usada apenas em tarefas auxiliares de processamento, classificação, extração
estruturada ou enriquecimento.

A GennomX AI continua sendo infraestrutura de dados biomédicos, evidências e MCP. O LLM interno
não gera relatório final para cliente, não decide correções, não decide merges e não escreve fatos
diretamente no banco.

### Critério de sucesso

- backend possui um serviço interno `LLMService` ou equivalente;
- chamadas usam chave OPENCODE via variável protegida;
- modelo inicial fica configurável por ambiente;
- saídas são validadas por schema Pydantic antes de qualquer persistência por pipeline;
- chamadas registram metadados operacionais sem vazar prompt sensível ou segredo;
- testes mockados cobrem roteamento, erro, timeout, validação e bloqueio de escrita direta;
- documentação substitui "passo 11 adiado" por "Fase 11 planejada/implementada".

---

## 2. Link obrigatório antes da lógica final

Antes de implementar lógica dependente do provedor, o agente executor deve validar:

1. nome correto do provedor: `OPENCODE`;
2. URL base correta da API;
3. formato de autenticação;
4. compatibilidade com API estilo OpenAI Chat Completions/Responses;
5. identificador exato do modelo "DeepSeek V4 Pro";
6. suporte a JSON/schema structured output, ou fallback por validação local;
7. limites de contexto, tokens, rate limit, timeout e política de dados do provedor.

Criar uma checagem determinística em `tools/handshake.py` ou em script novo dedicado, por exemplo:

```bash
make handshake-llm
```

O handshake deve ser seguro:

- nunca imprimir a chave;
- aceitar modo `--dry-run` ou mock para CI;
- em ambiente sem chave, reportar `skipped: missing OPENCODE_API_KEY`;
- em ambiente com chave, executar requisição mínima de baixa exposição, como uma resposta JSON
  curta sem dados biomédicos reais.

Não construir extração clínica final sobre integração não validada.

---

## 3. Arquitetura proposta

### Configuração

Substituir ou deprecar as variáveis específicas de LiteLLM por variáveis genéricas e OPENCODE:

```env
LLM_PROVIDER=opencode
LLM_MODEL_PREMIUM=deepseek-v4-pro
LLM_MODEL_ECONOMY=deepseek-v4-pro
LLM_MAX_TOKENS=4096
LLM_TIMEOUT_SECONDS=60
LLM_TEMPERATURE=0
LLM_ENABLE_NETWORK_CALLS=false

OPENCODE_API_KEY=
OPENCODE_BASE_URL=
OPENCODE_MODEL_DEEPSEEK_V4_PRO=deepseek-v4-pro
```

O valor `deepseek-v4-pro` é placeholder operacional. O agente executor deve trocar pelo
identificador confirmado no handshake se o provedor usar outro nome.

### Serviço interno

Criar módulo sugerido:

```txt
backend/app/services/llm/
  __init__.py
  client.py
  schemas.py
  service.py
  errors.py
```

Responsabilidades:

- encapsular o cliente HTTP ou SDK;
- aplicar timeout, retries conservadores e backoff;
- forçar `temperature=0` em extrações estruturadas;
- impor limite de tokens;
- receber uma classe Pydantic de saída esperada;
- validar JSON retornado antes de devolver ao pipeline;
- retornar objeto interno com `model`, `provider`, `latency_ms`, `token_usage` quando disponível,
  `schema_valid`, `confidence` quando aplicável e `raw_response_hash`;
- nunca persistir dado factual sozinho.

Evitar acoplar o projeto ao OPENCODE de forma irreversível: `LLM_PROVIDER` deve permitir trocar o
adaptador depois, mesmo que o MVP só implemente `opencode`.

### Onde pode ser usado no MVP

Permitir somente usos controlados em workers:

- classificação auxiliar de documento;
- extração estruturada de campos a partir de texto já parseado;
- sugestão de normalização com evidence snippet obrigatório;
- triagem operacional de documentos.

Não usar em:

- rotas FastAPI síncronas;
- ferramentas MCP no caminho crítico;
- escrita direta em modelos SQLAlchemy;
- decisão final de conflito, correção, merge ou fonte vencedora;
- geração final de relatórios para cliente.

---

## 4. Dados e auditoria

Adicionar uma trilha de auditoria leve para chamadas LLM. Opção recomendada: nova tabela
`llm_call_logs`, via Alembic, com campos mínimos:

- `id`;
- `created_at`;
- `environment`;
- `provider`;
- `model`;
- `task_name`;
- `job_id` opcional;
- `source_document_id` opcional;
- `entity_type` e `entity_id` opcionais;
- `prompt_hash`;
- `input_payload_hash`;
- `raw_response_hash`;
- `schema_name`;
- `schema_valid`;
- `latency_ms`;
- `input_tokens`, `output_tokens`, `total_tokens`;
- `estimated_cost_usd` opcional;
- `status`;
- `error_type`;
- `error_detail_sanitized`.

Não armazenar prompt completo por padrão. Se houver necessidade futura de retenção de prompt para
auditoria, criar storage restrito com redaction e política própria antes de habilitar.

---

## 5. Segurança

Requisitos obrigatórios:

- `OPENCODE_API_KEY` somente em `.env`/secret manager, nunca no frontend;
- produção falha fechada se `LLM_ENABLE_NETWORK_CALLS=true` e faltar chave/base URL/modelo;
- logs não podem conter segredo, headers de autorização ou prompt completo;
- documentos externos passados ao LLM devem ser tratados como conteúdo não confiável;
- prompts do sistema devem instruir o modelo a extrair dados, não a executar instruções do texto;
- saída do LLM precisa de validação Pydantic;
- persistência exige evidência, confidence score e versionamento do pipeline;
- testes devem cobrir prompt injection indireta em fixture simples.

---

## 6. Testes obrigatórios

Criar testes unitários mockados em `backend/tests/unit/`:

- configuração carrega defaults seguros;
- produção rejeita LLM habilitado sem chave;
- cliente monta request sem expor segredo;
- timeout/retry gera erro controlado;
- JSON inválido é rejeitado;
- schema válido é aceito;
- erro do provedor é sanitizado;
- serviço não possui método de escrita direta no banco;
- prompt injection em texto externo não altera instrução do sistema;
- logging registra hashes/metadados sem conteúdo sensível.

Criar teste de integração opcional, marcado/skippable, para handshake real quando
`OPENCODE_API_KEY` estiver presente.

Gates esperados:

```bash
cd backend
python -m ruff check app tests
python -m pytest tests/unit/test_llm_* -q
python -m pytest tests/unit -q
```

Se houver migração:

```bash
cd backend
python -m alembic -c migrations/alembic.ini upgrade head --sql
python -m alembic -c migrations/alembic.ini downgrade -1 --sql
```

---

## 7. Documentação a atualizar

Atualizar no mesmo PR:

- `.env.example`: variáveis OPENCODE/LLM genéricas;
- `backend/app/config.py`: settings e validação fail-closed;
- `backend/pyproject.toml`: dependências necessárias, preferindo `httpx` já existente antes de SDK novo;
- `docs/01_ARQUITETURA.md`: camada LLM interna via OPENCODE;
- `docs/05_SEGURANCA_E_GOVERNANCA.md`: segurança de IA interna e segredos;
- `docs/06_TESTES_E_QUALIDADE.md`: testes LLM;
- `docs/09_DEPLOY_E_OPERACAO.md`: variáveis, handshake e observabilidade de custo;
- `docs/12_STACK_TECNOLOGICA_REFINADA.md`: substituir LiteLLM como decisão ativa do MVP por adaptador OPENCODE configurável;
- `docs/11_CHANGELOG_DECISOES.md`: registrar a decisão;
- `project_state/task_plan.md`: marcar Fase 11 como planejada/em implementação.

Se o agente decidir manter LiteLLM como biblioteca de abstração por trás do OPENCODE, deve
justificar no changelog. Caso contrário, remover a dependência opcional `llm` baseada em LiteLLM
quando não houver mais uso documentado.

---

## 8. Sequência recomendada de execução

1. Atualizar `.env.example` e `Settings`.
2. Criar handshake OPENCODE com mock/skip seguro.
3. Criar adaptador HTTP mínimo com `httpx`.
4. Criar schemas Pydantic de request/response internos.
5. Criar `LLMService` com validação por schema.
6. Criar migração `llm_call_logs`, se aprovada.
7. Criar testes unitários e integração opcional.
8. Atualizar docs e changelog.
9. Rodar gates locais.
10. Somente depois integrar o serviço a um worker real de extração/classificação.

---

## 9. Fora do escopo desta fase

- benchmark comparativo entre modelos;
- dashboard de prompts;
- geração final interna de relatórios;
- uso do LLM dentro de ferramentas MCP read-only;
- auto-merge, auto-correção ou seleção automática de fonte vencedora;
- exposição da chave OPENCODE ao frontend;
- processamento de documentos sensíveis sem política de retenção/redaction.

---

## 10. Riscos e decisões em aberto

| Risco | Mitigação |
|---|---|
| Nome real do modelo diverge de "DeepSeek V4 Pro" | handshake obrigatório antes da implementação final |
| OPENCODE não ser OpenAI-compatible | criar adaptador próprio; não espalhar chamadas diretas |
| Saída não estruturada | validação Pydantic local e rejeição fail-closed |
| Custo inesperado | limite de tokens, timeout, logging e flag `LLM_ENABLE_NETWORK_CALLS` |
| Prompt injection indireta | separar instruções do sistema de conteúdo externo e testar fixture maliciosa |
| Vazamento de dados sensíveis | não logar prompt completo; hash/redaction por padrão |

