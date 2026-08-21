---
name: memory-privacy
description: Aplica a política de captura antes de qualquer persistência ou transmissão — exclusão por caminho, allowlist de eventos, sanitização, redação de segredo, classificação, retenção e purga. Use antes de registrar evento, exportar histórico, compartilhar contexto ou commitar, e ao suspeitar que um segredo entrou no repositório ou no ledger. Não use como substituto de DLP completo, nem para justificar captura ampla.
metadata:
  protocol: VLAEG AI Ready First
  layer: memory
  version: 1.0.0
  source: "política de captura em camadas; mecanismos de isolamento externo excluídos por norma"
  adapted: true
  risk: critical
  vlaeg_phases: [cross-cutting]
  triggers:
    - "antes de registrar evento no ledger"
    - "antes de exportar, compartilhar ou transmitir contexto"
    - "suspeita de segredo no diff, no ledger ou no histórico"
  negative_triggers:
    - "substituir DLP corporativo"
    - "justificar captura ampla por existir sanitização"
  produces: ["evento sanitizado", "relatório de redação", "D-NNN em caso de purga"]
  gates: ["G9"]
---

# Privacidade da memória

Contenção de processo está excluída deste protocolo por norma. A proteção vem de camadas verificáveis sobre **o
que é capturado**, aplicadas antes de qualquer escrita, não de contenção do processo.

## Ordem de aplicação

Sempre nesta ordem, antes de persistir ou transmitir:

1. **Exclusão por caminho** — o evento toca caminho em `ignore_paths` de `.agents/policy/capture-policy.yaml`? Descarte localmente, antes de fila, rede ou arquivo.
2. **Allowlist de tipo** — o `type` está na lista permitida (`docs/ai-ready/memory-model.md` §3)? Fora dela, descarte com anotação de perda.
3. **Sanitização** — remova conteúdo que não pertence ao registro: corpo de arquivo inteiro, dump, saída binária.
4. **Redação** — aplique os padrões de segredo, substituindo por `[REDACTED:<tipo>]`.
5. **Limite de tamanho** — trunque com marcador explícito. Truncar em silêncio é perda escondida.
6. **Classificação** — respeite o nível declarado em `PROJECT.md`.

*Concluído quando:* as seis camadas rodaram, nesta ordem, e o que foi descartado ou truncado está anotado.

## Nunca capturar

`.env` e variantes · chaves privadas (`*.pem`, `*.key`, `id_rsa*`) · `~/.ssh/`, `~/.gnupg/`,
`~/.aws/`, `~/.config/gh/` · token ou credencial de qualquer provider · dump de banco · banco local
com dado real · resposta contendo dado pessoal · URL assinada · log confidencial · qualquer caminho
sob `private/**` do projeto.

## Padrões redigidos

O catálogo executável está em `.agents/policy/capture-policy.yaml`. Cobre chave de nuvem, token de
plataforma, chave de API, JWT, bloco de chave privada e o par genérico
`senha|secret|api_key|token = valor`.

O mesmo catálogo alimenta `tools/validate_ai_ready.py`. **Acerto do validador é bloqueio**, não
aviso: um segredo detectado impede declarar qualquer trabalho concluído.

## Limitação declarada

Exclusão por caminho **não é DLP**. Ela não interpreta comando de shell arbitrário, não rastreia
conteúdo citado em texto livre e não cobre todo formato. Resolve o caso verificável, e o protocolo
declara isso em vez de prometer garantia que não tem.

Consequência prática: a proteção real contra vazamento é **não trazer o segredo para o contexto**,
não confiar na filtragem depois.

## Quando um segredo escapa

1. **Pare.** Não commite, não faça push, não continue a tarefa.
2. Rode `python tools/validate.py` para delimitar o alcance — diff, ledger, evidência, handoff.
3. Trate o segredo como **comprometido** e rotacione na origem. Remover o arquivo não desfaz a exposição; quem teve acesso, teve.
4. Purgue o registro (`memory.purge`, nível de risco 5, aprovação humana), preservando o metadado de que houve purga.
5. Registre `D-NNN` com a causa e a barreira criada para não repetir.

Remover a linha e seguir trata o sintoma — exatamente o que `no-workarounds` proíbe.

*Concluído quando:* o segredo foi rotacionado, o alcance foi delimitado, a purga está registrada e existe barreira contra recorrência.

## Isolamento

- Entre projetos: `cross_project_search: false` por padrão. Ligar exige decisão registrada, justificativa, lista explícita de projetos e data de revisão — os quatro, ou o validador reprova.
- Entre clientes ou organizações: declarado em `PROJECT.md`; vale como restrição de nível 5.
- Preferência global nunca sobrescreve política de privacidade do projeto.

## Tratamento de falhas

- **Padrão desconhecido:** se parece segredo e não casa com nenhum padrão, trate como segredo e acrescente o padrão ao catálogo. Falso positivo custa uma linha; falso negativo custa uma rotação.
- **Registro histórico com segredo descoberto tarde:** purga imediata com aprovação, preservando o metadado.
- **Purga solicitada sem aprovador disponível:** não purgue nem ignore. Isole o registro, marque `pending_gates: [G9]` e escale.

## Anti-patterns

Capturar tudo e filtrar depois · confiar que sanitização substitui não trazer o segredo · desligar
a política "só nesta sessão" · ativar busca entre projetos sem decisão · purgar sem deixar rastro
de que houve purga · tratar exclusão por caminho como garantia completa.
