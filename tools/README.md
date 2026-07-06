# tools/ — Scripts determinísticos (VLAEG)

Scripts utilitários atômicos, testáveis e sem efeitos colaterais, conforme a Etapa 0 e a
Camada 3 (ferramentas determinísticas) do Protocolo VLAEG (`../docs/13_PROTOCOLO_VLAEG.md`).

Princípios:

- pequenos e atômicos;
- entrada e saída bem definidas;
- read-only por padrão (sem escrita no banco);
- com tratamento de erro explícito;
- reutilizáveis pela aplicação e por CI/pre-flight.

## Scripts

| Script | Fase VLAEG | Função |
|---|---|---|
| `handshake.py` | L — Link | Executa `BaseConnector.healthcheck()` de cada conector registrado e imprime a matriz Link. Exit code ≠ 0 se alguma fonte falhar. |

## Uso

```bash
python tools/handshake.py     # ou: make handshake
```

> Ao adicionar um novo conector, registre-o em `get_registered_connectors()` (em `handshake.py`)
> e atualize a matriz Link em `../docs/03_FONTES_E_INGESTAO.md`.
