"""Load and apply the repository's canonical capture redaction policy."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


POLICY = Path(".agents") / "policy" / "capture-policy.yaml"


class CapturePolicyError(RuntimeError):
    """Politica de captura ausente ou invalida no caminho de persistencia."""


def load_redaction_patterns(root: Path) -> list[tuple[str, re.Pattern[str]]]:
    """Padroes de redacao declarados pelo projeto.

    Politica ausente devolve lista vazia, e NAO uma excecao: quem reporta a
    ausencia e a verificacao dedicada (`ai-ready::capture-missing`), com caminho
    e acao. Estourar aqui matava o validador antes de ele conseguir dizer o que
    faltava — o usuario recebia um traceback no lugar do diagnostico.
    """
    path = root / POLICY
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    if "redaction_patterns:" not in text:
        return []
    block = text.split("redaction_patterns:", 1)[1].split("redaction_allowlist_files:", 1)[0]
    matches = re.findall(r'^\s*- name:\s*([^\s]+)\s*\n\s*pattern:\s*("(?:[^"\\]|\\.)*")', block, re.M)
    if not matches:
        raise ValueError(f"no redaction patterns found in {path}")
    return [(name, re.compile(json.loads(pattern))) for name, pattern in matches]


def require_redaction_patterns(root: Path) -> list[tuple[str, re.Pattern[str]]]:
    """Padroes para persistencia e transmissao. Falha fechada se a politica faltar.

    O validador usa `load_redaction_patterns` para diagnosticar ausencia. Quem
    escreve evento, log ou payload nao pode herdar essa tolerancia: sem padroes,
    a escrita passaria texto cru (AUD-001 R-01).
    """
    path = root / POLICY
    if not path.is_file():
        raise CapturePolicyError(f"capture policy missing: {path}")
    text = path.read_text(encoding="utf-8")
    if "redaction_patterns:" not in text:
        raise CapturePolicyError(f"redaction_patterns missing in {path}")
    patterns = load_redaction_patterns(root)
    if not patterns:
        raise CapturePolicyError(f"no redaction patterns in {path}")
    return patterns


def load_redaction_allowlist(root: Path) -> set[str]:
    path = root / POLICY
    if not path.is_file() or "redaction_allowlist_files:" not in path.read_text(encoding="utf-8"):
        return set()
    text = path.read_text(encoding="utf-8")
    block = text.split("redaction_allowlist_files:", 1)[1].split("# Camada 5", 1)[0]
    return {json.loads(value) for value in re.findall(r'^\s*-\s*("(?:[^"\\]|\\.)*")', block, re.M)}


def redact_text(value: str, patterns: list[tuple[str, re.Pattern[str]]]) -> tuple[str, list[str]]:
    redactions: list[str] = []
    for name, pattern in patterns:
        value, count = pattern.subn(f"[REDACTED:{name}]", value)
        if count:
            redactions.extend([name] * count)
    return value, redactions


def redact_value(value: Any, patterns: list[tuple[str, re.Pattern[str]]]) -> Any:
    if isinstance(value, str):
        return redact_text(value, patterns)[0]
    if isinstance(value, list):
        return [redact_value(item, patterns) for item in value]
    if isinstance(value, dict):
        return {key: redact_value(item, patterns) for key, item in value.items()}
    return value
