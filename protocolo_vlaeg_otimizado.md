<!-- validate-links: illustrative-paths -->
# Protocolo VLAEG Otimizado

**Framework operacional para criação de aplicações empresariais, automações, agentes de IA e sistemas digitais escaláveis**

**Versão:** 1.0  
**Data:** 17/06/2026  
**Uso recomendado:** planejamento, arquitetura, desenvolvimento, automação, governança e evolução de sistemas empresariais.

---

## Sumário

1. [Visão geral do Protocolo VLAEG](#1-visão-geral-do-protocolo-vlaeg)
2. [Objetivo central](#2-objetivo-central)
3. [Princípios fundamentais](#3-princípios-fundamentais)
4. [Pilares do protocolo](#4-pilares-do-protocolo)
5. [Etapas de aplicação](#5-etapas-de-aplicação)
6. [Modelo de arquitetura recomendado](#6-modelo-de-arquitetura-recomendado)
7. [Fluxo geral para criação de aplicações empresariais](#7-fluxo-geral-para-criação-de-aplicações-empresariais)
8. [Critérios de validação e qualidade](#8-critérios-de-validação-e-qualidade)
9. [Diretrizes para automação e integração](#9-diretrizes-para-automação-e-integração)
10. [Boas práticas de implementação](#10-boas-práticas-de-implementação)
11. [Riscos, limitações e pontos de atenção](#11-riscos-limitações-e-pontos-de-atenção)
12. [Modelo reutilizável do protocolo](#12-modelo-reutilizável-do-protocolo)
13. [Conclusão estratégica](#13-conclusão-estratégica)

---

# 1. Visão geral do Protocolo VLAEG

O **Protocolo VLAEG** é um modelo operacional para planejar, arquitetar, construir, validar, automatizar e evoluir sistemas digitais empresariais com alta rastreabilidade, segurança e capacidade de manutenção.

A sigla **VLAEG** é definida operacionalmente como:

| Letra | Pilar | Finalidade |
|---|---|---|
| **V** | **Visão** | Definir problema, objetivo, escopo, usuários, dados, regras de negócio e resultado esperado. |
| **L** | **Link** | Validar conexões, integrações, fontes de dados, APIs, credenciais, webhooks e ambientes. |
| **A** | **Arquitetura** | Desenhar módulos, responsabilidades, modelos de dados, fluxos, regras determinísticas e estrutura técnica. |
| **E** | **Estilo** | Refinar experiência do usuário, interface, linguagem, apresentação dos dados e qualidade da entrega. |
| **G** | **Gatilho** | Implantar automações, agendamentos, webhooks, monitoramento, operação contínua e evolução. |

O protocolo deve ser utilizado como referência para projetos de:

- ERPs internos;
- CRMs;
- dashboards executivos;
- sistemas de gestão de processos;
- automações administrativas;
- agentes de IA corporativos;
- integrações entre sistemas;
- fluxos operacionais automatizados;
- aplicações sob demanda;
- backoffices digitais;
- sistemas com rotinas programadas, webhooks, filas ou listeners.

---

# 2. Objetivo central

O objetivo central do Protocolo VLAEG é transformar uma necessidade empresarial em uma solução digital funcional, segura, rastreável e escalável, evitando improvisação técnica e reduzindo riscos de retrabalho.

O protocolo busca garantir que todo projeto tenha:

1. objetivo claro;
2. fonte de dados definida;
3. regras de negócio documentadas;
4. arquitetura validada antes do desenvolvimento;
5. integrações testadas antes da lógica final;
6. automações determinísticas sempre que possível;
7. documentação viva;
8. testes mínimos obrigatórios;
9. UX adequada ao usuário final;
10. rotina de manutenção e evolução contínua.

> **Regra central:** nenhuma implementação relevante deve começar antes de existir clareza sobre entrada, processamento, saída, regras de negócio, fonte da verdade e critério de sucesso.

---

# 3. Princípios fundamentais

## 3.1. Dados primeiro

Antes de construir telas, agentes, scripts, automações ou integrações, o projeto deve definir:

- quais dados entram;
- de onde os dados vêm;
- quem é a fonte da verdade;
- quais campos são obrigatórios;
- quais formatos são aceitos;
- quais validações serão aplicadas;
- qual é o payload final;
- onde o resultado será entregue.

### Modelo mínimo de contrato de dados

```json
{
  "input": {
    "fonte": "sistema_origem",
    "campos_obrigatorios": [],
    "campos_opcionais": [],
    "formato": "json/csv/api/manual"
  },
  "processamento": {
    "regras": [],
    "validacoes": [],
    "transformacoes": []
  },
  "output": {
    "destino": "dashboard/api/email/banco_de_dados",
    "formato": "json/html/pdf/tabela",
    "criterio_de_sucesso": ""
  }
}
```

---

## 3.2. Lógica de negócio determinística

Agentes de IA podem auxiliar em interpretação, classificação, redação, priorização e tomada de decisão assistida. Porém, regras críticas de negócio devem ser implementadas de modo determinístico.

Exemplos de lógica que deve ser determinística:

- cálculo financeiro;
- apuração de impostos;
- validação documental;
- controle de estoque;
- geração de cobrança;
- autorização de acesso;
- integração com sistemas oficiais;
- execução de pagamentos;
- atualização de registros produtivos.

> **Regra prática:** IA pode sugerir, classificar e auxiliar. Código determinístico deve validar, calcular, registrar e executar.

---

## 3.3. Fonte única da verdade

Todo projeto deve declarar sua fonte primária de dados.

Exemplos:

- PostgreSQL/Supabase;
- ERP legado;
- planilha controlada;
- CRM;
- API oficial;
- banco transacional;
- storage documental;
- sistema público;
- base interna validada.

Nenhum sistema deve operar com múltiplas fontes conflitantes sem regra clara de precedência.

### Modelo de precedência de fontes

```text
1. Banco transacional oficial
2. API oficial
3. Exportação controlada
4. Planilha validada
5. Upload manual auditável
6. Extração externa controlada
```

---

## 3.4. Documentação como parte da arquitetura

A documentação não é acessória. Ela é parte operacional do sistema.

Todo projeto deve manter, no mínimo:

- contexto estratégico;
- arquitetura;
- segurança e governança;
- testes e qualidade;
- decisões de UX;
- roadmap;
- deploy e operação;
- glossário;
- changelog de decisões.

Toda mudança relevante deve ser registrada com:

```text
Data:
Autor:
Decisão:
Motivo:
Impacto:
Arquivos afetados:
Riscos:
Próximos passos:
```

---

## 3.5. Autocorreção estruturada

Quando houver erro, falha de integração, bug ou comportamento inesperado, aplicar o ciclo:

1. **Analisar:** ler erro, logs, payload e contexto.
2. **Isolar:** identificar se o problema está em dados, regra, integração, infraestrutura ou interface.
3. **Corrigir:** ajustar código, configuração ou regra.
4. **Testar:** executar teste unitário, teste de integração ou simulação manual.
5. **Documentar:** registrar aprendizado no changelog, arquitetura ou documentação operacional.
6. **Prevenir recorrência:** criar validação, teste ou alerta.

> **Regra:** o mesmo erro não deve ocorrer duas vezes sem gerar melhoria documental, teste ou validação preventiva.

---

# 4. Pilares do protocolo

## Pilar 1 — Clareza estratégica

Antes de qualquer implementação:

- qual problema será resolvido?
- para quem?
- com qual ganho operacional?
- qual dor será eliminada?
- qual indicador será melhorado?
- o projeto é necessário, desejável e viável?

### Checklist

```text
[ ] Problema definido
[ ] Usuário-alvo definido
[ ] Resultado esperado definido
[ ] Métrica de sucesso definida
[ ] Escopo inicial delimitado
[ ] Fora de escopo declarado
[ ] Restrições conhecidas
```

---

## Pilar 2 — Governança de dados

Todo dado deve ter:

- origem;
- dono;
- formato;
- periodicidade de atualização;
- regra de validação;
- política de retenção;
- nível de sensibilidade;
- permissão de acesso.

### Classificação sugerida

```text
Público
Interno
Confidencial
Sensível
Crítico
```

---

## Pilar 3 — Arquitetura modular

Todo sistema deve ser dividido em módulos com responsabilidades claras.

### Modelo base

```text
Interface
├─ Frontend / Dashboard / Chat / Portal

Aplicação
├─ API
├─ Serviços de negócio
├─ Orquestração
├─ Agentes de IA
├─ Validações

Dados
├─ Banco transacional
├─ Banco analítico
├─ Storage
├─ Cache

Integrações
├─ APIs externas
├─ Webhooks
├─ Filas
├─ ETL/ELT
├─ Conectores

Operação
├─ Logs
├─ Monitoramento
├─ Alertas
├─ Auditoria
├─ Backups
```

---

## Pilar 4 — Automação controlada

A automação deve ser:

- rastreável;
- reversível quando possível;
- auditável;
- testável;
- monitorada;
- limitada por permissões;
- protegida contra falhas em cascata.

Toda automação deve declarar:

```text
Evento de disparo:
Condição de execução:
Dados necessários:
Ação executada:
Destino do resultado:
Responsável:
Fallback:
Log obrigatório:
Critério de sucesso:
Critério de falha:
```

---

## Pilar 5 — Segurança desde o início

Segurança não deve ser adicionada ao final. Deve existir desde a visão inicial.

Controles mínimos:

- autenticação;
- autorização por perfil;
- segregação de ambientes;
- proteção de segredos;
- logs de auditoria;
- validação de entrada;
- rate limit;
- backup;
- criptografia em trânsito;
- controle de acesso a dados sensíveis;
- princípio do menor privilégio.

---

## Pilar 6 — UX orientada à decisão

A interface deve ajudar o usuário a decidir e agir.

Cada tela, dashboard ou relatório deve responder:

- o que aconteceu?
- por que aconteceu?
- qual é o status?
- qual é o risco?
- qual ação deve ser tomada?
- qual é a prioridade?

Evitar:

- excesso de indicadores;
- telas poluídas;
- métricas sem ação associada;
- botões ambíguos;
- fluxos longos sem necessidade;
- ausência de feedback após ação.

---

## Pilar 7 — Evolução contínua

Todo projeto deve nascer com capacidade de evolução.

Isso exige:

- backlog;
- roadmap;
- versionamento;
- changelog;
- testes;
- modularidade;
- documentação;
- logs;
- métricas;
- monitoramento.

---

# 5. Etapas de aplicação

# Etapa 0 — Inicialização obrigatória

Antes de construir, criar a estrutura mínima do projeto:

```text
/
├─ AGENTS.md
├─ README.md
├─ CLAUDE.md
├─ GEMINI.md
├─ .env.example
├─ docs/
│  ├─ 00_CONTEXTO_ESTRATEGICO.md
│  ├─ 01_ARQUITETURA.md
│  ├─ 02_SEGURANCA_E_GOVERNANCA.md
│  ├─ 03_TESTES_E_QUALIDADE.md
│  ├─ 04_DASHBOARD_UX.md
│  ├─ 05_ROADMAP.md
│  ├─ 06_DEPLOY_E_OPERACAO.md
│  ├─ 07_GLOSSARIO.md
│  └─ 08_CHANGELOG_DECISOES.md
├─ architecture/
│  └─ POPs técnicos, quando aplicável
├─ tools/
│  └─ scripts determinísticos
├─ .tmp/
│  └─ arquivos temporários
└─ project_state/
   ├─ task_plan.md
   ├─ findings.md
   └─ progress.md
```

## Função de cada arquivo

### `AGENTS.md`

Arquivo normativo principal para IA, agentes e desenvolvedores. Deve conter:

- regras de execução;
- limites operacionais;
- padrões de código;
- responsabilidades;
- comandos permitidos;
- critérios de segurança;
- comportamento esperado dos agentes.

### `README.md`

Arquivo introdutório para humanos. Deve explicar:

- objetivo do projeto;
- escopo;
- instalação;
- uso básico;
- visão geral da arquitetura;
- principais comandos.

### `CLAUDE.md` e `GEMINI.md`

Arquivos curtos de redirecionamento. Devem informar que `AGENTS.md` é a fonte principal de instruções.

Modelo:

```md
# GEMINI.md

Este projeto usa `AGENTS.md` como fonte principal de instruções para agentes.

Antes de alterar código ou documentação, leia:
- `AGENTS.md`
- `docs/00_CONTEXTO_ESTRATEGICO.md`
- `docs/01_ARQUITETURA.md`
```

### `docs/00_CONTEXTO_ESTRATEGICO.md`

Problema, objetivo, público, escopo, restrições, métricas de sucesso e contexto de negócio.

### `docs/01_ARQUITETURA.md`

Arquitetura macro, módulos, fluxos, decisões técnicas, modelo de dados e integrações.

### `docs/02_SEGURANCA_E_GOVERNANCA.md`

Segurança, permissões, LGPD, segredos, logs, auditoria, retenção de dados e governança.

### `docs/03_TESTES_E_QUALIDADE.md`

Estratégia de testes unitários, integração, E2E, validação de payloads, critérios de aceite e qualidade.

### `docs/04_DASHBOARD_UX.md`

Interface, experiência do usuário, fluxos, telas, padrões visuais, acessibilidade e decisões de apresentação.

### `docs/05_ROADMAP.md`

Fases, entregas, milestones, backlog, priorização e evolução.

### `docs/06_DEPLOY_E_OPERACAO.md`

Ambientes, deploy, variáveis, monitoramento, logs, backup, recuperação e rotina operacional.

### `docs/07_GLOSSARIO.md`

Termos técnicos, regras de negócio, siglas, conceitos e definições operacionais.

### `docs/08_CHANGELOG_DECISOES.md`

Registro de decisões arquiteturais, escopo, stack, dados, segurança, fontes, MCPs, integrações e mudanças relevantes.

### `project_state/task_plan.md`

Plano de execução, fases, tarefas, responsáveis e checklists.

### `project_state/findings.md`

Pesquisas, descobertas, limitações, hipóteses, restrições externas e aprendizados.

### `project_state/progress.md`

Histórico de execução, erros, testes realizados, pendências e resultados.

---

# Etapa 1 — V: Visão

Objetivo: transformar uma demanda vaga em um blueprint operacional.

## Perguntas obrigatórias

```text
1. Estrela-guia:
Qual é o resultado único mais importante que este sistema deve entregar?

2. Usuários:
Quem usará o sistema? Administrador, operador, cliente, gestor, agente interno?

3. Fonte da verdade:
Onde vivem os dados primários?

4. Entrada:
Quais dados entram no sistema? Em qual formato?

5. Processamento:
Quais regras, cálculos, validações ou classificações serão aplicadas?

6. Saída:
Qual payload final será entregue? Dashboard, API, e-mail, planilha, PDF, banco, notificação?

7. Integrações:
Quais sistemas externos serão conectados?

8. Segurança:
Quais dados são sensíveis? Quem pode ver, editar, excluir ou exportar?

9. Frequência:
O processo é manual, sob demanda, agendado, em tempo real ou por webhook?

10. Critério de sucesso:
Como saberemos que a solução funcionou?
```

## Entregáveis da fase

```text
[ ] Contexto estratégico preenchido
[ ] Escopo definido
[ ] Fora de escopo definido
[ ] Usuários mapeados
[ ] Fonte da verdade definida
[ ] Regras de negócio documentadas
[ ] Payload de entrada definido
[ ] Payload de saída definido
[ ] Critérios de sucesso definidos
```

---

# Etapa 2 — L: Link

Objetivo: validar conectividade antes de construir lógica complexa.

## Checklist de conectividade

```text
[ ] APIs disponíveis
[ ] Credenciais configuradas
[ ] Variáveis de ambiente definidas
[ ] Permissões testadas
[ ] Webhooks validados
[ ] Banco acessível
[ ] Storage acessível
[ ] Filas ou jobs configurados
[ ] Rate limits conhecidos
[ ] Erros de conexão tratados
```

> **Regra:** não desenvolver lógica final sobre integração não testada.

## Scripts mínimos de handshake

Devem testar:

- autenticação;
- leitura simples;
- escrita simples, quando aplicável;
- tratamento de erro;
- timeout;
- resposta inesperada;
- limite de taxa;
- credencial inválida.

---

# Etapa 3 — A: Arquitetura

Objetivo: desenhar o sistema antes de construir.

## Modelo em camadas

### Camada 1 — Documentação e POPs

Contém:

- regras de negócio;
- fluxos;
- modelos de dados;
- integrações;
- exceções;
- casos de borda;
- decisões arquiteturais.

> **Regra:** se a regra mudar, atualize a documentação antes ou junto com o código.

### Camada 2 — Orquestração

Responsável por:

- coordenar fluxos;
- chamar serviços;
- aplicar regras;
- decidir rotas;
- acionar ferramentas;
- controlar estado;
- registrar logs.

### Camada 3 — Ferramentas determinísticas

Responsável por:

- cálculos;
- extrações;
- transformações;
- validações;
- integrações;
- geração de arquivos;
- execução de tarefas.

As ferramentas devem ser:

```text
[ ] Pequenas
[ ] Atômicas
[ ] Testáveis
[ ] Reutilizáveis
[ ] Sem efeitos colaterais desnecessários
[ ] Com logs
[ ] Com tratamento de erro
[ ] Com entrada e saída definidas
```

---

# Etapa 4 — E: Estilo

Objetivo: tornar a solução usável, compreensível e profissional.

Aplicar em:

- dashboards;
- relatórios;
- portais;
- mensagens automatizadas;
- e-mails;
- respostas de agentes;
- PDFs;
- telas administrativas;
- interfaces internas.

## Critérios de estilo e UX

```text
[ ] Linguagem clara
[ ] Hierarquia visual
[ ] Métricas acionáveis
[ ] Estados de vazio
[ ] Mensagens de erro compreensíveis
[ ] Feedback após ações
[ ] Responsividade
[ ] Acessibilidade básica
[ ] Consistência visual
[ ] Redução de ruído
```

## Estrutura sugerida para dashboards

```text
Topo: KPIs principais
Centro: evolução temporal e status
Lateral: filtros e segmentações
Base: detalhes, logs ou registros
Ações: exportar, atualizar, corrigir, aprovar, rejeitar
```

---

# Etapa 5 — G: Gatilho

Objetivo: colocar a solução para operar de forma confiável.

## Tipos de gatilho

```text
Manual
Agendado por cron
Webhook
Evento de banco de dados
Fila
Listener
Upload de arquivo
Ação do usuário
Chamada de API
Agente autônomo supervisionado
```

## Checklist de implantação

```text
[ ] Ambiente de produção configurado
[ ] Variáveis de ambiente revisadas
[ ] Segredos protegidos
[ ] Logs habilitados
[ ] Monitoramento ativo
[ ] Backup configurado
[ ] Rotina de rollback definida
[ ] Teste de produção controlado
[ ] Responsável operacional definido
[ ] Documentação de operação atualizada
```

---

# 6. Modelo de arquitetura recomendado

## Arquitetura padrão para aplicações empresariais

```text
[Usuário / Operador / Cliente]
        |
        v
[Interface]
Dashboard | Portal | Chat | App | Formulário
        |
        v
[API / Backend]
Autenticação | Validação | Regras | Orquestração
        |
        v
[Serviços de Negócio]
Cálculos | Workflows | Aprovações | Notificações
        |
        v
[Camada de Dados]
PostgreSQL | Storage | Cache | Data Warehouse
        |
        v
[Integrações]
ERP | CRM | E-mail | WhatsApp | APIs externas | Webhooks
        |
        v
[Operação]
Logs | Auditoria | Alertas | Backups | Monitoramento
```

## Arquitetura recomendada por tipo de solução

### ERP interno

```text
Frontend administrativo
Backend modular
Banco relacional
Controle de permissões
Logs de auditoria
Relatórios
Integração fiscal/financeira
```

### CRM

```text
Cadastro de leads
Pipeline
Histórico de interações
Automação de follow-up
Integração com e-mail/WhatsApp
Dashboard comercial
Permissões por equipe
```

### Dashboard executivo

```text
ETL/ELT
Banco analítico
Camada de métricas
Interface visual
Filtros
Exportação
Atualização agendada
```

### Agente de IA empresarial

```text
Base de conhecimento
Regras de comportamento
Ferramentas determinísticas
Orquestrador
Memória controlada
Logs de decisão
Camada de revisão humana
```

### Automação operacional

```text
Evento de entrada
Validação
Execução determinística
Registro de log
Notificação
Fallback
Monitoramento
```

---

# 7. Fluxo geral para criação de aplicações empresariais

```text
1. Receber demanda
2. Aplicar perguntas de Visão
3. Definir escopo e fora de escopo
4. Mapear usuários e permissões
5. Definir fonte da verdade
6. Modelar entrada, processamento e saída
7. Validar integrações na fase Link
8. Desenhar arquitetura
9. Criar documentação base
10. Criar protótipo ou MVP
11. Implementar módulos determinísticos
12. Testar unidade, integração e fluxo completo
13. Refinar UX e payload
14. Configurar gatilhos de automação
15. Implantar em produção controlada
16. Monitorar logs, erros e métricas
17. Registrar decisões e mudanças
18. Evoluir por ciclos curtos
```

---

# 8. Critérios de validação e qualidade

## 8.1. Critérios funcionais

```text
[ ] O sistema entrega o resultado esperado
[ ] As regras de negócio foram implementadas
[ ] Os dados são processados corretamente
[ ] O payload final está no formato previsto
[ ] As integrações funcionam
[ ] Os usuários conseguem executar o fluxo principal
```

## 8.2. Critérios técnicos

```text
[ ] Código modular
[ ] Baixo acoplamento
[ ] Alta coesão
[ ] Testes automatizados mínimos
[ ] Logs estruturados
[ ] Tratamento de erro
[ ] Configuração por ambiente
[ ] Segredos fora do código
[ ] Documentação atualizada
```

## 8.3. Critérios de segurança

```text
[ ] Autenticação implementada
[ ] Autorização por perfil
[ ] Validação de entrada
[ ] Proteção contra injeção
[ ] Rate limit quando aplicável
[ ] Dados sensíveis protegidos
[ ] Logs sem exposição indevida de segredos
[ ] Backup e recuperação definidos
```

## 8.4. Critérios de UX

```text
[ ] Fluxo claro
[ ] Interface intuitiva
[ ] Feedback ao usuário
[ ] Mensagens de erro úteis
[ ] Dados apresentados com hierarquia
[ ] Ações principais visíveis
[ ] Layout sem poluição
```

## 8.5. Critérios operacionais

```text
[ ] Deploy documentado
[ ] Monitoramento ativo
[ ] Alerta para falhas críticas
[ ] Procedimento de rollback
[ ] Responsável definido
[ ] Changelog atualizado
[ ] Roadmap vivo
```

---

# 9. Diretrizes para automação e integração

## 9.1. Ordem preferencial de integração de dados

```text
1. API oficial
2. Exportação oficial
3. Banco ou réplica autorizada
4. Upload manual controlado
5. Conector/MCP externo registrado
6. Scraping controlado apenas quando não houver alternativa estruturada aceitável
```

## 9.2. Regras para APIs

```text
[ ] Documentar endpoint
[ ] Documentar método
[ ] Documentar autenticação
[ ] Documentar payload
[ ] Testar resposta de sucesso
[ ] Testar resposta de erro
[ ] Tratar timeout
[ ] Tratar limite de taxa
[ ] Registrar logs
[ ] Não expor tokens
```

## 9.3. Regras para webhooks

```text
[ ] Validar assinatura
[ ] Registrar evento recebido
[ ] Evitar processamento duplicado
[ ] Responder rapidamente
[ ] Processar tarefa longa em fila
[ ] Criar mecanismo de retry
[ ] Tratar payload inválido
```

## 9.4. Regras para agentes de IA

```text
[ ] Definir papel do agente
[ ] Definir ferramentas disponíveis
[ ] Definir limites de autonomia
[ ] Definir o que o agente não pode fazer
[ ] Registrar decisões relevantes
[ ] Usar ferramentas determinísticas para cálculos e ações críticas
[ ] Exigir revisão humana para ações irreversíveis ou sensíveis
```

## 9.5. Regras para scraping, quando inevitável

```text
[ ] Verificar termos de uso
[ ] Respeitar robots.txt quando aplicável
[ ] Usar allowlist de domínios
[ ] Aplicar rate limits
[ ] Limitar redirecionamentos
[ ] Prevenir SSRF
[ ] Sanitizar HTML
[ ] Bloquear execução de scripts
[ ] Registrar URL, data e método de extração
[ ] Permitir desativação imediata da fonte
[ ] Armazenar preferencialmente metadados e trechos necessários
```

---

# 10. Boas práticas de implementação

## 10.1. Planejamento

```text
[ ] Começar pelo problema, não pela tecnologia
[ ] Definir MVP
[ ] Separar escopo inicial de evolução futura
[ ] Validar restrições antes do desenvolvimento
[ ] Documentar hipóteses
```

## 10.2. Arquitetura

```text
[ ] Separar interface, negócio, dados e integrações
[ ] Evitar lógica crítica no frontend
[ ] Evitar dependência direta de fornecedor único quando possível
[ ] Criar contratos claros entre módulos
[ ] Usar filas para tarefas demoradas
```

## 10.3. Desenvolvimento

```text
[ ] Código pequeno e modular
[ ] Funções com responsabilidade única
[ ] Validação de entrada
[ ] Tipagem quando possível
[ ] Testes desde o início
[ ] Logs úteis
[ ] Tratamento explícito de erro
```

## 10.4. Banco de dados

```text
[ ] Modelagem antes da implementação
[ ] Chaves primárias claras
[ ] Índices para consultas críticas
[ ] Migrações versionadas
[ ] Auditoria para dados sensíveis
[ ] Backup testado
```

## 10.5. Segurança

```text
[ ] Nunca versionar segredos
[ ] Usar .env.example
[ ] Aplicar menor privilégio
[ ] Separar ambientes
[ ] Sanitizar entradas
[ ] Registrar acessos relevantes
```

## 10.6. Operação

```text
[ ] Deploy reproduzível
[ ] Logs centralizados
[ ] Monitoramento
[ ] Alertas
[ ] Procedimento de rollback
[ ] Rotina de manutenção
```

---

# 11. Riscos, limitações e pontos de atenção

## Risco 1 — Construir antes de entender

**Mitigação:** obrigar fase de Visão, schema de dados, fonte da verdade e critério de sucesso antes do código.

## Risco 2 — IA executando lógica crítica sem validação

**Mitigação:** separar IA de regras determinísticas. Usar scripts, serviços e validações para ações críticas.

## Risco 3 — Integrações instáveis

**Mitigação:** fase Link obrigatória com handshake, timeout, retry, logs e fallback.

## Risco 4 — Documentação desatualizada

**Mitigação:** toda mudança relevante deve atualizar `AGENTS.md`, documentos técnicos ou changelog.

## Risco 5 — Escopo crescendo sem controle

**Mitigação:** manter roadmap, backlog, fora de escopo e changelog de decisões.

## Risco 6 — Baixa adoção pelo usuário

**Mitigação:** validar UX, prototipar, coletar feedback e simplificar fluxos.

## Risco 7 — Falhas de segurança

**Mitigação:** aplicar segurança desde o início, classificar dados, limitar permissões e auditar ações.

## Risco 8 — Dependência excessiva de ferramentas externas

**Mitigação:** criar abstrações, documentar integrações e prever fallback ou substituição.

---

# 12. Modelo reutilizável do protocolo

```md
# Projeto: [Nome do Projeto]

## 1. Visão

### Problema
[Descrever problema]

### Objetivo central
[Descrever resultado esperado]

### Usuários
- [Perfil 1]
- [Perfil 2]

### Fonte da verdade
[Descrever fonte primária]

### Entrada
[Descrever dados de entrada]

### Processamento
[Descrever regras de negócio]

### Saída / Payload
[Descrever entrega final]

### Critério de sucesso
[Definir métrica ou condição objetiva]

---

## 2. Link

### Integrações necessárias

| Sistema | Tipo | Status | Credencial | Observação |
|---|---|---|---|---|

### Handshake

- [ ] API testada
- [ ] Banco testado
- [ ] Webhook testado
- [ ] Permissões validadas

---

## 3. Arquitetura

### Módulos

| Módulo | Responsabilidade | Entrada | Saída |
|---|---|---|---|

### Modelo de dados

[Inserir schema]

### Fluxo principal

1. [Passo 1]
2. [Passo 2]
3. [Passo 3]

### Regras determinísticas

- [Regra 1]
- [Regra 2]

### Agentes de IA, se aplicável

| Agente | Função | Ferramentas | Limites |
|---|---|---|---|

---

## 4. Estilo

### Interface

[Descrever telas, dashboards ou mensagens]

### UX

- [ ] Fluxo claro
- [ ] Feedback ao usuário
- [ ] Erros compreensíveis
- [ ] Métricas acionáveis

### Padrão de comunicação

[Tom, linguagem, restrições]

---

## 5. Gatilho

### Tipo de execução

- [ ] Manual
- [ ] Cron
- [ ] Webhook
- [ ] Fila
- [ ] Evento
- [ ] Agente

### Operação

- [ ] Logs
- [ ] Monitoramento
- [ ] Alertas
- [ ] Backup
- [ ] Rollback

---

## 6. Testes

### Testes mínimos

- [ ] Entrada válida
- [ ] Entrada inválida
- [ ] Regra de negócio
- [ ] Integração
- [ ] Payload final
- [ ] Permissões
- [ ] Erros esperados

---

## 7. Segurança

### Classificação dos dados

[Definir nível]

### Permissões

| Perfil | Ler | Criar | Editar | Excluir | Exportar |
|---|---|---|---|---|---|

### Controles

- [ ] Autenticação
- [ ] Autorização
- [ ] Logs
- [ ] Segredos protegidos
- [ ] Backup

---

## 8. Changelog de decisões

| Data | Autor | Decisão | Motivo | Impacto |
|---|---|---|---|---|
```

---

# 13. Conclusão estratégica

O **Protocolo VLAEG Otimizado** funciona como um framework de governança técnica e operacional para criação de aplicações empresariais. Sua principal força é impedir que projetos digitais sejam iniciados apenas pela codificação, sem clareza sobre dados, regras, integrações, segurança e operação.

A versão harmonizada consolida dois elementos essenciais:

1. **método de execução**, por meio das fases Visão, Link, Arquitetura, Estilo e Gatilho;
2. **estrutura documental permanente**, por meio de `AGENTS.md`, documentação técnica, registros de progresso, decisões arquiteturais e artefatos de operação.

Na prática, o VLAEG deve ser usado como protocolo padrão antes de iniciar qualquer novo sistema, automação ou agente empresarial. Ele permite sair de uma ideia inicial para uma solução implantável, com rastreabilidade, menor risco técnico, melhor manutenção e maior capacidade de evolução.

> **Diretriz final:** planeje pela Visão, valide pelo Link, construa pela Arquitetura, refine pelo Estilo e automatize pelo Gatilho.
