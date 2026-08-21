# FINDINGS - GennomX AI

## F-001 - Validação VPS não é local
**Autoridade:** evidence


O PostgreSQL alvo está em rede Docker privada. Testes locais e mocks não validam conectividade,
roles, RLS, MinIO ou fontes externas na VPS. Isso exige janela autorizada futura.

## F-002 - DRY-7 não equivale a cobertura clínica ampla
**Autoridade:** evidence


As fixtures cobrem a estrutura escolhida do ClinicalTrials.gov. Estruturas adicionais, reconciliação
com publicações e semântica clínica avançada permanecem fora do incremento.

## F-003 - Schema de adverse events tem granularidade limitada
**Autoridade:** evidence


O índice corrente existente não inclui `seriousness`. O incremento usa termo + população/grupo e
não altera schema; colisões raras entre o mesmo termo sério/não sério no mesmo grupo exigirão
revisão antes de ampliar o parser.

## F-004 - Estado antigo continha contradições de runtime
**Autoridade:** evidence


Docs vivos misturavam Supabase temporário, MinIO transitório e R2 futuro. A fonte vigente foi
reconciliada; menções Supabase restantes devem ser lidas apenas no changelog/arquivo v1.

## F-005 - Segredos já apareceram em stdout histórico
**Autoridade:** evidence


O arquivo v1 registra que `docker compose config` interpolou segredos. Não repetir; usar
`--no-interpolate` ou testes estruturais e avaliar rotação antes de produção.

## Achados P0.4 refeita (2026-08-12, tip 3bbfa56)

- F-GXAI-001 atualizado: tip limpo apos commit do WIP.
- F-GXAI-002 fechado no tip: CONTEXT/TASKS/DECISIONS versionados.
- F-GXAI-006: Platform Auth + warehouse locais; VPS/R2 pendentes.
- F-GXAI-007: Supabase frontend removido no tip.
- Parecer vigente: project_state/audits/parecer-p04-estrutura-fronteiras.md

## F-006 — Validador 4.0: sandbox historico, credential-pair e links residuais Sandbox de agente, ai-jail e YOLO estão excluídos por D-044; a menção neste parágrafo é isolamento de produto, histórico ou finding, não adoção.

**Data:** 2026-08-21 | **Status:** ativo | **Autoridade:** evidence | **Impacto:** 22 erros apos marcar arquivos de arquivo como illustrative-paths
**Workstream:** WS-001 / T-012

Mencoes a sandbox de scraper/teste em docs de produto, sem contexto de exclusao D-044 no mesmo paragrafo. Hits credential-pair em codigo de env. Nove links residuais (protocolo_vlaeg_2.0.md e similares). Isolamento de scraper nao e ai-jail; a redacao precisa declarar a exclusao.
