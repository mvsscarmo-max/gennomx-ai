---
id: AUD-002
status: vigente
tipo: revisao-de-ciclo
ws: WS-003
engine: opencode/openai/gpt-5.6-sol
independence: cross-LLM — cursor/grok-4.6 → opencode/openai/gpt-5.6-sol
commit: 60eaf628746397d977596fe79373197f8e8d8ef0
patch_sha256: be53bcf76e31ab89fc7d9592b9a80272dbfc1846a0fa392da1ab2f82436403ef
verdict: FIX_BEFORE_SHIP
findings: 2
---

# AUD-002 — Revisao de Ciclo · WS-003

## Diagnostico

A mecanica assinada esta verde no SHA avaliado, os pisos e pinos de `aiohttp` e `cryptography` conferem, e o tip de `origin/main` (`2fa5e84`) tem o run `33584535995` concluido com todos os jobs verdes, inclusive Security Scan. O lock do protocolo acompanha a normalizacao LF e nao encontrei segredo, teste enfraquecido ou mudanca fora do escopo declarado. A entrega, porem, nao esta pronta para fechamento: dois overrides globais do frontend fecham o audit substituindo versoes por outras que ficam fora das faixas explicitamente exigidas por seus consumidores. `npm ci`, lint, build e E2E verdes nao restauram esses contratos, pois o mecanismo de override deliberadamente prevalece sobre a resolucao semantica.

## Achados

### R-01 — Override global rebaixa `brace-expansion` atraves de uma major incompatível
- **Severidade:** alta
- **Tipo:** defeito
- Classe: contrato
- Arquivo: frontend/package.json:44
- Problema: o override global fixa todo `brace-expansion` em `1.1.18`. Com isso, o lock removeu a instancia `5.0.7` que existia na base e passou a atender `minimatch@10.2.5`, que declara `brace-expansion@^5.0.5` em `frontend/package-lock.json:1513-1521`, com a unica instancia `1.1.18` de `frontend/package-lock.json:2311-2319`. O override cruza quatro majors e viola o contrato do consumidor.
- Por que importa: o objetivo de fechar o audit nao autoriza trocar uma dependencia transitiva por uma major fora da faixa aceita. O override mascara a incompatibilidade para o resolvedor; o lint verde cobre apenas os caminhos executados e nao prova paridade da API e da semantica de expansao. Isso contraria G4 e a regra de corrigir a causa raiz sem silenciar o sinal.
- Correcao sugerida: restringir o override ao ramo vulneravel 1.x, preservando uma versao corrigida 5.x para consumidores que exigem `^5.0.5`; regenerar o lock e repetir `npm ci`, audit, lint, typecheck, build e E2E antes de recomputar G13.

### R-02 — Override de `sharp` escolhe versao excluida pelo Next instalado
- **Severidade:** alta
- **Tipo:** defeito
- Classe: contrato
- Arquivo: frontend/package.json:45
- Problema: o override fixa `sharp@0.35.3`, mas `next@15.5.25` declara `sharp@^0.34.3 || ^0.35.4` em `frontend/package-lock.json:4857-4884`. O lock confirma a instalacao forçada de `0.35.3` em `frontend/package-lock.json:5912-5915`, versao que nao satisfaz nenhum dos dois ramos aceitos pelo framework.
- Por que importa: a arvore instala e pode construir porque overrides prevalecem sobre a faixa transitiva, nao porque a combinacao seja suportada. A suite nao exerce otimizacao de imagens, e a ausencia atual de uso de `next/image` nao transforma uma dependencia opcional incompatível em contrato valido para o framework.
- Correcao sugerida: remover o override ou fixa-lo em uma versao corrigida que tambem satisfaca a faixa do Next, como o ramo `0.35.4` ou superior compativel; regenerar o lock e repetir os gates frontend antes de recomputar G13.

## Paridade de contrato

| Campo do contrato | Esperado | Entregue | Confere |
|---|---|---|---|
| Objetivo | `origin/main` com Security Scan verde e sem as CVEs de `aiohttp`/`cryptography` do run antigo | `origin/main` em `2fa5e84`; run `33584535995` verde, incluindo Security Scan | sim |
| Escopo Python | Pisos em `pyproject.toml` e `_lock_requirements.in`; pinos no lock | `aiohttp>=3.14.3`, `cryptography>=50.0.0`; lock em `3.14.3` e `50.0.1` | sim |
| Escopo overlay/EOL | Lock do overlay alinhado aos bytes LF e checkout fixado | `.gitattributes` fixa LF; lock atualizado; validacao protocol assinada 26/0 | sim |
| Escopo frontend | `package.json` e lock corrigem o audit sem regressao de contrato | Audit e CI verdes, mas overrides de `brace-expansion` e `sharp` violam faixas dos consumidores | nao |
| Escopo de estado | Indice, plano, estado, ledger e evidencia da WS atualizados | Artefatos existem, ligam T-014...T-017 ao PLAN-004 e mantem G14 pendente | sim |
| Push e conferencia GitHub | Mudanca no origin e run GitHub conferido | `origin/main` contem a janela; runs `33584290345` e `33584535995` verdes | sim |
| Etapa T-014 | Subir `aiohttp` e `cryptography` na origem e no lock | Pisos e pinos entregues | sim |
| Etapa T-015 | Alinhar overlay a LF e validar protocolo | Entregue com CI e fatia protocol verdes | sim |
| Etapa T-016 | Fechar npm audit e mypy/numpy no runner 3.12 | Gates verdes, mas remediacao npm deixa dois contratos transitivos invalidos | nao |
| Etapa T-017 | G13 verde, RC e G14 humano | G13 assinado verde; esta auditoria entrega a RC; G14 permanece corretamente posterior e humano | n/a |
| Criterio `aiohttp` | Lock declara `aiohttp==3.14.3` | `backend/requirements.lock:7` | sim |
| Criterio `cryptography` | Lock declara `cryptography==50.0.1` | `backend/requirements.lock:34` | sim |
| Criterio G13 | G13 verde no tip | 33 verificacoes, 0 erros, 1 aviso do artefato `_inflight`, assinado no SHA auditado | sim |
| Fora de escopo | Sem deploy, ingestao real ou arquivos R2 do checkout paralelo | Nenhum desses itens aparece na janela | sim |

## O que nao consegui verificar

Nao reexecutei `tools/validate.py` nem `tools/verify.py`, conforme proibicao do prompt; usei as saidas assinadas do SHA auditado. A CI existente nao prova o comportamento de `minimatch` em todos os padroes nem a otimizacao de imagens do Next sob as versoes forcadas, e nao tratei a ausencia desses exercicios como prova de compatibilidade. G14 ainda nao pode ser verificado porque deve ocorrer depois desta RC e ser assinado pelo responsavel humano.
