"""Validate the provider-neutral coordination foundation."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from _common import Report, read, strip_yaml_comment, yaml_scalar_value
from coordination.filesystem import CAPABILITY_STATUS, LOCK_TIMEOUT_SECONDS, FilesystemProvider

# Artefatos que a extensao exige independentemente de quais providers existem.
REQUIRED = [
    ".agents/coordination/README.md",
    ".agents/coordination/contract.yaml",
    ".agents/coordination/config.example.yaml",
    ".agents/coordination/providers.yaml",
    ".agents/coordination/capabilities.yaml",
    ".agents/coordination/authority.yaml",
    ".agents/coordination/routing.yaml",
    ".agents/coordination/ids.yaml",
    # O provider de filesystem e a referencia e o fallback: sem ele nao ha modo
    # degradado, e modo degradado e o piso de conformidade do protocolo.
    ".agents/providers/filesystem/adapter.yaml",
    "tools/coordination/filesystem.py",
    "tools/coordination_cli.py",
    "tools/setup_harness.py",
    ".gitignore",
]

# Providers alem do de referencia sao declarados pelo projeto, nao fixados aqui:
# gravar o nome de um fornecedor no validador transformaria uma escolha local em
# requisito do protocolo.
def declared_providers(root: Path) -> list[str]:
    registry = root / ".agents" / "coordination" / "providers.yaml"
    if not registry.is_file():
        return []
    names: list[str] = []
    inside = False
    for line in read(registry).splitlines():
        if line.startswith("providers:"):
            inside = True
            continue
        if inside:
            if line[:1] not in {" ", "\t"} and line.strip():
                break
            match = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)
            if match:
                names.append(match.group(1))
    return names


SCHEMAS = {
    "provider", "agent", "presence", "message", "acknowledgment", "work", "claim",
    "conflict", "approval", "evidence", "common", "thread", "handoff", "review",
    "error", "capabilities", "runtime-event",
}
STATUSES = {"supported", "partially_supported", "emulated", "unsupported", "unverified"}


def yaml_list_block(text: str, heading: str, child_indent: int) -> list[str]:
    lines = text.splitlines()
    start = next((index for index, line in enumerate(lines) if line.strip() == f"{heading}:"), None)
    if start is None:
        return []
    result: list[str] = []
    for line in lines[start + 1:]:
        indent = len(line) - len(line.lstrip())
        if line.strip() and indent < child_indent:
            break
        match = re.match(rf"^\s{{{child_indent}}}-\s+([a-z0-9_.-]+)\s*$", line)
        if match:
            result.append(match.group(1))
    return result


def capability_matrix(text: str) -> dict[str, list[str]]:
    lines = text.splitlines()
    start = next((index for index, line in enumerate(lines) if line.strip() == "capability_status:"), None)
    result = {status: [] for status in STATUSES}
    if start is None:
        return result
    current: str | None = None
    for line in lines[start + 1:]:
        indent = len(line) - len(line.lstrip())
        if line.strip() and indent < 2:
            break
        status = re.match(r"^\s{2}([a-z_]+):(?:\s*\[\])?\s*$", line)
        if status:
            current = status.group(1)
            continue
        item = re.match(r"^\s{4}-\s+([a-z0-9_-]+)\s*$", line)
        if current in result and item:
            result[current].append(item.group(1))
    return result


def yaml_scalars(text: str) -> dict[tuple[str, ...], list[str]]:
    values: dict[tuple[str, ...], list[str]] = {}
    stack: list[tuple[int, str]] = []
    for raw in text.splitlines():
        line = strip_yaml_comment(raw)
        if line is None:
            continue
        match = re.match(r"^(\s*)([a-zA-Z0-9_-]+):\s*(.*?)\s*$", line)
        if not match:
            continue
        indent, key, value = len(match.group(1)), match.group(2), match.group(3)
        while stack and stack[-1][0] >= indent:
            stack.pop()
        path = tuple(item[1] for item in stack) + (key,)
        if value:
            parsed = yaml_scalar_value(value)
            if parsed is not None:
                values.setdefault(path, []).append(parsed)
        else:
            stack.append((indent, key))
    return values


def run(root: Path) -> Report:
    report = Report("coordination")

    # Coordenacao Multi-Harness e EXTENSAO OPCIONAL do protocolo: um projeto
    # conforme opera com um agente por vez, sem esta camada. Exigir os artefatos
    # de quem nao a adotou produziria 32 erros por uma escolha legitima — e
    # validador que reprova escolha legitima deixa de ser lido.
    #
    # Adotada a camada, tudo abaixo volta a ser obrigatorio: meia adocao e pior
    # que nenhuma, porque anuncia uma garantia que nao existe.
    if not (root / ".agents" / "coordination").is_dir():
        report.checked += 1
        return report

    for relative in REQUIRED:
        report.checked += 1
        if not (root / relative).is_file():
            report.error(
                "coordination::required-file", relative, "Required coordination artifact is missing.",
                "Restore the versioned contract or implementation file.",
            )

    schema_root = root / ".agents" / "coordination" / "schemas"
    for name in sorted(SCHEMAS):
        path = schema_root / f"{name}.schema.json"
        relative = path.relative_to(root).as_posix()
        report.checked += 1
        if not path.is_file():
            report.error("coordination::schema-missing", relative, "Canonical schema is missing.", "Add the versioned JSON Schema.")
            continue
        try:
            value = json.loads(read(path))
        except json.JSONDecodeError as exc:
            report.error("coordination::schema-json", relative, f"Invalid JSON: {exc}", "Repair the schema JSON.")
            continue
        if value.get("$schema") != "https://json-schema.org/draft/2020-12/schema" or "$id" not in value:
            report.error(
                "coordination::schema-version", relative, "Schema lacks the canonical draft or ID.",
                "Declare JSON Schema 2020-12 and a stable $id.",
            )
        for reference in re.findall(r'"\$ref"\s*:\s*"([^"#]+\.schema\.json)', read(path)):
            report.checked += 1
            if not (schema_root / reference).is_file():
                report.error(
                    "coordination::schema-reference", relative,
                    f"Schema references missing file: {reference}.", "Restore the referenced schema.",
                )

    taxonomy_path = root / ".agents" / "coordination" / "capabilities.yaml"
    capabilities = set(yaml_list_block(read(taxonomy_path), "capabilities", 2)) if taxonomy_path.is_file() else set()
    # Os providers vem do registro do projeto; "filesystem" entra sempre por ser a
    # referencia executavel contra a qual a paridade e medida.
    for provider in dict.fromkeys(["filesystem", *declared_providers(root)]):
        adapter_path = root / ".agents" / "providers" / provider / "adapter.yaml"
        report.checked += 1
        if not adapter_path.is_file():
            report.error(
                "coordination::provider-adapter-missing",
                f".agents/providers/{provider}/adapter.yaml",
                f"Provider '{provider}' is declared in providers.yaml but has no adapter.",
                "Add the adapter, or remove the provider from providers.yaml.",
            )
            continue
        matrix = capability_matrix(read(adapter_path))
        adapter_text = read(adapter_path)
        classified = [item for values in matrix.values() for item in values]
        report.checked += 1
        status_keys_once = all(
            len(re.findall(rf"^\s{{2}}{status}:", adapter_text, re.M)) == 1 for status in STATUSES
        )
        if set(classified) != capabilities or len(classified) != len(set(classified)) or not status_keys_once:
            report.error(
                "coordination::capability-matrix", adapter_path.relative_to(root).as_posix(),
                "Provider must classify every canonical capability exactly once.",
                "Complete the five status lists without omissions or duplicates.",
            )
        if provider == "filesystem":
            report.checked += 1
            if matrix != CAPABILITY_STATUS:
                report.error(
                    "coordination::capability-runtime-parity", adapter_path.relative_to(root).as_posix(),
                    "Filesystem adapter differs from executable capability discovery.",
                    "Keep adapter.yaml and FilesystemProvider capability statuses identical.",
                )
            report.checked += 1
            lock_timeout = yaml_scalars(adapter_text).get(("limits", "lock_timeout_seconds"))
            if lock_timeout != [f"{LOCK_TIMEOUT_SECONDS:g}"]:
                report.error(
                    "coordination::lock-timeout-parity", adapter_path.relative_to(root).as_posix(),
                    "Filesystem adapter lock timeout differs from the executable provider.",
                    "Keep lock_timeout_seconds aligned with LOCK_TIMEOUT_SECONDS.",
                )

    contract_path = root / ".agents" / "coordination" / "contract.yaml"
    if contract_path.is_file():
        active = set(yaml_list_block(read(contract_path), "filesystem_active", 4))
        report.checked += 1
        if active != set(FilesystemProvider.SUPPORTED_OPERATIONS):
            report.error(
                "coordination::operation-runtime-parity", contract_path.relative_to(root).as_posix(),
                "Filesystem active operations differ from the executable provider binding.",
                "Classify active and reserved operations against SUPPORTED_OPERATIONS.",
            )

    config_path = root / ".agents" / "coordination" / "config.example.yaml"
    if config_path.is_file():
        config = read(config_path)
        scalars = yaml_scalars(config)
        expectations = {
            ("coordination", "enabled"): ("false", "coordination disabled by default"),
            ("coordination", "provider", "preferred"): ("compozy", "Compozy preferred"),
            ("coordination", "provider", "active"): ("filesystem", "filesystem active"),
            ("coordination", "provider", "fallback"): ("filesystem", "filesystem fallback"),
            ("coordination", "worktrees", "required_for_parallel_writes"): ("true", "worktrees required"),
            ("coordination", "memory", "provider_events_are_normative"): ("false", "provider events non-normative"),
            ("coordination", "ide", "extension_required"): ("false", "IDE extension optional"),
            ("coordination", "sandbox", "enabled"): ("false", "sandbox excluded"),
            ("coordination", "sandbox", "required"): ("false", "sandbox cannot be required"),
        }
        for path, (expected, description) in expectations.items():
            report.checked += 1
            if scalars.get(path) != [expected]:
                report.error(
                    "coordination::safe-default", config_path.relative_to(root).as_posix(),
                    f"Missing safe default: {description}.", "Restore the approved default configuration.",
                )

    providers_path = root / ".agents" / "coordination" / "providers.yaml"
    if providers_path.is_file():
        providers = read(providers_path)
        for marker in ["preferred: compozy", "active_default: filesystem", "fallback: filesystem"]:
            report.checked += 1
            if marker not in providers:
                report.error(
                    "coordination::provider-registry", providers_path.relative_to(root).as_posix(),
                    f"Provider registry lacks '{marker}'.", "Keep Compozy preferred and filesystem active/fallback.",
                )

    compozy_path = root / ".agents" / "providers" / "compozy" / "adapter.yaml"
    if compozy_path.is_file():
        compozy = read(compozy_path)
        for marker in [
            "approval_status: approved-for-spike", "operational_status: experimental",
            "required: false", "auto_update: false", "public_interfaces_only: true",
            "installed: false", "verified_locally: false",
        ]:
            report.checked += 1
            if marker not in compozy:
                report.error(
                    "coordination::compozy-gate", compozy_path.relative_to(root).as_posix(),
                    f"Compozy adapter lacks '{marker}'.", "Do not promote an unverified provider.",
                )

    ignore_path = root / ".gitignore"
    if ignore_path.is_file():
        ignored = read(ignore_path)
        for marker in [".coordination/", ".claude/skills/", ".compozy/skills/", "__pycache__/"]:
            report.checked += 1
            if marker not in ignored:
                report.error(
                    "coordination::transient-ignore", ".gitignore", f"Missing transient rule: {marker}",
                    "Keep runtime and generated aliases outside Git.",
                )

    try:
        completed = subprocess.run(
            ["git", "ls-files", ".coordination/**", ".claude/skills/**", ".compozy/skills/**", "**/__pycache__/**", "*.pyc"],
            cwd=root, capture_output=True, text=True, check=False,
        )
        report.checked += 1
        deleted = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=D"], cwd=root,
            capture_output=True, text=True, check=False,
        )
        tracked = set(completed.stdout.splitlines())
        pending_deletions = set(deleted.stdout.splitlines()) if deleted.returncode == 0 else set()
        remaining = sorted(tracked - pending_deletions)
        if completed.returncode == 0 and remaining:
            report.error(
                "coordination::transient-tracked", remaining[0],
                "Transient coordination or generated artifacts are tracked.",
                "Remove them from the Git index and keep the ignore rules.",
            )
        elif completed.returncode == 0:
            for probe in [".coordination/probe", ".claude/skills/probe", ".compozy/skills/probe", "tools/__pycache__/probe.pyc"]:
                ignored = subprocess.run(
                    ["git", "check-ignore", "--no-index", "-q", probe],
                    cwd=root, capture_output=True, check=False,
                )
                report.checked += 1
                if ignored.returncode != 0:
                    report.error(
                        "coordination::transient-ignore", ".gitignore", f"Runtime path is not ignored: {probe}",
                        "Add an effective non-negated ignore rule.",
                    )
    except OSError:
        completed = None

    if completed is None or completed.returncode != 0:
        report.warn(
            "coordination::git-unavailable", ".", "Could not inspect tracked transient files.",
            "Run the validator inside a Git worktree for the full gate.",
        )

    return report
