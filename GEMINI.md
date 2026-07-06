# GEMINI.md

Este projeto utiliza `AGENTS.md` como fonte principal de instruções para agentes de IA.

Antes de modificar código, banco de dados, documentação, pipelines, MCP, segurança ou deploy, leia:

1. `AGENTS.md`
2. `README.md`
3. `docs/00_CONTEXTO_ESTRATEGICO.md`
4. `docs/01_ARQUITETURA.md`
5. `docs/13_PROTOCOLO_VLAEG.md` e `project_state/task_plan.md`
6. o documento específico da área que será alterada.

O projeto adota o **Protocolo VLAEG** (`protocolo_vlaeg_otimizado.md`, operacionalizado em `docs/13_PROTOCOLO_VLAEG.md`): planeje pela Visão, valide pela conectividade (Link) antes da lógica, construa pela Arquitetura, refine pelo Estilo e automatize pelo Gatilho. O estado de execução vivo está em `project_state/`.

A premissa central do projeto é que a GennomX AI é uma infraestrutura proprietária de dados biomédicos e competitivos com acesso via MCP. A geração final de relatórios é feita por modelos host externos e não deve ser implementada como núcleo da aplicação.
