# Racionalizações e suas respostas

Leia quando a pressão estiver empurrando para a gambiarra. Cada desculpa tem resposta conhecida.

## Fundamentos

- **Jidoka (Toyota)** — a linha para quando o defeito aparece. Parar cedo é mais barato que embarcar o defeito. O sinal que você quer calar é a linha parando.
- **Quadrante de dívida (Fowler)** — dívida deliberada e prudente é uma decisão registrada com plano de pagamento. Dívida imprudente e inadvertida é o que se contrai calando sinal.
- **"Bom gosto" (Torvalds)** — a correção certa costuma **remover** o caso especial, não acrescentar mais um.
- **Janelas quebradas** — o primeiro `as any` autoriza o segundo. O custo real não é a linha; é a norma que ela cria.

## As desculpas

**"É só temporário."** — Nenhuma gambiarra é temporária sem data e canário. As cinco etapas de
contenção da válvula de escape existem justamente para tornar "temporário" verificável.

**"O prazo é hoje."** — Prazo não altera onde está a causa. Se a correção correta não cabe hoje,
o caminho é a válvula de escape com registro, não a gambiarra silenciosa. A diferença entre as
duas é o rastro.

**"O código de terceiro está errado."** — Pode estar. Isso satisfaz a condição 1 de quatro. Verifique
as outras três antes de concluir que a válvula se aplica.

**"Ninguém mais toca nesse arquivo."** — Alguém tocará, e será um agente sem sua memória. É
exatamente o cenário para o qual este protocolo foi desenhado.

**"O teste é que está errado."** — Às vezes é. Então conserte o teste **enunciando por que ele
estava errado** e o que ele deveria verificar. Enfraquecer asserção para passar não é consertar
o teste; é apagá-lo devagar.

**"Já funciona assim em produção."** — Funcionar não é estar correto. Isso torna a mudança mais
arriscada, não mais dispensável.

**"Vou abrir um registro depois."** — Depois é quando o contexto já evaporou. O registro faz parte
da correção, não do follow-up.

**"A causa raiz é grande demais."** — Então o trabalho não é a gambiarra: é dividir a causa raiz em
etapas e registrar um plano. Tamanho da causa é motivo para planejar, não para calar.
