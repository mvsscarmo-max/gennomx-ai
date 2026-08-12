# CLAUDE.md

Este projeto utiliza `AGENTS.md` como fonte principal de instruções para agentes de IA.

Antes de modificar código, banco de dados, documentação, pipelines, MCP, segurança ou deploy, leia:

1. `AGENTS.md`
2. `project_state/CONTEXT.md`
3. `project_state/TASKS.md` e o plano ativo citado no contexto
4. `project_state/DECISIONS.md` e `project_state/FINDINGS.md`
5. `docs/13_PROTOCOLO_VLAEG.md`
6. o documento específico da área que será alterada.

O projeto adota o **Protocolo VLAEG 2.0** (`../protocolo_vlaeg_2.0.md`, operacionalizado em `docs/13_PROTOCOLO_VLAEG.md`). O estado vivo está em `project_state/{CONTEXT,DECISIONS,TASKS,FINDINGS,PROGRESS}.md` e `project_state/plans/`.

A premissa central do projeto é que a GennomX AI é uma infraestrutura proprietária de dados biomédicos e competitivos com acesso via MCP. A geração final de relatórios é feita por modelos host externos e não deve ser implementada como núcleo da aplicação.
