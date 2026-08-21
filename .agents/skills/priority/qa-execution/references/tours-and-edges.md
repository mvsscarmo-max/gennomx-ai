# Tours e casos de borda

## Tours

Um tour é um **tema** que guia a atenção durante a caminhada. Um tour por charter. A pergunta a
cada ação: *isso importaria para o tema deste tour?*

| Tour | Tema | Melhor superfície |
|---|---|---|
| **Guia turístico** | percorrer o caminho feliz destacado pelo produto | onboarding, tela inicial |
| **Colecionador** | acionar toda saída possível de uma tela | listagem, relatório, filtro |
| **Bairro perigoso** | visitar as áreas com mais bugs no histórico | módulo com mais registros em `bugs/` |
| **Madrugada** | o que acontece depois de muito tempo parado, sessão expirada, aba antiga | qualquer fluxo autenticado |
| **Sabotador** | fazer de propósito o que não deveria dar certo | formulário, upload, pagamento |
| **Obsessivo** | repetir a mesma ação muitas vezes, clicar duas vezes, voltar e refazer | ação com efeito colateral |
| **Supermodelo** | só a superfície: alinhamento, truncamento, estado vazio, texto longo | toda tela |
| **Turista de fuso** | mudar idioma, fuso, formato de número | data, moeda, agendamento |
| **Antiquário** | dado antigo, registro legado, conta criada há muito tempo | listagem, migração |
| **Mochileiro** | rede ruim, offline, reconexão | qualquer coisa que salva |

## Casos de borda

Escolha de 5 a 10 compatíveis com a superfície e a persona. **Tentado-e-limpo também é evidência** —
registre o que foi tentado, não só o que quebrou.

**Entrada** — campo vazio · só espaços · texto muito longo · emoji e acento · aspas e apóstrofo ·
HTML e script colados · número negativo · zero · valor no limite exato · casas decimais além do
esperado.

**Estado** — recarregar no meio · voltar pelo navegador · duas abas na mesma ação · sessão expirada
durante o preenchimento · clicar duas vezes em enviar · fechar e reabrir · desfazer depois de salvar.

**Dado** — lista vazia · exatamente um item · muitos itens (paginação) · registro apagado por outro
usuário durante a edição · registro sem campo opcional · caractere que quebra ordenação.

**Rede** — lenta · queda no meio do envio · resposta duplicada · timeout · voltar online.

**Permissão** — usuário sem acesso ao recurso · acesso revogado durante a sessão · link direto para
recurso alheio.

## Anti-patterns

Rodar todos os tours em toda jornada · escolher bordas que sempre passam · registrar só o que
quebrou · deixar o tour virar exploração sem caixa de tempo.
