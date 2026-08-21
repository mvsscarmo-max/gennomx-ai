"""Valida referencias internas: links markdown, caminhos citados em prosa e ancoras de evidencia."""
from __future__ import annotations

import re
from pathlib import Path

from _common import Report, excluded_parts, iter_markdown, read, rel

MD_LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+?)(?:\s+\"[^\"]*\")?\)")
# Caminhos citados em prosa: com barra e extensao conhecida, ou diretorio do protocolo.
PROSE_PATH = re.compile(
    r"`((?:\.agents|docs|tools|project_state)/[A-Za-z0-9_./-]+)`")
# A regex acima nao distingue arquivo de notacao pontilhada: `tools/review/
# contract.validate_artifact` e modulo e funcao Python, nao caminho, e virava
# "arquivo inexistente" dentro de um artefato selado (F-029). O ultimo segmento
# decide: sem ponto e diretorio; com ponto, so e alegacao de arquivo se o sufixo
# estiver aqui. Extensao nova em uso no repositorio entra nesta lista.
KNOWN_SUFFIXES = frozenset({
    "md", "py", "yaml", "yml", "json", "jsonl", "txt", "patch", "toml", "cfg",
    "ini", "sh", "ps1", "html", "css", "js", "ts", "tsx", "sql", "lock", "example",
})
SKIP_PREFIX = ("http://", "https://", "mailto:", "#", "data:")
# Caminhos que sao exemplo/molde por desenho, nao referencia a arquivo existente.
PLACEHOLDER = re.compile(r"<|\bWS-NNN\b|\bPLAN-NNN\b|\bT-NNN\b|\bD-NNN\b|\bF-NNN\b|\bK-NNN\b"
                         r"|\bAUD-NNN\b|\bNNN\b|\broundN\b|\*|AAAA-MM-DD|~/")
# Um documento pode declarar que seus caminhos em prosa sao ilustrativos — estrutura
# de outro repositorio, layout historico, ou destino a criar num projeto que adota o
# protocolo. A declaracao fica visivel no proprio documento, em vez de escondida numa
# lista de excecoes do validador. Links markdown continuam verificados.
ILLUSTRATIVE = re.compile(r"<!--\s*validate-links:\s*illustrative-paths\s*-->")


def is_path_claim(target: str) -> bool:
    """O token citado afirma que existe um arquivo ou diretorio com esse nome?"""
    last = target.rstrip("/").rsplit("/", 1)[-1]
    if "." not in last:
        return True
    return last.rsplit(".", 1)[1].lower() in KNOWN_SUFFIXES


def run(root: Path) -> Report:
    r = Report("links")
    scope = excluded_parts(root)
    resolved_root = root.resolve()

    for md in iter_markdown(root):
        # A copia arquivada da fonte P3 e historica: seus links descrevem outro repositorio.
        if "legacy" in md.parts or md.name == "protocolo_vlaeg_2.0.md":
            continue
        text = read(md)
        p = rel(md, root)

        for m in MD_LINK.finditer(text):
            target = m.group(2)
            if target.startswith(SKIP_PREFIX) or PLACEHOLDER.search(target):
                continue
            r.checked += 1
            if "#" in target:
                target = target.split("#", 1)[0]
            if not target:
                continue
            resolved = (md.parent / target).resolve()
            try:
                relative = resolved.relative_to(resolved_root)
            except ValueError:
                relative = None
            if relative and relative.parts and relative.parts[0] in scope.top_level:
                continue
            if not resolved.exists():
                line = text[:m.start()].count("\n") + 1
                r.error("links::broken", p,
                        f"Link para '{m.group(2)}' nao resolve.",
                        f"Corrija o caminho ou crie {target}.", line)

        if ILLUSTRATIVE.search(text):
            continue

        for m in PROSE_PATH.finditer(text):
            target = m.group(1)
            if PLACEHOLDER.search(target) or not is_path_claim(target):
                continue
            r.checked += 1
            resolved = (root / target)
            if not resolved.exists():
                line = text[:m.start()].count("\n") + 1
                r.error("links::prose-path", p,
                        f"Caminho citado '{target}' nao existe.",
                        "Documentacao que cita arquivo inexistente diverge da implementacao — "
                        "corrija o caminho ou crie o arquivo.", line)

    return r
