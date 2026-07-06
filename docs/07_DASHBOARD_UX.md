# 07 — Dashboard, UX e Design System

## Tela de governança — 2026-06-21

A rota `/governance` exibe domínios, kill switches, limites, políticas de retenção e legal holds.
Administradores podem pausar um domínio, simular retenção ou enfileirar o ciclo real. Ativação de
domínio exige owner, finalidade, base legal, revisão de termos e robots pela API administrativa.

Este documento consolida os princípios de experiência do usuário, estrutura do dashboard e diretrizes visuais.

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

## 10.5 Estado implementado — 2026-06-20

- empresas, indicações, targets, jobs, logs MCP e segurança possuem busca/filtro,
  paginação, loading, vazio e erro consistentes;
- empresas, indicações e targets consultam catálogos persistidos, sem dados simulados;
- logs MCP e eventos de segurança são restritos a administradores e exibem apenas campos
  operacionais sanitizados;
- assets, trials, sources e overview permanecem funcionais; o overview agora contabiliza empresas;
- o modo E2E pode ignorar autenticação somente com `NODE_ENV != production` e
  `E2E_BYPASS_AUTH=true`; produção nunca aceita esse bypass;
- fontes remotas de tipografia foram removidas do build para torná-lo reproduzível/offline,
  preservando a pilha de fontes de sistema definida no design system.

## Estado implementado — 2026-07-02

- **Correção da visão geral (overview):** a entrada de 2026-06-20 acima registrava "o overview
  agora contabiliza empresas", mas o endpoint `GET /api/v1/overview` **não existia** no backend —
  `fetchServerOverviewStats` chamava uma rota inexistente e o `.catch()` da página mascarava o
  404, exibindo os 4 KPIs do topo sempre zerados em produção. Corrigido: `OverviewService`
  (`backend/app/services/overview_service.py`) agrega `total_assets`/`total_companies`/
  `total_trials`/`active_sources`/`last_ingest` em uma única query e é exposto por
  `GET /api/v1/overview`.
- **Filtro de fase de ativos:** o parâmetro `phase` era aceito pela API/serviço de ativos mas
  nunca chegava ao SQL (`asset_service.list_assets` o declarava e descartava). Corrigido —
  agora filtra por `development_stage`.
- **Vocabulário de fase incorreto no frontend (achado durante a correção acima):** os dropdowns
  de fase em `/assets` e `/trials`, e a função `phaseLabel`, usavam o vocabulário `PHASE_1`
  (com underscore), enquanto o vocabulário real gravado no banco (`phase_normalized` /
  `development_stage`) é `PHASE1` (sem underscore) — ver `ClinicalTrialsNormalizer.PHASE_MAP`.
  Isso significava que (a) o filtro de fase de **trials** também nunca funcionava, e (b) a
  legenda de fase em português ("Fase I", "Fase II"...) nunca era aplicada às linhas reais da
  tabela de trials — o código bruto (`PHASE1`) aparecia na tela em vez do rótulo traduzido.
  Corrigido em `frontend/src/lib/utils.ts` (`phaseLabel`), `assets/page.tsx` e `trials/page.tsx`.

---
