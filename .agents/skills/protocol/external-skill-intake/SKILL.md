---
name: external-skill-intake
description: Audita uma skill externa antes do primeiro uso — existência, versão, scripts, dependências, licença, risco e compatibilidade — e registra o veredito de aprovação no catálogo. Use antes de executar qualquer skill que não seja local e aprovada, e ao reavaliar skill cujo commit de origem mudou. Não use para skills locais do protocolo, nem para aprovar por semelhança de nome sem leitura.
metadata:
  protocol: VLAEG AI Ready First
  layer: protocol
  version: 1.0.0
  risk: high
  vlaeg_phases: [cross-cutting]
  triggers:
    - "primeira utilização de skill externa"
    - "skill com approval_status not-evaluated ou experimental"
    - "commit de origem de skill aprovada mudou"
  negative_triggers:
    - "skills locais do protocolo"
    - "aprovar por semelhança de nome"
  produces: ["entrada auditada em external-skills.yaml", "F-NNN de risco quando aplicável"]
  gates: ["G8", "G9"]
---

# Intake de skill externa

Uma skill externa é código e instrução de terceiro entrando no seu fluxo de trabalho. Ela **nunca**
roda porque o nome parece relevante.

## Estados de aprovação

| Estado | Pode executar | Significa |
|---|---|---|
| `approved` | sim | auditada, com data e commit registrados |
| `experimental` | sim, escopo limitado e resultado validado | auditada, ainda sem uso consolidado |
| `not-evaluated` | **não** | catalogada, nunca auditada — estado padrão |
| `blocked` | **nunca** | reprovada; o motivo fica registrado |
| `deprecated` | não | substituída; o sucessor fica registrado |

## Procedimento

**Passo 1 — Existência e versão.** Confirme que a skill existe na origem declarada e capture o
`source_commit` exato. "Última versão" não é versão.

*Concluído quando:* origem e commit estão fixados.

**Passo 2 — Leitura do `SKILL.md`.** Leia **integralmente**. Verifique: o que ela faz, quando não
deve ser usada, que artefatos produz, que estado altera.

*Concluído quando:* você consegue enunciar em uma frase o que ela altera no repositório.

**Passo 3 — Auditoria de scripts.** Leia **todo** arquivo em `scripts/`. Procure especificamente:

- escrita fora do diretório de trabalho;
- comando destrutivo (`rm -rf`, `git reset --hard`, `git push --force`, `DROP`);
- chamada de rede e para onde;
- leitura de arquivo sensível (`.env`, `~/.ssh`, credencial);
- execução de conteúdo baixado;
- variável de ambiente lida e transmitida.

Qualquer um destes sem justificativa clara no `SKILL.md` → `blocked`, com o motivo registrado.

*Concluído quando:* todo script foi lido e os seis pontos foram verificados.

**Passo 4 — Dependências.** Liste binários, serviços e credenciais exigidos. Dependência de
binário externo não instalado torna a skill inutilizável — registre em vez de descobrir na hora do
uso. Dependência que exige credencial é elevação automática de risco.

**Passo 5 — Licença.** Registre a licença. Ausência de licença é `blocked` para uso em projeto de
cliente.

**Passo 6 — Risco.** Classifique:

| Risco | Critério |
|---|---|
| `low` | só leitura e orientação; nenhum script mutante |
| `medium` | escreve arquivos no repositório, escopo previsível |
| `high` | executa comando de sistema, rede, ou altera configuração |
| `critical` | toca segredo, produção, dado real ou é irreversível |

**Passo 7 — Compatibilidade.** A stack bate? A skill contradiz alguma regra em `docs/rules/` ou
decisão ativa? Contradição → `blocked` até haver decisão substituta.

**Passo 8 — Registro.** Preencha a entrada em `.agents/registry/external-skills.yaml` com
`approval_status`, `last_audited_at`, `source_commit` e `content_hash`.

*Concluído quando:* a entrada está completa e o commit auditado está registrado.

## Execução após aprovação

1. Registre a seleção no `STATE.md` da workstream, com motivo, gatilho e saída esperada.
2. **Limite o escopo**: caminhos explícitos, sem permissão ampla de escrita.
3. **Valide a saída** contra o esperado antes de aceitá-la. Saída de skill externa é hipótese até verificada.
4. Grave o evento `skill_selected` com nome, versão e commit.

## Atualização

Atualização automática é **desativada**. Mudar o `source_commit` de uma skill aprovada é decisão
(`D-NNN`) e exige novo intake: o conteúdo mudou, e a auditoria anterior valia para o conteúdo
anterior.

`content_hash` divergente do registrado → a skill foi alterada fora do processo. Trate como
`not-evaluated` e reaudite.

## Tratamento de falhas

- **Origem inacessível:** não use. Registre `F-NNN`; skill inacessível não vira aprovada por conveniência.
- **Script ilegível ou ofuscado:** `blocked`. Código que não se deixa auditar não passa no intake.
- **Skill útil mas com um script perigoso:** `blocked` como pacote; se o valor justificar, extraia o procedimento para uma skill local, citando a origem.

## Anti-patterns

Executar por semelhança de nome · aprovar sem ler os scripts · aprovar "temporariamente" sem
registro · deixar `not-evaluated` em uso · atualizar commit sem reauditar · instalar o catálogo
inteiro.
