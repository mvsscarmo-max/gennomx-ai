# Diagnóstico de carregamento — quando o agente ignora as referências

Uma skill cujas referências o agente não lê comporta-se como uma skill mais curta e mais burra.
O defeito quase nunca está no arquivo de referência; está na **redação do ponteiro**.

## Sintomas

| Sintoma | Provável causa |
|---|---|
| O agente executa o passo sem os detalhes que só a referência traz | ponteiro fraco, sem condição de disparo |
| O agente cita a referência mas erra o conteúdo | leu o nome, não o arquivo — ponteiro sem "integralmente" |
| A referência é lida só às vezes | ponteiro condicional ambíguo ("se necessário", "quando fizer sentido") |
| A referência é lida sempre e infla o contexto | material devia estar inline, ou o ponteiro é forte demais para conteúdo opcional |
| O agente inventa o conteúdo da referência | arquivo órfão: citado no corpo mas com caminho errado |

## Escada de força do ponteiro

Do mais fraco ao mais forte. Suba um degrau por vez e reteste.

1. `veja references/x.md` — menção. O agente raramente carrega.
2. `consulte references/x.md para detalhes` — sugestão. Carrega às vezes.
3. `leia references/x.md quando <condição>` — condicional nomeada. Carrega quando a condição bate.
4. `leia references/x.md integralmente antes de <ação>` — obrigatório com momento definido.
5. `PARE. Leia references/x.md integralmente antes de prosseguir.` — barreira dura. Reserve para o caso em que agir sem o arquivo produz dano.

O degrau 5 gasta autoridade: usado em tudo, deixa de significar algo. Um ou dois por skill.

## Correções, nesta ordem

1. **Corrija o caminho.** Confirme que o arquivo existe e que o caminho funciona a partir da raiz do repositório. Um ponteiro quebrado é a causa mais comum e a mais barata de eliminar. `python tools/validate_links.py` acha todos.
2. **Nomeie a condição.** Troque "se necessário" pela condição observável real ("quando qualquer categoria de sinal disparar").
3. **Suba o degrau.** Aplique "integralmente" e um momento ("antes de escolher a correção").
4. **Reduza o alvo.** Referência gigantesca desencoraja leitura. Divida por ramo: cada ponteiro aponta o pedaço que aquele ramo precisa.
5. **Traga inline.** Se todo ramo precisa do material e ele é curto, ele não devia estar fora. Divulgação progressiva é para o que só alguns ramos alcançam.
6. **Inverta.** Se o material é essencial e curto, deixe inline e empurre para a referência o que é opcional — em vez de forçar o carregamento do essencial por ponteiro.

## Checklist de reparo

- [ ] Todo caminho citado existe e resolve da raiz do repositório.
- [ ] Todo ponteiro nomeia sua condição de disparo.
- [ ] Ponteiros que devem sempre disparar dizem "integralmente".
- [ ] No máximo dois ponteiros de barreira dura (`PARE`) na skill.
- [ ] Nenhum arquivo empacotado está órfão.
- [ ] Nenhuma referência excede o que aquele ramo realmente precisa.
- [ ] Após a correção, a skill foi reexecutada e o carregamento foi observado, não presumido.
