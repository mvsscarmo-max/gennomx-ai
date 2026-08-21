## F-NNN — <o que foi descoberto, em uma frase>

**Data:** AAAA-MM-DD · **Origem:** <exploração | teste | falha | revisão | divergência doc↔código>
**Autoridade:** evidence | hypothesis · **Workstream:** WS-NNN · **Commit:** `<sha>`

**Detalhe:** <o que exatamente foi observado, com arquivo e linha quando aplicável>

**Como foi observado:** `EVIDENCE.md#E-NNN` ou o comando e a saída

**Consequência:** <o que isso muda no plano, na arquitetura ou no que se pode prometer>

**Vale além desta tarefa?** sim → candidato a `knowledge-promotion` · não

**Status:** ativo | superado por F-NNN | resolvido em T-NNN

---

<!--
Um finding registra o que foi observado, não o que se concluiu. A conclusão, quando vale além
da tarefa, passa pelo funil de knowledge-promotion.

Findings comuns que este protocolo espera ver registrados:
- limitação de API ou ferramenta descoberta na prática;
- caminho investigado e descartado (impede reexploração);
- divergência entre documentação e código (o código vence — corrija o documento);
- uso da válvula de escape de no-workarounds, com qual das quatro condições a justifica;
- gate pulado, com o motivo.

Autoridade `evidence` exige comando e saída. Sem eles, é `hypothesis`.
-->
