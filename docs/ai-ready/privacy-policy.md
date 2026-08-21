<!-- validate-links: illustrative-paths -->

# Privacidade e segurança da memória

Contenção de processo está excluída deste protocolo (`PROTOCOL.md` §3.1). Segurança da memória,
não. Ela vem de **camadas verificáveis sobre o que é capturado**.

## 1. Defesa em camadas

| # | Camada | Onde | Falha se |
|---|---|---|---|
| 1 | Exclusão por caminho | `capture-policy.yaml` § `ignore_paths` | o segredo chega por outro caminho |
| 2 | Allowlist de tipos de evento | política de captura | o tipo permitido carrega o segredo no corpo |
| 3 | Sanitização | antes de qualquer escrita | o padrão não está no catálogo |
| 4 | Redação de padrões | regex sobre `summary` e `detail` | segredo em formato não previsto |
| 5 | Limite de tamanho | truncamento com marcador | — |
| 6 | Classificação de dados | `PROJECT.md` § Classificação | classificação errada na origem |
| 7 | Isolamento por projeto | busca entre projetos desativada | ativação sem decisão |
| 8 | Isolamento por cliente/organização | `PROJECT.md` | — |
| 9 | Retenção | política de retenção | — |
| 10 | Purga | operação de nível 5 | — |
| 11 | Auditoria | validador de segredos | — |
| 12 | Controle de acesso | **fora do escopo do protocolo** | delegado ao repositório e ao sistema operacional |

**Limitação declarada:** exclusão por caminho **não é prevenção completa de vazamento**. Ela não
interpreta comando de shell arbitrário, não rastreia conteúdo citado em texto livre e não cobre
todo formato. Resolve o caso verificável — e o protocolo **declara isso** em vez de prometer
garantia que não tem.

Prometer proteção que não existe é pior que não ter proteção: leva a equipe a baixar a guarda.

## 2. Nunca capturar

Arquivos de ambiente · chaves privadas · diretórios de credencial do usuário (SSH, GPG, nuvem,
CLI de repositório) · tokens e credenciais de qualquer provider · dumps de banco · bancos locais
com dado real · respostas contendo dados pessoais · URLs assinadas · logs confidenciais · conteúdo
de diretórios marcados como privados no projeto.

## 3. Padrões redigidos

Substituídos por `[REDACTED:<tipo>]` **antes** de persistir. O catálogo executável vive em
`capture-policy.yaml`; ele cobre, no mínimo: chaves de nuvem, tokens de plataforma de código,
chaves de API, tokens de mensageria, JWT, blocos de chave privada, URLs assinadas e pares
credencial-valor em texto.

O validador aplica os mesmos padrões ao diff e ao ledger; **acerto do validador é bloqueio**, não
aviso.

## 4. Quando um segredo escapa

1. **Pare.** Não commite.
2. Rode o validador para delimitar o alcance.
3. Trate o segredo como **comprometido**: rotacione na origem. **Remover o arquivo não desfaz a exposição.**
4. Purgue o registro (nível 5, aprovação humana), preservando o metadado da purga.
5. Registre uma decisão com a causa e a barreira criada para não repetir.

Remover a linha e seguir trata o sintoma — exatamente o que o guardrail de causa raiz proíbe.

## 5. Escopo entre projetos

Busca entre projetos é **desativada por padrão** e não é alterável por preferência global. Ativar
exige, cumulativamente: decisão registrada · justificativa escrita · lista explícita dos projetos ·
data de revisão. Sem os quatro, o validador reprova.
