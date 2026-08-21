#!/usr/bin/env python3
"""Valida metadados de uma skill local contra a spec agentskills.io e o contrato
do Protocolo VLAEG AI Ready First.

Auxiliar SOMENTE LEITURA. Nao altera nenhum arquivo.

Uso:
    python .agents/skills/priority/writing-skills/scripts/validate_metadata.py --path <dir-da-skill>
    python .agents/skills/priority/writing-skills/scripts/validate_metadata.py --name x --description "..."

Saida: stdout descritivo no sucesso, stderr acionavel na falha, exit 1 em erro.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FIRST_PERSON = {"eu", "meu", "minha", "nos", "nosso", "nossa", "voce", "seu", "sua",
                "i", "me", "my", "we", "our", "you", "your"}
REQUIRED_META = ["protocol", "layer", "version", "risk", "vlaeg_phases",
                 "triggers", "negative_triggers", "produces", "gates"]
LAYERS = {"priority", "memory", "protocol", "coordination", "project"}
RISKS = {"low", "medium", "high", "critical"}
PHASES = {"V", "L", "A", "E", "G", "cross-cutting", "not-applicable"}
FORBIDDEN = re.compile(r"\b(sandbox|ai-jail|yolo)\b", re.IGNORECASE)


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 3)
    if end == -1:
        return "", text
    return text[3:end], text[end + 4:]


def scalar(fm: str, key: str) -> str | None:
    """Le um escalar de topo do frontmatter, suportando blocos > e |."""
    m = re.search(rf"^{key}:[ \t]*(>-|>|\|-|\|)?[ \t]*(.*)$", fm, re.M)
    if not m:
        return None
    if m.group(1):
        lines = []
        for line in fm[m.end():].splitlines():
            if line.strip() and not line.startswith((" ", "\t")):
                break
            lines.append(line.strip())
        return " ".join(x for x in lines if x).strip()
    return m.group(2).strip().strip("'\"")


def meta_block(fm: str) -> str:
    m = re.search(r"^metadata:[ \t]*$", fm, re.M)
    if not m:
        return ""
    out = []
    for line in fm[m.end():].splitlines():
        if line.strip() and not line.startswith((" ", "\t")):
            break
        out.append(line)
    return "\n".join(out)


def validate(name: str, description: str, meta: str, dirname: str | None) -> list[str]:
    errors: list[str] = []

    if not name:
        errors.append("NAME ERROR: campo 'name' ausente no frontmatter.")
    else:
        if not 1 <= len(name) <= 64:
            errors.append(f"NAME ERROR: '{name}' tem {len(name)} caracteres; use 1-64.")
        if not NAME_RE.match(name):
            errors.append(
                f"NAME ERROR: '{name}' invalido. Use minusculas, numeros e hifens simples; "
                "sem hifens consecutivos e sem hifen no inicio ou fim.")
        if dirname and name != dirname:
            errors.append(
                f"NAME ERROR: 'name' ({name}) difere do diretorio ({dirname}). "
                "Devem ser identicos.")

    if not description:
        errors.append("DESCRIPTION ERROR: campo 'description' ausente.")
    else:
        if len(description) > 1024:
            errors.append(
                f"DESCRIPTION ERROR: {len(description)} caracteres; o limite e 1024.")
        found = FIRST_PERSON.intersection(re.findall(r"\b\w+\b", description.lower()))
        if found:
            errors.append(
                f"STYLE ERROR: descricao usa primeira/segunda pessoa {sorted(found)}. "
                "Escreva em terceira pessoa ('Autora...', 'Remove...').")
        low = description.lower()
        if "use " not in low and "use ao" not in low:
            errors.append("TRIGGER ERROR: descricao sem gatilho positivo ('Use ao...').")
        if "nao use" not in low.replace("ã", "a").replace("ã", "a") and "don't use" not in low:
            errors.append("TRIGGER ERROR: descricao sem gatilho negativo ('Nao use para...').")

    if not meta:
        errors.append("METADATA ERROR: bloco 'metadata:' ausente. "
                      f"Campos exigidos: {', '.join(REQUIRED_META)}.")
    else:
        for key in REQUIRED_META:
            if not re.search(rf"^\s+{key}:", meta, re.M):
                errors.append(f"METADATA ERROR: campo 'metadata.{key}' ausente.")
        layer = scalar(meta, r"\s+layer")
        if layer and layer not in LAYERS:
            errors.append(f"METADATA ERROR: layer '{layer}' invalida; use {sorted(LAYERS)}.")
        risk = scalar(meta, r"\s+risk")
        if risk and risk not in RISKS:
            errors.append(f"METADATA ERROR: risk '{risk}' invalido; use {sorted(RISKS)}.")
        ver = scalar(meta, r"\s+version")
        if ver and not re.match(r"^\d+\.\d+\.\d+$", ver):
            errors.append(f"METADATA ERROR: version '{ver}' nao e semver (x.y.z).")
        phases = re.search(r"^\s+vlaeg_phases:\s*\[(.*?)\]", meta, re.M)
        if phases:
            for p in [x.strip().strip("'\"") for x in phases.group(1).split(",") if x.strip()]:
                if p not in PHASES:
                    errors.append(
                        f"METADATA ERROR: fase VLAEG '{p}' invalida; use {sorted(PHASES)}.")

    hit = FORBIDDEN.search(f"{description}\n{meta}")
    if hit:
        errors.append(
            f"POLICY ERROR: termo proibido '{hit.group(0)}' nos metadados. "
            "Sandbox, ai-jail e YOLO estao excluidos por norma do protocolo.")

    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--path", help="diretorio da skill contendo SKILL.md")
    ap.add_argument("--name")
    ap.add_argument("--description")
    args = ap.parse_args()

    if args.path:
        skill_dir = Path(args.path)
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            print(f"PATH ERROR: {skill_file} nao existe.", file=sys.stderr)
            return 1
        fm, _ = split_frontmatter(skill_file.read_text(encoding="utf-8"))
        if not fm:
            print(f"FRONTMATTER ERROR: {skill_file} nao tem frontmatter YAML.", file=sys.stderr)
            return 1
        errors = validate(scalar(fm, "name") or "", scalar(fm, "description") or "",
                          meta_block(fm), skill_dir.name)
        target = str(skill_file)
    elif args.name and args.description:
        errors = validate(args.name, args.description, "", None)
        errors = [e for e in errors if not e.startswith("METADATA ERROR")]
        target = args.name
    else:
        print("USAGE ERROR: informe --path <dir> ou --name e --description.", file=sys.stderr)
        return 1

    if errors:
        print(f"FALHA: {target}", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print(f"OK: metadados validos em {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
