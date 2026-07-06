# 10 — Glossário Operacional

Este documento concentra a terminologia operacional do projeto.

---

## 10. Glossário operacional

**MCP — Model Context Protocol**  
Protocolo que permite que modelos e agentes de IA acessem ferramentas, dados e sistemas externos de forma padronizada.

**Servidor MCP**  
Componente que expõe ferramentas da GennomX AI para clientes MCP, como ChatGPT, Claude e agentes privados.

**Ferramenta MCP**  
Função semântica acessível via MCP, como `search_drugs`, `find_trials` ou `fetch_source_evidence`.

**Data lake**  
Camada de armazenamento de dados brutos e semiestruturados, preservando arquivos originais e snapshots de fontes.

**Banco proprietário**  
Base estruturada da GennomX AI, construída por ingestão, normalização, deduplicação e enriquecimento de múltiplas fontes.

**ETL**  
Extract, Transform, Load. Processo em que dados são extraídos, transformados e depois carregados no banco.

**ELT**  
Extract, Load, Transform. Processo em que dados são primeiro carregados em uma camada bruta e transformados posteriormente.

**Entidade**  
Objeto estruturado do domínio, como ativo, empresa, ensaio, target, indicação ou documento.

**Ativo terapêutico**  
Medicamento, biológico, terapia celular/gênica, molécula, combinação ou candidato em desenvolvimento.

**Endpoint**  
Medida de desfecho de um estudo clínico, como ORR, PFS, OS, HbA1c, PASI, ACR20, mudança de biomarcador ou evento de segurança.

**Target**  
Alvo biológico associado a um mecanismo terapêutico, como receptor, proteína, gene, pathway ou biomarcador.

**Curadoria**  
Processo de revisão, correção, validação e enriquecimento de dados por humano ou sistema especializado.

**Conector**  
Módulo de integração com uma fonte via API, export, upload, MCP externo ou scraping.

**Scraper**  
Rotina de coleta automatizada de dados em páginas web ou documentos sem API estruturada.

**Pipeline**  
Sequência automatizada de extração, parsing, normalização, deduplicação, validação, persistência e indexação.

**Normalização**  
Padronização de nomes, campos, unidades, status, fases, entidades e formatos.

**Deduplicação**  
Identificação e fusão controlada de registros que representam a mesma entidade.

**Resolução de entidade**  
Processo de mapear aliases e identificadores diferentes para uma entidade canônica.

**Relatório de inteligência**  
Documento analítico gerado por modelo host com base nos dados e evidências acessados via GennomX AI/MCP.

**EvidenceSnippet**  
Trecho específico de uma fonte que sustenta um dado estruturado.

**SourceDocument**  
Documento original ou página coletada, como artigo, bula, press release, abstract ou PDF regulatório.

**DataSource**  
Fonte de origem, com metadados sobre tipo de acesso, licença, frequência, confiabilidade e restrições.

---
