"""Utilitarios compartilhados da verificacao (D-064).

G13 (`tools/verify.py`) e a fase RC (`build_prompt.py`) reusam estes helpers.
"""
from __future__ import annotations

import re
import subprocess
import unicodedata
from pathlib import Path

SHA = re.compile(r"^[0-9a-fA-F]{7,40}$")


def fold(text: str) -> str:
    """Chave de comparacao insensivel a acento, caixa e forma Unicode."""
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(stripped.casefold().split())


def normalize(text: str) -> str:
    """Forma canonica para leitura. NFC + CRLF→LF."""
    return unicodedata.normalize("NFC", text.replace("\r\n", "\n"))


def split_frontmatter(text: str) -> tuple[str, str]:
    """Devolve (frontmatter, corpo). Frontmatter vazio quando ausente."""
    text = normalize(text)
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 3)
    if end == -1:
        return "", text
    return text[3:end], text[end + 4:]


def scalar(fm: str, key: str) -> str | None:
    """Le um escalar do frontmatter, aceitando continuacao indentada."""
    m = re.search(rf"^{re.escape(key)}:[ \t]*(.*)$", fm, re.M)
    if not m:
        return None
    parts = [m.group(1).strip()]
    rest = fm[m.end():]
    if rest.startswith("\n"):
        rest = rest[1:]
    for line in rest.splitlines():
        if not line.strip():
            break
        if re.match(r"^\S+:", line):
            break
        parts.append(line.strip())
    return " ".join(p for p in parts if p).strip()


def parse_status_paths(status: str) -> list[str]:
    """Extrai paths de `git status --short` (suporta rename `->`)."""
    out: list[str] = []
    for line in status.splitlines():
        if len(line) < 4:
            continue
        rest = line[3:]
        if " -> " in rest:
            rest = rest.split(" -> ", 1)[1]
        path = rest.strip().replace("\\", "/")
        if path:
            out.append(path)
    return out


def _meta_estado_paths(ws_dir_name: str) -> frozenset[str]:
    """Estado operacional da WS — sujo nao conta como codigo sob revisao."""
    base = f"project_state/workstreams/{ws_dir_name.strip('/')}"
    return frozenset({
        f"{base}/STATE.md",
        f"{base}/EVIDENCE.md",
        f"{base}/EVENTS.jsonl",
        "project_state/WORKSTREAMS.md",
    })


def substantive_dirty_paths(status: str, *, ws: str,
                            path_filters: list[str] | None = None,
                            reviewed_files: list[str] | None = None) -> list[str]:
    """Paths sujos no escopo revisado, excluindo meta-estado da propria WS."""
    reviewed = {p.replace("\\", "/") for p in reviewed_files or []}
    filters = [f.replace("\\", "/") for f in path_filters or []]
    meta = _meta_estado_paths(ws)
    out: list[str] = []
    for path in parse_status_paths(status):
        if path in meta:
            continue
        if reviewed and path in reviewed:
            out.append(path)
            continue
        if filters:
            if any(path == f or path.startswith(f.rstrip("/") + "/") or f in path
                   for f in filters):
                out.append(path)
            continue
        if not reviewed:
            out.append(path)
    return out


def git_diff_name_only(root: Path, a: str, b: str) -> list[str] | None:
    """Paths tocados em a..b. None = git falhou (fail-closed)."""
    proc = subprocess.run(
        ["git", "-C", str(root), "diff", "--name-only", f"{a}..{b}"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if proc.returncode != 0:
        return None
    return [line.replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()]
