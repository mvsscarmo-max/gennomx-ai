# Catálogo de gambiarras (W-01…W-30)

Trinta padrões nomeados. Para cada um: o que o sinal estava dizendo e onde fica a origem real.
Consulte a categoria que disparou; não leia o catálogo inteiro.

## Evasão do sistema de tipos

**W-01 — `any` genérico.** O tipo real é desconhecido ou incômodo. Origem: modele o tipo, ou valide
na fronteira e propague o tipo validado.

**W-02 — asserção para compilar.** `x as T` sem prova de que `x` é `T`. Origem: o valor não tem a
forma prometida; corrija quem o produz ou valide antes.

**W-03 — asserção de não-nulo em valor incerto.** `x!` onde `x` pode ser nulo. Origem: torne a
ausência representável e trate-a, ou garanta a presença no construtor/consulta.

**W-04 — `object` / `Record<string, unknown>` como escape.** Apaga a forma para calar o compilador.
Origem: declare a forma; se ela varia, use união discriminada.

**W-05 — dupla asserção (`as unknown as T`).** Confissão de que a conversão é impossível. Origem:
duas representações incompatíveis; escreva a conversão explícita e testada.

## Supressão de lint e aviso

**W-06 — `eslint-disable` inline.** A regra achou algo real. Origem: corrija o apontado; se a regra
é inadequada ao repositório, desative-a **na configuração**, com motivo.

**W-07 — `@ts-ignore` / `@ts-expect-error` sem plano.** Origem: o erro de tipo é verdadeiro. Se vem
de tipagem de terceiro, escreva a declaração correta.

**W-08 — silenciar aviso de depreciação.** Origem: a API vai sumir. Migre, ou registre a migração
com prazo.

## Erro engolido

**W-09 — catch vazio.** Origem: você não sabe o que fazer com a falha — descubra. Log com contexto
e relance é o piso.

**W-10 — catch-e-default.** Devolve valor "seguro" que mascara o erro. Origem: separe "ausente"
de "falhou"; são estados diferentes.

**W-11 — catch amplo demais.** Captura o erro que você previu e mais dez que não. Origem: capture
o tipo específico.

**W-12 — `.catch(() => null)` em promessa.** Origem: mesma de W-09, agora assíncrona e mais difícil
de rastrear.

## Hacks de tempo e ciclo de vida

**W-13 — `setTimeout(fn, 0)` para acertar renderização.** Origem: dependência de ordem não
declarada. Use o gancho de ciclo de vida correto.

**W-14 — sleep arbitrário em teste.** Origem: o teste não sabe o que esperar. Espere pela
condição observável, não pelo relógio.

**W-15 — retry escondendo corrida.** Origem: duas operações sem ordem garantida. Sincronize na
origem; retry é para falha transitória de rede, não para bug de ordem.

## Monkey patch e mutação em runtime

**W-16 — extensão de protótipo.** Origem: falta uma função utilitária. Escreva-a.

**W-17 — sobrescrita de estado global.** Origem: acoplamento escondido. Injete a dependência.

**W-18 — substituir internals de biblioteca.** Origem: a biblioteca não expõe o que você precisa.
Use o ponto de extensão oficial, um wrapper, ou troque a biblioteca.

## Duplicação defensiva

**W-19 — optional chaining em tudo.** `a?.b?.c?.d` denuncia que ninguém sabe a forma do dado.
Origem: valide uma vez na fronteira.

**W-20 — cadeias de fallback.** `x ?? y ?? z ?? default` esconde qual fonte deveria valer.
Origem: declare a precedência de fontes explicitamente.

## Cópia adaptada

**W-21 — handler copiado com ajustes.** Origem: a abstração existente não serve. Extraia o
comum ou escreva código específico — não clone.

**W-22 — validação duplicada.** A mesma regra em dois lugares diverge no primeiro ajuste.
Origem: uma fonte única de verdade para a regra.

## Ambiente e build

**W-23 — variável de ambiente como feature flag permanente.** Origem: decisão adiada. Decida e
remova a flag, ou registre-a como configuração de produto com dono.

**W-24 — hack no script de build.** `|| true`, ignorar exit code, copiar arquivo à mão. Origem:
o build está errado; conserte a etapa, não a maquiagem.

## Específicas de teste

**W-25 — método só-para-teste em código de produção.** Origem: o objeto é difícil de testar
porque tem dependência escondida. Injete-a.

**W-26 — mock para não entender.** Mockar o que você não compreendeu produz teste que passa e
código que quebra. Origem: entenda o colaborador antes de simulá-lo.

**W-27 — teste marcado skip como "TODO".** Origem: um teste vermelho. Skip transforma sinal em
silêncio — é exatamente o que este guardrail proíbe.

## Arquitetura

**W-28 — objeto-deus / depósito de utilitários.** Origem: falta de fronteira. Nomeie a
responsabilidade e mova o código para ela.

**W-29 — prop drilling no lugar de estado adequado.** Origem: o estado está no nível errado.

**W-30 — feature flag que nunca expira.** Origem: dois caminhos de código mantidos para sempre.
Toda flag nasce com data de remoção.

## O padrão

Todas as trinta compartilham uma forma: **o código sabia de algo verdadeiro e foi silenciado.**
A pergunta que resolve qualquer caso não catalogado é sempre a mesma — *o que este sinal estava
tentando me dizer, e onde nasce o que ele viu?*
