"""Helpers compartilhados da verificacao independente.

`contract.py` reune o que G13 e o gerador de prompt da RC precisam ler do mesmo
jeito: dobra de acento e caixa, normalizacao de texto, leitura de frontmatter e
inspecao do diff. Sao utilitarios, nao politica.

O gerador de prompt e o runner do revisor NAO fazem parte deste Kit: dependem da
ferramenta e dos modelos disponiveis em cada projeto. Ver reference/excluded.md.
"""
