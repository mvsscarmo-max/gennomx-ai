# FINDINGS - GennomX AI

## F-001 - Validação VPS não é local

O PostgreSQL alvo está em rede Docker privada. Testes locais e mocks não validam conectividade,
roles, RLS, MinIO ou fontes externas na VPS. Isso exige janela autorizada futura.

## F-002 - DRY-7 não equivale a cobertura clínica ampla

As fixtures cobrem a estrutura escolhida do ClinicalTrials.gov. Estruturas adicionais, reconciliação
com publicações e semântica clínica avançada permanecem fora do incremento.

## F-003 - Schema de adverse events tem granularidade limitada

O índice corrente existente não inclui `seriousness`. O incremento usa termo + população/grupo e
não altera schema; colisões raras entre o mesmo termo sério/não sério no mesmo grupo exigirão
revisão antes de ampliar o parser.

## F-004 - Estado antigo continha contradições de runtime

Docs vivos misturavam Supabase temporário, MinIO transitório e R2 futuro. A fonte vigente foi
reconciliada; menções Supabase restantes devem ser lidas apenas no changelog/arquivo v1.

## F-005 - Segredos já apareceram em stdout histórico

O arquivo v1 registra que `docker compose config` interpolou segredos. Não repetir; usar
`--no-interpolate` ou testes estruturais e avaliar rotação antes de produção.
