<!-- validate-links: illustrative-paths -->
# Gosset AI – Plataforma de inteligência em biotecnologia e MCP

## 1. Resumo executivo

Gosset AI é uma plataforma de inteligência de mercado em life sciences focada em dados de ensaios clínicos e performance de fármacos, combinando um data lake proprietário de mais de 100 mil ativos de medicamentos com agentes de IA e conectores MCP (Model Context Protocol) para Claude, ChatGPT e agentes customizados. A proposta central é permitir comparações head‑to‑head, mapeamento competitivo e suporte a decisões de P&D, corporate development e investimento em biotecnologia, com acesso via dashboard, planilhas, API e, de forma cada vez mais estratégica, via MCP integrado a modelos de linguagem.[^1][^2][^3][^4]

A empresa posiciona-se como alternativa mais completa que bases tradicionais como Evaluate, Cortellis, GlobalData e ClinicalTrials.gov, agregando resultados de artigos, pôsteres de congresso, investor decks e press releases em uma base estruturada que pode ser consultada de forma natural language através de agentes. Do ponto de vista técnico, a Gosset opera um MCP proprietário (mcp.gosset.ai) autenticado por token/OAuth e publica também MCPs públicos auxiliares para bases biomédicas (PubMed, bioRxiv/medRxiv, ClinicalTrials.gov, DrugBank, Open Targets), reforçando um ecossistema de agentes e conectores em biotecnologia.[^2][^3][^5][^6]


## 2. Perfil da empresa

### 2.1 Posicionamento, segmento e proposta de valor

Gosset se define como uma "life science market intelligence platform" que fornece dados de eficácia e segurança para todos os ensaios clínicos, com foco em 100.000+ ativos de drogas. O posicionamento é claro em torno de competitive intelligence, due diligence e desenho de ensaios para biotecnologia e farmacêutica, com ênfase em comparações entre drogas, benchmarks de desenho de estudo e relatórios de due diligence automatizados.[^4][^1][^2]

O segmento de atuação cobre três grandes públicos: investidores (VC, PE e mercados públicos), empresas de biotecnologia e times de corporate development em farma, todos com uso intensivo de dados clínicos e de pipeline para decisões estratégicas. O diferencial competitivo alegado é a abrangência e profundidade do banco de dados de evidência clínica, incluindo resultados não facilmente acessíveis em bases tradicionais, combinada com interfaces de IA (agentes e MCP) que retornam respostas estruturadas e acionáveis em vez de análises genéricas de LLMs generalistas.[^5][^1][^2]

### 2.2 Estágio, país de origem e sede

Os materiais públicos (site, documentação e posts de LinkedIn) indicam Gosset como um startup focado em inteligência para biotech, com forte conexão a Stanford e ao ecossistema de IA em saúde; a organização GitHub menciona sede nos Estados Unidos. Não há referência explícita a data de fundação, mas os primeiros anúncios públicos da plataforma aparecem em 2024, sugerindo uma empresa em estágio early/growth com alguns anos de curadoria de dados acumulados.[^7][^8][^5]

O site oficial e os perfis dos fundadores indicam base na Bay Area / Menlo Park, Califórnia, com advisors e investidores com forte presença em Stanford e em empresas de tecnologia em IA aplicada à saúde. Não há evidência de escritórios regionais; o modelo aparenta ser predominantemente remoto/SaaS com foco global em clientes de life sciences.[^9][^5]

### 2.3 Modelo de negócio e mercados-alvo

O modelo de negócio é claramente B2B, com monetização via acesso à plataforma (dashboard, exportações, API) e via conectores MCP/IA para uso em fluxos de trabalho de análise. Os mercados-alvo são:[^3][^2]

- Funds de venture capital, private equity e investidores em mercados públicos focados em biotecnologia.
- Empresas de biotecnologia (especialmente mid‑size) que precisam mapear competidores, benchmarkar endpoints e desenhar ensaios.
- Times de corporate development e strategy em farmacêuticas para M&A, parcerias e licensing deals.[^2][^5]

A ênfase em "head‑to‑head comparisons", "competitive landscapes" e "trial design benchmarks" no site reforça uma proposta voltada para decisões de portfólio, seleção de targets e leitura de risco/retorno de programas clínicos.[^1][^4]


## 3. Produtos e serviços

### 3.1 Visão geral das ofertas

A partir da documentação oficial e do GitHub, é possível inferir três camadas principais de oferta:

1. **Plataforma de inteligência (dashboard web)** – interface interativa para explorar doenças, pipelines, dados de eficácia/segurança e benchmarks de desenho de ensaios.
2. **Acesso programático aos dados** – via planilhas (exportações) e API proprietária.[^5][^2]
3. **Acesso via MCP/Agentes de IA** – conectores Gosset para Claude, ChatGPT (Plus/Pro, Business/Enterprise) e agentes customizados usando OpenAI Agents SDK ou outras implementações MCP.[^10][^3][^1]

Além disso, o repositório `web-research-agent` mostra o desenvolvimento de um agente de pesquisa web genérico, usado para automatizar a coleta e estruturação de informações sobre empresas de biotech, coerente com a narrativa de "AI agents" da marca.[^11]

### 3.2 Detalhamento das principais ofertas

| Oferta/Produto                            | Descrição resumida                                                                                     | Público‑alvo principal                           | Acesso                          |
|------------------------------------------|--------------------------------------------------------------------------------------------------------|-------------------------------------------------|---------------------------------|
| Plataforma web (dashboard)               | Visualização de pipelines, comparação de drogas, benchmarks de desenho de ensaios, filtros avançados. | Investidores, BI/CI em biotech, corp dev farma  | SaaS via browser.[^2]       |
| Exportações em planilha                  | Download de dados estruturados para análise offline e relatórios customizados.                        | Analistas quantitativos, consultorias           | CSV/Excel via plataforma.[^2]|
| API proprietária                         | Acesso programático completo aos dados de ensaios, drogas e endpoints.                                | Times de dados, plataformas internas            | REST/API documentada.[^2]   |
| Conector MCP para Claude                 | Acesso direto ao banco de dados da Gosset via Claude, com "unlimited results" e suporte completo MCP.| Usuários Claude Pro/Max, analistas avançados    | MCP remoto `https://mcp.gosset.ai/sse`.[^3][^12] |
| Conector MCP para ChatGPT Plus/Pro       | Conector customizado usando Developer Mode, com autenticação OAuth para acessar Gosset pela interface.| Usuários ChatGPT Plus/Pro                       | MCP remoto `https://mcp.gosset.ai/sse`.[^10] |
| Conector MCP para ChatGPT Business/Ent.  | Conector gerenciado por admin de workspace, com acesso para usuários corporativos.                    | Times enterprise em farma/biotech               | MCP remoto `https://mcp.gosset.ai/sse`.[^13] |
| Agentes customizados (OpenAI Agents SDK) | Classes e exemplos de agentes especializados em competitive intelligence e target analysis.           | Times de dados, plataformas internas, vendors   | Integração via SDK e MCP.[^3][^14] |
| MCPs públicos auxiliares (`other-public-mcps`) | Servidores MCP para PubMed, bioRxiv/medRxiv, ClinicalTrials.gov, DrugBank, Open Targets.        | Comunidade de pesquisa biomédica, devs          | Scripts Python open source.[^6] |

### 3.3 Problemas resolvidos e casos de uso

A Gosset estrutura seus casos de uso principalmente em torno de:

- **Comparação de eficácia e segurança entre drogas**: comparar candidatos em desenvolvimento com standard‑of‑care e entre si, usando endpoints como ORR, PFS, eventos adversos etc.[^8][^15]
- **Mapeamento competitivo de áreas terapêuticas**: identificar todos os programas relevantes, fases de desenvolvimento, mecanismos e players em determinada doença.[^1][^2]
- **Desenho e benchmark de ensaios clínicos**: analisar critérios de inclusão/exclusão, endpoints, regimes de dose e histórico de sucesso por desenho.[^2][^5]
- **Due diligence para investimentos e M&A**: gerar relatórios estruturados de ativos, comparar head‑to‑head e avaliar riscos regulatórios e de eficácia.[^5][^2]

Os conectores MCP ampliam esses casos permitindo que analistas e modelos de IA façam consultas em linguagem natural, como "Compare all PD‑1 inhibitors vs PD‑L1 inhibitors including their development status" ou "Show me Phase 3 EGFR inhibitors for non‑small cell lung cancer", recebendo de volta tabelas estruturadas e análises.[^10][^1]


## 4. Plataforma de inteligência de mercado via MCP

### 4.1 O que a plataforma MCP faz

A camada MCP da Gosset é um servidor de ferramentas que expõe o banco de dados de mais de 100 mil ativos de drogas diretamente para modelos compatíveis com o protocolo Model Context Protocol. O servidor remoto principal é `https://mcp.gosset.ai/sse`, acessado via SSE/HTTP no contexto do OpenAI Agents SDK e via configuração de servidor remoto no Claude e ChatGPT.[^12][^3][^10][^1]

Por meio desse MCP, agentes de IA podem listar ferramentas e chamar métodos como `find_drugs`, `search` e `fetch` para obter listas de drogas por alvo, indicação, fase, mecanismo de ação, status regulatório e outros filtros avançados. Os exemplos oficiais de uso incluem consultas por alvo (EGFR, PD‑1, BRAF), indicação (oncologia, doenças autoimunes, diabetes), fase de desenvolvimento (Phase 2, Phase 3, approved), tecnologia (mRNA, CRISPR, cell therapy) e status regulatório (breakthrough therapy, accelerated approval, priority review).[^14][^3][^1]

### 4.2 Posicionamento e utilidade prática do MCP

Do ponto de vista de produto, o MCP é apresentado como forma "AI‑first" de conectar dados estruturados da Gosset diretamente em fluxos de trabalho de modelos de linguagem, evitando limitação de web search incompleto. A utilidade prática para usuários corporativos inclui:[^3]

- Embutir consultas de inteligência em bots internos, copilotos de analistas e painéis customizados.
- Automatizar rotinas de competitive intelligence (por exemplo, monitorar todos os Phase 3 EGFR inhibitors e novos breakthrough designations em um TA).
- Permitir que analistas façam deep dives iterativos a partir de perguntas em linguagem natural, com follow‑ups e filtragens adicionais.[^3][^1]

Para pesquisadores e investidores, o ganho é transformar perguntas complexas – como "Analyze the complete competitive landscape for diabetes treatments" – em saídas estruturadas com listas de drogas, mecanismos, fases, status regulatório e diferenciais, já organizados para análise.[^1]

### 4.3 Implementação e integração do MCP

A documentação mostra integração nativa com:

- **Claude (desktop/web)**: configuração de um remote MCP server chamado "Gosset" com URL `https://mcp.gosset.ai/sse`, permitindo acesso ilimitado a resultados e uso como ferramenta em conversas.[^12]
- **ChatGPT Plus/Pro**: criação de conector customizado via Developer Mode, com autenticação OAuth e uso de Gosset como fonte em chats e em fluxos de Deep Research.[^10]
- **ChatGPT Business/Enterprise**: conector gerenciado por admin, com mesma URL MCP e OAuth, disponibilizado para usuários corporativos com botão "+ G Gosset" na interface.[^13]
- **Agentes customizados (OpenAI Agents SDK)**: instâncias de `MCPServerSse` com parâmetros de URL, timeout e cabeçalhos de autenticação, associadas a agentes especializados como `BiotechIntelligenceAgent` para competitive analysis e target analysis.[^14][^3]

Além de SSE, o guia de agentes customizados descreve um cliente MCP direto usando websockets (`wss://mcp.gosset.ai/ws`), com mensagens JSON‑RPC para `initialize`, `tools/list` e `tools/call`, sinalizando suporte a uma implementação mais completa do protocolo MCP.[^3]

### 4.4 Arquitetura operacional inferida da camada MCP

Evidências sugerem uma arquitetura em que o MCP atua como camada de orquestração entre LLMs e o data backend da Gosset:

- O cliente inicializa uma sessão MCP (`initialize`) e lista ferramentas (`tools/list`).[^3]
- Ferramentas incluiriam funções como `find_drugs` com argumentos estruturados (`query`, `limit`, filtros por fase, indicação, etc.).[^3]
- O servidor MCP traduz essas chamadas em queries contra o data warehouse da Gosset (provavelmente um banco relacional ou data lake com metadados de drogas, ensaios, endpoints, status regulatório, etc.).[^2][^3]
- A resposta retorna payloads estruturados (JSON) que o LLM usa para compor respostas analíticas e tabelas.[^1][^3]

Essa inferência é respaldada por exemplos de código com `cache_tools_list`, `max_retry_attempts`, filtros estáticos de ferramentas e uso de agentes especializados para competitive intelligence, sugerindo uma camada robusta de ferramentas internas – ainda que o schema exato das respostas não seja público.[^14][^3]


## 5. Fontes de dados, bancos de dados, APIs, integrações e mecanismos de extração

### 5.1 Fontes de dados explicitamente mencionadas

As principais pistas sobre as origens dos dados vêm da documentação e dos repositórios GitHub:

- A Gosset declara coletar dados de resultados de ensaios em **artigos científicos, pôsteres de congresso, investor decks e press releases**, buscando resultados não presentes em bases tradicionais.[^11][^2]
- A cobertura é comparada a Evaluate, Cortellis, GlobalData e ClinicalTrials.gov, indicando que o dataset próprio supera (mas não necessariamente depende diretamente de) essas fontes comerciais e da base pública de ClinicalTrials.gov.[^2]
- O repositório `other-public-mcps` expõe MCPs públicos para **PubMed, bioRxiv/medRxiv, ClinicalTrials.gov, DrugBank e Open Targets**, explicitando uso dessas fontes em fluxos de pesquisa biomédica e possivelmente em pipelines internos.[^6][^16]

### 5.2 Tabela – fontes de dados e características inferidas

| Fonte / camada                   | Evidência                          | Origem e tipo             | Método de coleta / acesso                           | Frequência / atualização (inferida)          | Finalidade analítica principal                                            | Natureza (pública/privada)        |
|----------------------------------|------------------------------------|---------------------------|-----------------------------------------------------|----------------------------------------------|---------------------------------------------------------------------------|-----------------------------------|
| ClinicalTrials.gov               | MCP público `clinicaltrials-mcp`   | Banco público de ensaios  | Acesso via API/NCT, MCP em Python.[^6]          | Atualizado conforme ClinicalTrials; provável ingestão contínua.          | Metadados de ensaios, status, desenho.                                   | Pública                           |
| Artigos científicos (PubMed)    | MCP `pubmed-mcp`; docs Gosset     | Literatura biomédica      | API PubMed via email user, MCP servidor Python.[^6][^11] | Atualização contínua, via API.               | Extração de resultados, endpoints e contexto científico.                 | Pública (acesso via NCBI)         |
| Preprints (bioRxiv/medRxiv)     | MCP `biorxiv-mcp`                  | Preprints biomédicos      | Acesso via DOIs e APIs, MCP Python.[^6][^16] | Atualização frequente conforme repositórios. | Cobrir resultados preliminares e sinais de eficácia/segurança emergentes.| Pública                           |
| DrugBank                         | MCP `drugbank-mcp`                 | Base de fármacos          | API DrugBank com chave de API no código.[^6]    | Depende de licença/limite de API.            | Dados de mecanismo, interações, características de drogas.               | Privada/licenciada                |
| Open Targets                     | MCP `opentargets-mcp`              | Alvos e associações       | API pública Open Targets via MCP.[^6]           | Atualização conforme releases.              | Mapeamento alvo‑doença, ligações droga‑alvo.                              | Pública (com termos de uso)       |
| Investor decks e press releases | Docs Gosset (resultados)           | Materiais corporativos    | Web scraping / agentes de pesquisa (`web-research-agent`).[^2][^11] | Atualização contínua via agentes.            | Capturar resultados de ensaios anunciados fora de artigos formais.       | Pública / semi‑pública            |
| Conference posters               | Docs Gosset                        | Pôsteres de congressos    | Coleta manual e/ou scraping de sites de congressos.[^2] | Provavelmente batch por conferência.         | Dados de eficácia/segurança de apresentações de congresso.               | Pública (acesso variável)         |
| ClinicalTrials.gov (próprio)    | Comparação com ClinicalTrials.gov  | Metadados de ensaios      | Ingestão além dos dados oficiais, com enriquecimento.[^2] | Atualização regular, possivelmente diária.   | Estrutura base de ensaios para cruzar com resultados de múltiplas fontes.| Pública + enriquecimento privado  |
| Banco proprietário Gosset       | Life science market intelligence   | Data warehouse consolidado| Pipelines ETL/ELT que combinam todas as fontes acima.[^2][^3] | Curadoria contínua; "quase um ano de curadoria" citado em posts.[^8] | Base principal de 100.000+ ativos, endpoints, desenhos, comparações.     | Proprietária/híbrida              |

### 5.3 Mecanismos de coleta e extração (inferência)

- **MCPs públicos como building blocks**: o repositório `other-public-mcps` sugere que a Gosset opera (ou pelo menos disponibiliza) MCPs modulares para conectar LLMs a bases clássicas de biomedicina, possivelmente tanto para uso da comunidade quanto para alimentar fluxos internos de curadoria.[^6]
- **Agentes de pesquisa web**: o `web-research-agent` demonstra um fluxo de busca Google, extração de conteúdo e estruturação em JSON conduzido por Claude 3.5 Sonnet, sugerindo que parte do enriquecimento do data lake (principalmente sobre empresas e deals) é feita por agentes automatizados com campo dinâmico.[^11]
- **Curadoria manual e semiautomática**: posts de LinkedIn mencionam "almost a year of data curation" e "AI agents that extract insights from thousands of trial sources", indicando uma combinação de pipelines automáticos com validação humana.[^15][^8]

### 5.4 Diferenciação entre fatos e inferências

- **Confirmado**: uso de ClinicalTrials.gov, PubMed, bioRxiv/medRxiv, DrugBank e Open Targets via MCPs públicos; coleta de resultados em artigos, pôsteres, investor decks e press releases; existência de um banco proprietário de >100k ativos; acesso via dashboard/planilha/API e MCP.[^6][^11][^2]
- **Inferido**: existência de um data lake relacional/colunar unificado; uso sistemático dos MCPs públicos como parte do pipeline interno (não há afirmação explícita, mas forte alinhamento técnico); frequência exata de atualização (presumivelmente contínua/batch). Essas hipóteses baseiam‑se em padrões setoriais e na arquitetura de MCP/ETL descrita.


## 6. Pessoas‑chave

### 6.1 Fundadores

**Łukasz Kidziński (Lukas Kidzinski)** – Co‑fundador da Gosset, ex‑Director of AI na Clario, pesquisador em bioengenharia e estatística na Stanford, com PhD em estatística matemática e histórico de pesquisa em biomecânica e machine learning. Kidziński também foi co‑fundador de Saliency.ai, plataforma de imagiologia médica com IA adquirida pela Clario, o que reforça experiência anterior em tradução de pesquisa em produto regulado em saúde.[^17][^9][^5]

**Kevin Thomas** – Co‑fundador da Gosset, PhD em biomedical data science por Stanford, co‑fundador da Saliency (adquirida pela Clario), onde atuou como Director of AI, com experiência em biomarcadores de imaging, biomecânica e projetos com Adidas, Philadelphia Phillies e EXOS em performance e saúde. Seu background em biomecânica, wearables e análise de dados clínicos complementa a visão de Kidziński em IA aplicada a problemas biomédicos complexos.[^9]

### 6.2 Advisors e investidores

O site lista advisors e investidores de alto perfil:

- **Scott Delp** – Professor de Bioengenharia em Stanford, figura central em biomecânica e fundador do Mobilize Center.[^5]
- **Dan Gebow** – CEO da Recombo.ai e ex‑SVP Product em Oracle Life Sciences, com experiência em produtos regulados e plataformas de dados clínicos para a indústria farmacêutica.[^5]
- **Robert Bogucki** – Diretor no Google e ex‑CEO da deepsense.ai, investidor na Gosset, trazendo experiência em IA aplicada e escala de engenharia.[^5]

### 6.3 Relação das pessoas‑chave com a estratégia da empresa

O perfil acadêmico e de produto dos fundadores e advisors reforça a estratégia da Gosset de combinar rigor científico na curadoria de dados clínicos com engenharia de IA aplicada. A experiência prévia com Saliency (IA em imagiologia médica) e com empresas de software clínico (Clario, Oracle Life Sciences) indica familiaridade tanto com requisitos regulatórios quanto com necessidades práticas de sponsors e CROs.[^9][^5]

Essa combinação de competências suporta a narrativa de um produto que vai além de web scraping simples, focando em granularidade de endpoints clínicos, critérios de elegibilidade e comparações head‑to‑head que exigem interpretação sofisticada de documentos técnicos.[^9][^2]


## 7. Parcerias, networking e relações comerciais

### 7.1 Clientes e uso no mercado

Os materiais públicos não listam explicitamente logotipos de clientes, mas a comunicação de LinkedIn enfatiza uso por "biotech investors and corporate development professionals" e exemplos de perguntas típicas de VCs, estrategistas farmacêuticos e consultores. A presença de conteúdo que analisa mercados como obesidade, IL‑15 therapeutics e PD‑1/PD‑L1, com relatórios gerados por agentes Gosset, sugere envolvimento com investidores e empresas focados nesses temas.[^16][^18][^8][^15]

### 7.2 Ecossistema MCP e integrações tecnológicas

Além dos conectores oficiais para Claude e ChatGPT, o repositório de MCPs públicos e listagens em diretórios como LobeHub e mcp.so mostram que a Gosset participa ativamente do ecossistema MCP, oferecendo servidores para múltiplas fontes biomédicas. Isso amplia o alcance da marca entre engenheiros de IA biomédica e permite que usuários combinem Gosset MCP com outros MCPs (por exemplo, PubMed) em fluxos unificados.[^19][^16][^6]

A documentação de agentes customizados traz exemplos de integração com:

- OpenAI Agents SDK.
- LangChain (via `MCPTool.from_server`).
- AutoGen.
- Websockets diretos MCP.[^3]

Isso posiciona a Gosset não apenas como um dataset, mas como infraestrutura de dados e ferramentas num stack de agentes para biotecnologia.

### 7.3 Vínculos acadêmicos e com hubs de inovação

Os perfis dos fundadores e advisors revelam fortes conexões com Stanford (Mobilize Center, Neuromuscular Biomechanics Lab), reforçando um networking intenso com a academia em biomecânica, IA e ciência de dados biomédica. Posts mencionam uso de agentes da Gosset para gerar análises complexas de targets (como CLDN18.2) e de leitura de catalysts para ações em biotecnologia, engajando a comunidade de pesquisa e investimento em torno da plataforma.[^8][^15][^17][^9]

Não há evidência explícita de parcerias formais com farmacêuticas específicas ou biotechs nomeadas; essa informação provavelmente é tratada de forma confidencial ou comunicada apenas em interações comerciais diretas.


## 8. Preços e modelo comercial

### 8.1 Evidências diretas

O site da Gosset não publica tabelas de preços nem tiers visíveis; a principal call‑to‑action é "Get product info/Book a call", com promessa de envio de "detalhes sobre features, use cases, pricing" por e‑mail. Isso indica um modelo de precificação sob consulta, típico de soluções B2B enterprise/upper‑mid market em life sciences.[^1]

A documentação e o conteúdo de onboarding reforçam a existência de acesso via dashboard, planilha, API e MCP, mas sem distinções explícitas de planos (por exemplo, "Standard", "Pro", "Enterprise"). Não são encontrados registros públicos de preços em marketplaces, App Stores ou em materiais de terceiros.[^2][^3]

### 8.2 Inferências sobre modelo comercial

Com base em padrões setoriais e na linguagem de materiais institucionais, é razoável inferir que o modelo inclui:

- **Licenças por assento ou por time** para o dashboard e exportações de dados.
- **Pacotes de API** com limites de volume e/ou escopo de dados (por ex., por TA, região, ou nível de detalhe).[^2]
- **Add‑ons enterprise** para integrações personalizadas, conectores MCP gerenciados em tenants corporativos e suporte prioritário.

A presença de conectores para ChatGPT Business/Enterprise, com configuração via administrador e disponibilidade para todos os usuários do workspace, sugere um foco em contratos corporativos com múltiplos usuários. Todavia, sem menções explícitas de valores ou tiers, qualquer suposição de ticket médio ou modelo exato de faturamento permanece como hipótese.[^13]


## 9. Evidências técnicas e arquitetura inferida

### 9.1 Stack tecnológica observável

A partir dos repositórios públicos e da documentação, é possível identificar componentes da stack:

- **Linguagem de backend MCPs públicos**: Python 100%, com scripts individuais para PubMed, bioRxiv/medRxiv, ClinicalTrials.gov, DrugBank e Open Targets.[^6]
- **Agentes de pesquisa web**: Python para orquestração, Anthropic Claude 3.5 Sonnet como LLM, integração com Google Search e parsers HTML.[^11]
- **Camada de agentes MCP**: uso do OpenAI Agents SDK, com classes `MCPServerSse`, `Agent`, `Runner` e `ModelSettings`, sugerindo backend compatível com SSE e JSON‑RPC MCP.[^3]
- **Clientes MCP alternativos**: implementação exemplo em websockets (`wss://mcp.gosset.ai/ws`) com mensagens JSON‑RPC para `initialize`, `tools/list` e `tools/call`.[^3]

### 9.2 Arquitetura de dados (inferida)

Combinando documentação de produto e exemplos técnicos, pode‑se inferir a seguinte arquitetura de alto nível:

1. **Ingestão de dados**: pipelines Python (e possivelmente outros componentes) coletam dados de ClinicalTrials.gov, PubMed, bioRxiv/medRxiv, DrugBank, Open Targets, investor decks, press releases e pôsteres.
2. **Curadoria e normalização**: agentes de IA e curadores humanos transformam textos não estruturados em estruturas padronizadas – endpoints, tempos de follow‑up, critérios de elegibilidade, regimes de dose, etc.[^11][^2]
3. **Data warehouse/lake proprietário**: base consolidada de mais de 100 mil ativos de drogas com metadados de ensaios, endpoints, status regulatório, empresas, patentes e deals.[^5][^2]
4. **Camadas de acesso**:
   - API REST e exportações em planilha.
   - Dashboard web com gráficos e tabelas filtráveis.
   - MCP server (`mcp.gosset.ai`) expondo ferramentas de query estruturada para LLMs.[^2][^3]

Essa arquitetura alinha‑se a práticas comuns em plataformas de inteligência de mercado em life sciences (Evaluate, Cortellis, GlobalData), porém com a particularidade de uma exposição MCP nativa que serve diretamente modelos generativos.

### 9.3 IA, RAG, vetorização e agentes

Embora a documentação não detalhe explicitamente uso de RAG ou vetorização interna, há fortes sinais de uma abordagem agent‑centric:

- O `web-research-agent` exemplifica agentes que iteram entre busca, leitura e estruturação, com limites configuráveis de buscas e resultados.[^11]
- A camada MCP presume que o LLM cliente decide quando chamar ferramentas (tool_choice="auto" ou "required"), reforçando um modelo de agentes orquestrados.[^3]

No entanto, não há evidência pública do uso de bancos vetoriais específicos, frameworks de RAG ou motores de busca internos; qualquer afirmação mais detalhada sobre essas escolhas seria especulativa.


## 10. Benchmark competitivo

### 10.1 Contexto e concorrentes relevantes (alto nível)

No segmento de inteligência para biotecnologia e life sciences, alguns players comparáveis incluem:

- **Evaluate Pharma** – plataforma consolidada de previsão e análise de mercado farmacêutico.
- **Clarivate Cortellis** – inteligência de pipeline clínico e farmacêutico.
- **GlobalData Healthcare** – dados de ensaios, pipelines e mercado.
- **Citeline (ex‑Informa Pharma Intelligence)** – dados de ensaios clínicos e pipelines.
- **Bases científicas/referenciais isoladas** – ClinicalTrials.gov, PubMed, DrugBank, Open Targets etc.

Essas plataformas oferecem dados estruturados e análises, mas geralmente não são desenhadas nativamente para interação via LLMs ou MCP.

### 10.2 Tabela – comparação qualitativa

| Dimensão                        | Gosset AI                                        | Evaluate / Cortellis / GlobalData (inferido)         | ClinicalTrials.gov + PubMed isolados          |
|---------------------------------|--------------------------------------------------|------------------------------------------------------|-----------------------------------------------|
| Foco principal                  | Inteligência de mercado em biotecnologia com IA  | Inteligência de mercado e forecasts farmacêuticos    | Registro de ensaios e literatura científica   |
| Cobertura de dados             | 100k+ ativos de drogas, todos ensaios, endpoints detalhados.[^2][^5] | Pipelines, forecasts, vendas, deals – foco financeiro e regulatório | Ensaios registrados; artigos individuais      |
| Fontes adicionais               | Artigos, pôsteres, investor decks, press releases.[^2][^11] | Relatórios proprietários, filings regulatórios       | Somente o que é submetido às bases            |
| Interface principal            | Dashboard, API, exportações e MCP para LLMs.[^2][^3] | Dashboards web e APIs tradicionais                  | Interfaces web e APIs públicas                |
| Integração com LLM/MCP         | Conectores oficiais para Claude e ChatGPT; SDK MCP.[^3][^10][^12] | Geralmente ausente ou limitada                      | Não há MCP nativo; uso via wrappers terceiros |
| Profundidade em endpoints      | Detalhe de eficácia/segurança em múltiplos timepoints por ensaio.[^2][^5] | Varia por fornecedor; muitas vezes agregada         | Parcial, dependente da submissão              |
| Granularidade em desenho de ensaio | Critérios estruturados de elegibilidade, desenho, SOC.[^2] | Presente, mas nem sempre completamente estruturado  | Dados de desenho muitas vezes resumidos       |
| Acesso programático            | API + MCP + planilhas                             | APIs e exportações                                   | APIs limitadas/públicas                       |
| Orientação a agentes           | Forte (MCP, exemplos de agentes customizados).[^3][^14] | Baixa                                               | Nula                                           |

### 10.3 Pontos fortes e fracos relativos

**Pontos fortes Gosset** (inferidos):

- Forte integração com IA e agentes (MCP, exemplos de agentes, conectores oficiais para Claude e ChatGPT), diferencial claro frente a concorrentes tradicionais.[^12][^10][^3]
- Foco explícito em endpoints de eficácia/segurança e desenho de ensaios, o que atende diretamente a due diligence e competitive intelligence em nível clínico.[^5][^2]
- Capacidade declarada de ir além de ClinicalTrials.gov e bases comerciais, incluindo resultados dispersos em múltiplos formatos.[^2]

**Possíveis fragilidades** (com base em lacunas públicas):

- Falta de transparência detalhada sobre modelo de preços e tiers pode ser barreira de entrada para alguns segmentos.
- Menor histórico e reconhecimento de marca em relação a Evaluate/Cortellis, que têm décadas de presença no setor.
- Dependência de conectores MCP para parte relevante do valor pode exigir maturidade técnica maior em clientes.


## 11. Lacunas, limitações e pontos que exigem validação adicional

- **Data de fundação, tamanho da equipe e base instalada de clientes**: não foram encontradas fontes públicas que detalhem esses aspectos; seria necessário obter essa informação diretamente com a empresa ou via bancos de dados privados de mercado.
- **Modelo de preços e tiers**: não há pricing público; qualquer suposição além de "sob consulta" seria especulativa. Entrevistas, RFPs ou materiais de vendas seriam necessários para quantificar ticket médio e estrutura de planos.[^1]
- **Detalhes da arquitetura interna de dados**: não há descrições técnicas completas de schema, tecnologias de armazenamento (por exemplo, Redshift, BigQuery, Snowflake) ou uso de bancos vetoriais. As inferências se baseiam em padrões setoriais e na presença de MCP/ETL em Python.[^6][^3]
- **Amplitude real de cobertura vs. Evaluate/Cortellis**: a afirmação de que a Gosset cobre dados "não disponíveis" nessas bases é qualitativa; validar quantitativamente exigiria acesso paralelo às plataformas para comparação sistemática por TA e indicador.[^2]
- **Grau de automação vs. revisão humana**: embora haja menções a quase um ano de curadoria e uso de agentes, a proporção exata de automação/human‑in‑the‑loop não é explicitada.[^15][^8]


## 12. Conclusão analítica

Gosset AI emerge como um player especializado em inteligência de mercado para biotecnologia que combina um data asset profundo de ensaios clínicos com uma camada de acesso orientada a IA via MCP, posicionando‑se à frente de concorrentes tradicionais em termos de integração com fluxos de trabalho de LLMs e agentes. A capacidade de expor dados estruturados de 100k+ ativos de drogas por alvo, indicação, fase, mecanismo e status regulatório, tanto via dashboard quanto via conectores para Claude e ChatGPT, é um diferencial relevante para fundos, biotechs e times de corporate development.[^5][^2][^3]

Do ponto de vista de due diligence técnica, porém, permanecem abertas questões sobre modelo de preços, métricas de adoção, arquitetura detalhada do data backend e a exata composição do pipeline de fontes – temas que podem ser endereçados em interações diretas com a equipe da Gosset ou em testes controlados via trial/pilotos. Para um analista corporativo ou investidor, o próximo passo lógico seria: (i) solicitar demo com foco em uma área terapêutica de interesse; (ii) testar o conector MCP em um ambiente de agente interno; e (iii) comparar a cobertura da Gosset com outras fontes já utilizadas, medindo ganhos de velocidade, completude de dados e qualidade das análises geradas.[^6][^1][^2]

---

## References

1. [MCP Usage Examples - Gosset](https://docs.gosset.ai/guide/mcp-usage-examples) - This guide provides comprehensive examples for querying Gosset's drug database through MCP connector...

2. [kidzik/other-public-mcps - GitHub](https://github.com/gosset-ai/mcps) - For accessing Gosset MCP you need an active Gosset account. Reach out to us for details. A collectio...

3. [How to use Gosset MCSs / Connectors](https://docs.gosset.ai/guide/) - Model Context Protocol (MCP) connects AI models directly to comprehensive datasets. Instead of incom...

4. [Gosset | LinkedIn](https://www.linkedin.com/company/gosset-ai) - Gosset's products inform portfolio management decisions in biotech companies, pharmaceutical compani...

5. [Gosset AI - GitHub](https://github.com/gosset-ai) - Gosset AI provides the most comprehensive biotech intelligence data in the industry. We deliver safe...

6. [README.md - Web Research Agent - GitHub](https://github.com/gosset-ai/web-research-agent/blob/main/README.md) - Biotech Consultants: Quick analysis of trial design parameters and drug efficacy results. Learn more...

7. [Receptor.AI](https://gosset.ai/companies/receptor.ai/) - Receptor.AI is a preclinical-stage TechBio company specializing in generative AI-driven drug discove...

8. [Awesome MCP Servers](https://mcp.so/zh/server/awesome-mcp-servers/TensorBlock?tab=content) - ... MCP-compatible client. gosset-ai/mcps: A suite of MCP servers enabling AI assistants to access a...

9. [Getting Started with Gosset](https://docs.gosset.ai/guide/getting-started) - - Sign up at gosset.ai; Explore Your First Disease - Search for a therapeutic area you're interested...

10. [Pending AI](https://gosset.ai/companies/pending-ai/) - Pending AI has developed an advanced artificial intelligence and quantum mechanics-enabled drug disc...

11. [Claude Connector | Gosset](https://docs.gosset.ai/guide/claude-connector) - Connection Issues ​. Ensure you have Claude Pro or Max subscription; Verify the MCP Server URL is ex...

12. [Building a better AI for biotech research | Lukas Kidzinski posted on ...](https://www.linkedin.com/posts/lukaszkidzinski_ai-biotech-clinicaltrials-activity-7317532443748487168-zouo) - Intelligence for pharma decisions. 11mo Edited ... Try it out at https://gosset.ai/ #AI #Biotech #Cl...

13. [General Inception](https://gosset.ai/companies/general-inception/) - The recent acquisition of Enable Medicine adds advanced generative AI capabilities for drug discover...

14. [gosset.ai](https://gosset.ai) - Drug intelligence. See the results. · See Gosset in action · Built by experts in AI and life science...

15. [AI agents draft analysis for biotech R&D targets, assets, results.](https://www.linkedin.com/posts/lukaszkidzinski_6months-ago-our-ai-agents-began-mapping-activity-7346138598519226368-OjOI) - Example reports: https://gosset.ai/blog/il-15-therapeutics https://gosset.ai/blog/pd1-pdl1-market · ...

16. [Introducing Gosset, a new platform for biotech investors - LinkedIn](https://www.linkedin.com/posts/lukaszkidzinski_biotech-investors-and-corporate-development-activity-7198402494765412352-481b) - We've just launched Gosset, the platform that provides insights about biotech assets. Try our demo h...

17. [Gosset](https://docs.gosset.ai) - GossetLife Science Market Intelligence with AI. AI agents that analyze 100,000+ drug assets and deal...

18. [Łukasz Kidziński](https://kidzinski.com) - Łukasz Kidziński is a co-founder of Saliency.ai, a medical imaging platform, and a researcher in the...

19. [Kevin Thomas](https://kevinthomas.ai) - Kevin Thomas ... Kevin is a co-founder of Gosset, a platform that helps biotech investors and pharma...

