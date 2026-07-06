# 00 — Contexto Estratégico da GennomX AI

Este documento consolida a memória estratégica, conceitual e de produto da GennomX AI.

---

## 0. Correção conceitual adotada como premissa central

A **GennomX AI**, como aplicação, não deve ser confundida com a etapa final de geração de análises e relatórios.

A aplicação **GennomX AI** deve englobar principalmente:

1. **Estruturação, ingestão, normalização, enriquecimento e manutenção de um banco de dados proprietário** em life sciences.
2. **Criação, configuração e operação de um servidor MCP** próprio.
3. **Disponibilização de ferramentas MCP** para que modelos de IA host consultem o banco de dados proprietário de forma estruturada, auditável e rastreável.
4. **Dashboard e API** como interfaces operacionais de consulta, manutenção, monitoramento e governança dos dados.

A geração de análises, pareceres, landscapes, memorandos de due diligence e relatórios estratégicos será realizada por **modelos de IA host** — como ChatGPT, Claude e agentes privados — que utilizarão a GennomX AI por meio do servidor MCP.

Portanto, a GennomX AI deve ser pensada como uma **infraestrutura proprietária de dados biomédicos e competitivos com acesso inteligente via MCP**, e não como o próprio gerador final de relatórios.

---

## 1. Resumo executivo da GennomX AI

A **GennomX AI** será uma plataforma empresarial modular para estruturação e disponibilização de inteligência em biotecnologia, farmacêutica, ensaios clínicos, ativos terapêuticos, dados regulatórios, literatura científica, pipelines de drogas, targets, safety, mercado e inteligência competitiva.

O problema que a plataforma resolve é a fragmentação de informações críticas em fontes dispersas: registros de ensaios clínicos, bases regulatórias, bulas, publicações, abstracts de congressos, press releases, investor decks, sites corporativos e bases científicas. Em life sciences, decisões estratégicas exigem a integração de dados que normalmente estão separados, inconsistentes, parcialmente estruturados ou enterrados em documentos PDF, HTML e relatórios corporativos.

A proposta de valor da GennomX AI é criar um **banco de dados proprietário, continuamente atualizado e semanticamente estruturado**, capaz de ser acessado por modelos de IA por meio de ferramentas MCP. Isso permite que agentes externos façam perguntas complexas, recuperem dados rastreáveis e gerem análises com base em evidências, em vez de depender apenas de busca web genérica ou de respostas não verificáveis de LLMs.

A plataforma se diferencia de uma simples base de dados porque:

- consolida múltiplas fontes primárias e secundárias;
- mantém rastreabilidade entre dado estruturado, fonte original e trecho de evidência;
- permite consulta via dashboard, API e MCP;
- separa dado bruto, dado processado e insight gerado;
- incorpora pipelines de ingestão contínua e normalização;
- prepara os dados para uso por IA, sem transformar a própria aplicação em um chatbot;
- cria uma infraestrutura de inteligência reutilizável por diferentes modelos, agentes e fluxos analíticos.

A plataforma se diferencia de um chatbot porque o núcleo de valor está na **infraestrutura de dados e ferramentas MCP**, não na interface conversacional. Os modelos host serão consumidores da GennomX AI, e não a aplicação em si.

---

## 2. Inspiração conceitual na Gosset AI

### 2.1 Elementos da Gosset AI usados como referência

Os documentos do projeto descrevem a Gosset AI como uma plataforma de inteligência de mercado em life sciences focada em dados de ensaios clínicos e performance de fármacos, com banco proprietário de mais de 100 mil ativos, acesso via dashboard, planilhas, API e MCP, além de conectores para Claude, ChatGPT e agentes customizados.

Os elementos que servem como referência conceitual são:

- banco proprietário amplo de ativos terapêuticos;
- foco em eficácia, segurança, endpoints, desenho de ensaios e benchmarking competitivo;
- coleta de dados em publicações, pôsteres de congressos, press releases e investor decks;
- interface web para exploração de dados;
- exportação estruturada;
- API para acesso programático;
- MCP como camada de acesso para modelos de IA;
- uso de ferramentas especializadas como `find_drugs`, `search`, `fetch` e consultas por target, indicação, fase, mecanismo e status regulatório;
- posicionamento B2B para investidores, biotechs, farmacêuticas, consultorias e corporate development.

### 2.2 Elementos a adaptar para a GennomX AI

A GennomX AI deve adaptar a inspiração da Gosset para uma realidade própria:

- começar com MVP interno, não com produto SaaS externo pleno;
- priorizar fontes abertas e oficiais, sem integração inicial com bases pagas;
- incluir ANVISA e perspectiva global desde o desenho;
- ter banco e taxonomia em inglês, mas interface e relatórios em português/inglês;
- adotar Supabase/PostgreSQL como base preferencial para MVP, quando tecnicamente viável;
- construir o MCP inicialmente para uso interno com ChatGPT, Claude e agentes privados;
- tratar dashboard, MCP e API como prioridades, nessa ordem;
- permitir edição corretiva no banco, sem exigir curadoria humana prévia em todos os dados;


### 2.3 Elementos tratados apenas como inspiração, sem cópia direta

A GennomX AI não deve copiar:

- marca, identidade, interface ou linguagem comercial da Gosset;
- estrutura exata de ferramentas MCP proprietárias;
- modelo comercial específico;
- base de dados da Gosset;
- claims de cobertura não verificados;
- fluxos internos não publicados;
- nomes de funcionalidades que possam criar confusão com produto terceiro.

A Gosset deve ser tratada como **benchmark conceitual**, não como template literal.

---

## 3. Visão central da aplicação

A visão central é construir uma infraestrutura proprietária composta por quatro núcleos:

1. **Banco de dados proprietário**  
   Repositório estruturado de ativos, empresas, indicações, targets, ensaios, endpoints, resultados, eventos adversos, status regulatórios, publicações, abstracts, documentos-fonte e evidências.

2. **Ingestão contínua e pipelines de dados**  
   Conectores para APIs, exports, uploads, MCPs externos e scrapers estruturados. O fluxo deve capturar, versionar, normalizar, deduplicar, enriquecer, validar e indexar dados.

3. **Servidor MCP e ferramentas especializadas**  
   Camada que expõe dados e operações da GennomX AI a modelos host. O MCP deve retornar dados estruturados, metadados, citações, trechos de evidência e links para fontes originais.

4. **Interfaces operacionais**  
   Dashboard web para exploração, monitoramento e edição; API para acesso programático; exports para CSV/Excel/JSON quando necessário.

A geração de relatórios não é responsabilidade nuclear da aplicação. A aplicação deve fornecer os dados, ferramentas e evidências para que modelos host produzam análises fora dela.

---

## 6. Principais casos de uso

Embora os relatórios sejam gerados por modelos host, a GennomX AI deve dar suporte a casos de uso analíticos como fonte estruturada e auditável.

### 6.1 Inteligência competitiva

Permitir que modelos host consultem ativos, empresas, targets, indicações, fases, endpoints e resultados para construir landscapes competitivos.

### 6.2 Due diligence

Fornecer dados estruturados para avaliação de ativo, empresa, pipeline, risco clínico, risco regulatório, segurança, evidências e comparadores.

### 6.3 Landscape terapêutico

Organizar o universo de ativos por indicação, mecanismo, fase, sponsor, status regulatório e nível de evidência.

### 6.4 Análise de ativos

Permitir recuperação de perfil completo de um DrugAsset: mecanismo, target, indicações, estudos, resultados, aprovações, eventos adversos e documentos-fonte.

### 6.5 Comparações head-to-head indiretas

Fornecer dados estruturados para que modelos host comparem ativos, endpoints, populações e resultados, preservando limitações metodológicas.

### 6.6 Monitoramento de novidades

Detectar novas publicações, alterações em ensaios, novos abstracts, press releases, aprovações, recalls e updates regulatórios.

### 6.7 Apoio a decisões de P&D, investimento e corporate development

Disponibilizar evidências estruturadas para priorização de targets, leitura de risco/retorno, análise de pipelines, oportunidades de parceria e monitoramento de catalysts.

---

## 7. Princípios de produto

1. **Precisão antes de fluidez**  
   O valor da GennomX AI está na qualidade dos dados estruturados, não em respostas narrativas bonitas.

2. **Rastreabilidade obrigatória**  
   Todo dado relevante deve apontar para fonte, documento, trecho, data de coleta e versão.

3. **Atualização contínua**  
   Pipelines devem rodar de forma incremental, com frequência ajustada por fonte.

4. **Dados estruturados antes de respostas generativas**  
   Modelos host devem consumir dados organizados; a IA não deve inventar a estrutura.

5. **Separação entre dado bruto, dado processado e insight**  
   O banco deve preservar o material original, a versão normalizada e qualquer enriquecimento computacional.

6. **Interface premium com profundidade analítica**  
   O dashboard deve ser elegante, mas não superficial. Deve permitir filtros densos, visualizações refinadas, timelines e tabelas técnicas.

7. **Consulta em linguagem natural via MCP, não como única interface**  
   A linguagem natural será uma camada de consumo por modelos host. O dashboard e a API continuam essenciais para auditoria e operação.

8. **Respostas auditáveis**  
   Ferramentas MCP devem retornar IDs, fontes, datas, confidence score e evidências.

9. **Edição corretiva humana**  
   O MVP será automatizado, mas deverá permitir correção manual de registros quando erros forem identificados.

10. **Produto interno primeiro; comercial depois**  
    O desenho deve permitir futura comercialização por API/MCP, mas o MVP será voltado ao uso interno.

---

## 8. Princípios técnicos

1. **Arquitetura modular**  
   Separar conectores, ingestão, parsing, normalização, banco, indexação, MCP, API e dashboard.

2. **Ingestão incremental**  
   Evitar recarregar bases inteiras quando a fonte permitir delta/update.

3. **Normalização robusta**  
   Padronizar nomes de empresas, drogas, indicações, targets, fases, status e endpoints.

4. **Deduplicação e resolução de entidades**  
   Mapear sinônimos, nomes comerciais, códigos de ativos, INNs, NCT IDs, DOIs, sponsors e aliases corporativos.

5. **Versionamento de dados**  
   Manter histórico de alterações, data de ingestão, data de validade da fonte e snapshots.

6. **Observabilidade**  
   Monitorar jobs, erros, latência, alterações de schema, quebras de scraper, custos de IA e qualidade dos dados.

7. **Segurança desde o MVP**  
   Mesmo sem multiusuário avançado, o MCP deve ter token, logs, escopo de ferramentas e rate limits.

8. **Governança de fontes**  
   Toda fonte deve ter status de licença, método de acesso, frequência, limites, restrições e política de armazenamento.

9. **MCP como camada de acesso inteligente**  
   O MCP não deve ser apenas proxy de SQL. Deve expor ferramentas semânticas orientadas a tarefas.

10. **Escalabilidade pragmática**  
    Usar stack simples no MVP, mas com limites claros para migração futura.

---

## 9. Riscos e pontos de atenção

### 9.1 Licenciamento de dados

Algumas fontes abertas permitem uso amplo, outras têm restrições. Bases comerciais exigem contrato. A arquitetura deve permitir bloquear dados por fonte e por licença.

### 9.2 Scraping e termos de uso

Scraping deve ser usado somente quando não houver API/export oficial. É necessário respeitar robots.txt, termos de uso, limites de acesso, cache responsável e atribuição.

### 9.3 Qualidade dos dados

Dados clínicos e regulatórios podem ser incompletos, divergentes ou desatualizados. O banco deve registrar conflitos em vez de sobrescrevê-los sem critério.

### 9.4 Dados conflitantes entre fontes

Um ensaio pode ter status diferente no ClinicalTrials.gov, press release e publicação. A GennomX AI deve preservar múltiplas versões e indicar a fonte mais recente ou mais autoritativa.

### 9.5 Hallucination de LLMs

Modelos host podem extrapolar ou interpretar mal. As ferramentas MCP devem reduzir esse risco retornando dados estruturados, citações e limites explícitos.

### 9.6 Rastreabilidade insuficiente

Sem `SourceDocument` e `EvidenceSnippet`, o sistema vira uma base não auditável. Rastreabilidade deve ser requisito de arquitetura, não funcionalidade opcional.

### 9.7 Custos de manutenção dos conectores

APIs mudam, sites alteram HTML, congressos reorganizam plataformas. É necessário monitoramento ativo e alertas.

### 9.8 Mudanças em APIs externas

ClinicalTrials.gov, openFDA, DailyMed, EMA, Open Targets e ANVISA podem alterar schemas, limites ou formatos. Os conectores devem ser versionados e testados.

### 9.9 Segurança do MCP

MCP expõe ferramentas a modelos externos. Deve haver autenticação, autorização, rate limit, logs, allowlist de ferramentas e bloqueio de queries perigosas.

---

## 11. Premissas adotadas nesta fase

1. A plataforma será geral e multiárea desde o início.
2. O MVP será interno, mas com arquitetura preparada para API/MCP comercial no futuro.
3. As fontes prioritárias do MVP são ClinicalTrials.gov, PubMed/PMC, openFDA, DailyMed, EMA, Open Targets, abstracts de grandes congressos e ANVISA.
4. Não haverá integração inicial com bases pagas.
5. O MVP deve armazenar dados de alto nível e dados granulares de endpoints/resultados.
6. A ingestão será 100% automatizada, com possibilidade de edição humana corretiva.
7. Relatórios serão produzidos por modelos host externos à aplicação.
8. A prioridade de interface será dashboard web, MCP e API.
9. O MCP será inicialmente interno, para ChatGPT, Claude e agentes privados.
10. Banco e taxonomia devem ser preferencialmente em inglês; interface e relatórios devem ser bilíngues.
11. O dashboard deve seguir o Design System GennomX, com visual premium e profundidade analítica.
12. A estratégia de dados deve usar export/API oficial sempre que disponível; scraping será usado quando necessário, com salvaguardas legais.

---

## 12. Fontes-base consideradas

### Documentos do projeto

- `Gosset AI – Plataforma de inteligência em biotecnologia e MCP.md`
- `Contexto 1 - GennomX AI.txt`
- `Contexto 2 - GennomX AI.txt`
- `GennonX Design System Light Mode.txt`

### Fontes oficiais e técnicas consideradas para validação de arquitetura

- ClinicalTrials.gov API v2.
- openFDA API e downloads.
- DailyMed RESTful API.
- NCBI E-utilities / PubMed / PMC.
- EMA ePI Consuming API.
- Open Targets GraphQL API e data downloads.
- ANVISA Dados Abertos, Bulário Eletrônico e consultas públicas.
- MCP official documentation.
- Supabase/PostgreSQL/pgvector documentation.

---

## 13. Síntese estratégica

A GennomX AI deve ser construída como a **camada proprietária de dados e ferramentas MCP da GennomX para life sciences**.

O produto não deve tentar resolver tudo no início. O primeiro objetivo é formar um núcleo confiável de dados estruturados e rastreáveis sobre ativos, empresas, indicações, ensaios, endpoints, resultados e fontes. A partir desse núcleo, modelos host poderão gerar relatórios e análises com muito mais confiabilidade do que fariam usando apenas busca web ou memória paramétrica.

O diferencial estratégico está em três pontos:

1. **Banco proprietário curado por pipelines**, não por improvisação manual.
2. **MCP como interface nativa para IA**, não apenas API convencional.
3. **Rastreabilidade por evidência**, evitando que análises geradas por IA se tornem caixas-pretas.

---

## 14. Posicionamento: inteligência emergente como camada — 2026-06-20

A GennomX AI se posiciona como plataforma de **inteligência biomédica emergente e recente**, mas
isso é um **diferencial de camada de produto**, não um critério de seleção de fontes.

Regra estratégica:

- **O valor de "inteligência emergente" vem de recência + novidade + maturidade da evidência +
  *entity linking* cross-fonte aplicados sobre fontes confiáveis** — não de trocar o backbone
  estruturado por congressos e preprints.
- O *backbone* de fontes permanece **API-first e estruturado** (ClinicalTrials.gov, PubMed/PMC,
  openFDA, DailyMed, EMA, Open Targets, ANVISA). Essas fontes são **transversais a área
  terapêutica**, o que torna a cobertura **multiárea barata desde o início**.
- A multiplicação por área terapêutica só encarece **congressos**; por isso congressos entram em
  ondas (MVP+) e preprints entram como trilha sinalizada como preliminar.

Consequências de produto:

- A "inteligência emergente" é entregue como **scoring + alertas + views/ferramentas MCP** sobre o
  banco (ex.: `get_emerging_signals`, `compare_evidence_maturity`), não como um recorte de
  *sourcing*.
- A competição em life sciences se ganha em **normalizar, ligar (trial↔abstract↔paper↔label↔
  guideline) e datar** melhor — exatamente o que o motor bitemporal (`ADR-001`,
  `PersistenceDecisionEngine`) e o modelo de evidência (`SourceDocument`/`EvidenceSnippet`) já
  sustentam.

> Detalhamento operacional: taxonomia de maturidade da evidência, políticas de congressos/preprints
> e recorte temporal por fonte em `docs/03_FONTES_E_INGESTAO.md`; campos de scoring em
> `docs/02_MODELO_DE_DADOS.md`; decisão registrada em `docs/11_CHANGELOG_DECISOES.md`.
