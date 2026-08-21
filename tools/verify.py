#!/usr/bin/env python3
"""G13 — Verificação diferencial determinística (PLAN-024 / D-064).

Oito detectores sobre a janela ``base_commit..HEAD``. Nada é selado nem fixado a
SHA: se o tip andar, roda de novo. Saída no padrão dos validadores (arquivo,
linha quando aplicável, regra, o que fazer).

    python -X utf8 -B tools/verify.py
    python -X utf8 -B tools/verify.py --ws WS-009
    python -X utf8 -B tools/verify.py --base <sha> --head <sha>

Plugado em ``tools/validate.py`` como passo ``g13`` (só WS com G13 em pending_gates).
"""
from __future__ import annotations

import argparse
from fnmatch import fnmatchcase
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    Report, core_paths, print_report, read, read_ledger, rel, split_frontmatter,
    yaml_list, yaml_scalar,
)
from capture_policy import load_redaction_allowlist, load_redaction_patterns  # noqa: E402
from review.contract import (  # noqa: E402
    fold, git_diff_name_only, normalize, parse_status_paths,
)
from validate_state import (  # noqa: E402
    TASK_RE,
    _evidence_blocks,
    _evidence_commit,
    _evidence_contract,
)

DETECTORS = (
    "escopo",
    "teste-enfraquecido",
    "comportamento-sem-teste",
    "sinal-silenciado",
    "ledger-append-only",
    "paridade-de-contrato",
    "evidência",
    "segredos",
)

BACKTICK_CONTENT = re.compile(r"`([^`\r\n]+)`")
ROOT_FILE = re.compile(r"(?:\.[A-Za-z0-9_.-]+|[A-Za-z0-9_.-]+\.[A-Za-z0-9_.-]+)")

WEAKEN_ADDED = re.compile(
    r"(?:\.skip\b|@pytest\.mark\.skip|@unittest\.skip|"
    r"\bxit\s*\(|\bxdescribe\s*\(|\bit\.only\b|\bdescribe\.only\b|"
    r"\btest\.only\b|\bfdescribe\b|\bfit\s*\()",
    re.I,
)
ASSERT_LINE = re.compile(
    r"\b(?:assert\b|self\.assert\w+|expect\s*\(|\.to(?:Be|Equal|StrictEqual|"
    r"Contain|Match|Throw)\b)",
    re.I,
)
SILENCE_ADDED = re.compile(
    r"(?:except\s*:|except\s+Exception\s*:|"
    r"catch\s*\([^)]*\)\s*\{\s*\}|catch\s*\{\s*\}|"
    r"#\s*noqa\b|#\s*type:\s*ignore|@ts-ignore|@ts-nocheck|"
    r"eslint-disable(?:-next-line)?|"
    r"\|\|\s*true\b|2\s*>\s*/dev/null)",
    re.I,
)
ESCAPE_NOTE = re.compile(r"GAMBIARRA:|\bF-\d{3}\b|válvula de escape|valvula de escape", re.I)
# noqa de layout flat em tools/ (import após sys.path) — não é a classe G4.
IMPORT_LAYOUT_NOQA = re.compile(
    r"^\s*(?:from\s+\S+\s+import|import\s+)\b.*#\s*noqa:\s*(?:E402|WPS433)\b",
    re.I,
)
TOP_LEVEL_DEF = re.compile(r"^(?:async\s+)?def\s+(\w+)|^class\s+(\w+)", re.M)
SOURCE_SUFFIX = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx"}
TEST_NAME = re.compile(r"(?:^|/)(?:test_|.*_test\.|.*\.test\.|.*\.spec\.)", re.I)
CRITERION_LINE = re.compile(
    r"^- \[( |x)\] (.+?)\s*(?:→|->)\s*comando:\s*`([^`]+)`",
    re.M | re.I,
)


def _git(root: Path, *args: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=timeout,
    )


def _git_ok(root: Path, *args: str, timeout: int = 30) -> str | None:
    try:
        proc = _git(root, *args, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout.strip() if proc.returncode == 0 else None


def _rev_parse(root: Path, ref: str) -> str | None:
    return _git_ok(root, "rev-parse", "--verify", f"{ref}^{{commit}}")


def find_workstream(root: Path, ws_id: str | None = None) -> Path | None:
    ws_root = root / "project_state" / "workstreams"
    if not ws_root.is_dir():
        return None
    dirs = sorted(d for d in ws_root.iterdir() if d.is_dir())
    if ws_id:
        matches = [d for d in dirs if d.name.startswith(ws_id)]
        return matches[0] if len(matches) == 1 else None
    active: list[Path] = []
    for d in dirs:
        state = d / "STATE.md"
        if not state.is_file():
            continue
        fm, _ = split_frontmatter(read(state))
        if yaml_scalar(fm, "status") == "active":
            active.append(d)
    return active[0] if len(active) == 1 else None


def window_paths(root: Path, base: str, head: str) -> list[str] | None:
    """Paths tocados em base..head. None = git falhou (fail-closed)."""
    return git_diff_name_only(root, base, head)


def _diff_text(root: Path, base: str, head: str, path: str | None = None) -> str | None:
    args = ["diff", "--no-ext-diff", "-U0", f"{base}..{head}"]
    if path:
        args.extend(["--", path])
    try:
        proc = _git(root, *args)
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode not in (0, 1):
        return None
    return proc.stdout


def _show_text(root: Path, rev: str, path: str) -> str | None:
    try:
        proc = _git(root, "show", f"{rev}:{path}")
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def _plan_path(root: Path, plan_id: str | None) -> Path | None:
    if not plan_id:
        return None
    plans = root / "project_state" / "plans"
    matches = sorted(plans.glob(f"{plan_id}-*.md")) if plans.is_dir() else []
    return matches[0] if len(matches) == 1 else None


def _task_rows(body: str) -> dict[str, tuple[bool, str, int, str]]:
    """tid -> (done, rest, line, state_token)."""
    out: dict[str, tuple[bool, str, int, str]] = {}
    for match in TASK_RE.finditer(body):
        done = match.group(1) == "x"
        tid = match.group(2)
        rest = match.group(3)
        line = body[:match.start()].count("\n") + 1
        state_m = re.search(r"`([^`]+)`\s*$", rest)
        state = state_m.group(1) if state_m else ""
        out[tid] = (done, rest, line, state)
    return out


def _declared_path_roots(root: Path) -> tuple[str, ...]:
    """Raizes que o projeto declarou como centrais, sem nomes de produto fixos."""
    normalized = {
        value.replace("\\", "/").strip("/")
        for value in core_paths(root)
        if value and value not in {".", ".."}
    }
    return tuple(sorted(normalized, key=lambda value: (-len(value), value)))


def _path_from_backtick(raw: str, roots: tuple[str, ...]) -> str | None:
    """Extrai caminho relativo seguro de um trecho entre crases."""
    candidate = raw.strip().rstrip(".,;)")
    candidate = candidate.replace("\\", "/")
    if (not candidate or candidate.startswith(("/", "../"))
            or re.match(r"^[A-Za-z]:/", candidate)
            or "://" in candidate
            or any(part == ".." for part in candidate.split("/"))):
        return None
    if any(candidate == root or candidate.startswith(root + "/") for root in roots):
        return candidate
    if ("/" not in candidate and ROOT_FILE.fullmatch(candidate)
            and re.search(r"[A-Za-z]", candidate)):
        return candidate
    return None


def _declared_paths(root: Path, workstream: Path, body: str, plan_text: str,
                    plan_path: Path | None = None) -> set[str]:
    """Caminhos declarados pelas tarefas/plano + meta-estado da workstream."""
    declared: set[str] = set()
    ws_rel = rel(workstream, root).replace("\\", "/")
    declared.add(ws_rel)
    declared.add(ws_rel.rstrip("/") + "/")
    if plan_path is not None:
        declared.add(rel(plan_path, root).replace("\\", "/"))
    roots = _declared_path_roots(root)
    for text in (body, plan_text):
        for match in BACKTICK_CONTENT.finditer(text):
            path = _path_from_backtick(match.group(1), roots)
            if path:
                declared.add(path)
    # Convenção PLAN-024: módulo nomeado "em tools/" declara o diretório.
    if re.search(r"\bem `?tools/`?", plan_text) or "tools/" in declared or "tools" in declared:
        declared.add("tools/")
    if re.search(r"\bem `?docs/ai-ready/`?", plan_text) or "docs/ai-ready/" in declared:
        declared.add("docs/ai-ready/")
    if re.search(r"`?tools/review/`?", plan_text):
        declared.add("tools/review/")
    return declared


def _path_in_scope(path: str, declared: set[str]) -> bool:
    norm = path.replace("\\", "/")
    if norm in declared:
        return True
    for item in declared:
        prefix = item if item.endswith("/") else item.rstrip("/") + "/"
        if item.endswith("/") and (norm == item.rstrip("/") or norm.startswith(prefix)):
            return True
        if not item.endswith("/") and norm.startswith(item + "/"):
            return True
    return False


_FOREIGN_WS_META = re.compile(
    r"^project_state/workstreams/(WS-\d+[^/]*)/"
    r"(STATE\.md|EVENTS\.jsonl|EVIDENCE\.md|HANDOFF\.md)$"
)


def _is_foreign_workstream_meta(path: str, own_ws_rel: str) -> bool:
    """Meta-estado de outra WS no mesmo branch — higiene, não escopo desta."""
    norm = path.replace("\\", "/")
    if not _FOREIGN_WS_META.match(norm):
        return False
    own = own_ws_rel.replace("\\", "/").rstrip("/")
    return not (norm == own or norm.startswith(own + "/"))


def _test_path_patterns(root: Path | None) -> tuple[str, ...]:
    if root is None:
        return ()
    policy = root / ".agents" / "policy" / "validator-scope.yaml"
    if not policy.is_file():
        return ()
    return tuple(
        value.replace("\\", "/")
        for value in yaml_list(read(policy), "test_path_patterns")
        if value
    )


def _is_test_path(path: str, root: Path | None = None) -> bool:
    norm = path.replace("\\", "/")
    name = Path(norm).name
    if name == "run_scenarios.py":
        return True
    if TEST_NAME.search(norm):
        return True
    if name.startswith("test_") and name.endswith(".py"):
        return True
    if "/tests/" in f"/{norm}/" or "/__tests__/" in f"/{norm}/":
        return True
    return any(fnmatchcase(norm, pattern) for pattern in _test_path_patterns(root))


def _is_source_path(path: str, root: Path | None = None) -> bool:
    norm = path.replace("\\", "/")
    if _is_test_path(norm, root):
        return False
    return Path(norm).suffix.lower() in SOURCE_SUFFIX


def _span_in_string(content: str, start: int) -> bool:
    """True se o índice cai dentro de literal de string nesta linha."""
    i = 0
    n = len(content)
    while i < n and i < start:
        c = content[i]
        if c in "rRfFbBuU" and i + 1 < n and content[i + 1] in "'\"":
            i += 1
            c = content[i]
        if c in "'\"":
            quote = c
            i += 1
            while i < n:
                if content[i] == "\\":
                    i += 2
                    continue
                if content[i] == quote:
                    i += 1
                    break
                i += 1
            if i > start:
                return True
            continue
        i += 1
    return False


def _silence_or_weaken_hits(content: str, pattern: re.Pattern[str]) -> list[re.Match[str]]:
    """Matches ativos: fora de string e, para noqa, fora do layout flat de tools/."""
    hits: list[re.Match[str]] = []
    for match in pattern.finditer(content):
        if _span_in_string(content, match.start()):
            continue
        if pattern is SILENCE_ADDED and IMPORT_LAYOUT_NOQA.search(content):
            # Linha inteira é import+noqa de layout — não é engolir sinal de lógica.
            if match.group(0).lower().startswith("#") and "noqa" in match.group(0).lower():
                continue
        hits.append(match)
    return hits


def _top_level_defs(text: str) -> set[str]:
    names: set[str] = set()
    for match in TOP_LEVEL_DEF.finditer(text):
        names.add(match.group(1) or match.group(2))
    return names


def _symbols_removed_in_window(root: Path, base: str, head: str,
                               paths: list[str]) -> set[str]:
    """Defs/classes removidas de fonte na janela — poda de API, não enfraquecimento."""
    removed: set[str] = set()
    for path in paths:
        if not _is_source_path(path, root):
            continue
        before = _show_text(root, base, path) or ""
        after = _show_text(root, head, path) or ""
        removed |= _top_level_defs(before) - _top_level_defs(after)
    return removed


def _assert_targets_removed_api(content: str, removed: set[str]) -> bool:
    if not removed:
        return False
    return any(re.search(rf"\b{re.escape(name)}\b", content) for name in removed)


def check_escopo(report: Report, root: Path, *, paths: list[str],
                 workstream: Path, body: str, plan_text: str,
                 plan_path: Path | None = None) -> None:
    declared = _declared_paths(root, workstream, body, plan_text, plan_path=plan_path)
    own = rel(workstream, root)
    for path in paths:
        report.checked += 1
        if _path_in_scope(path, declared):
            continue
        if _is_foreign_workstream_meta(path, own):
            continue
        report.error(
            "g13::escopo", path,
            "Arquivo no diff da janela fora do escopo declarado pelas tarefas/plano.",
            "Declare o caminho na tarefa ou no plano ativo, ou remova-o do diff (G6).",
        )


def check_teste_enfraquecido(report: Report, root: Path, *, base: str, head: str,
                             paths: list[str]) -> None:
    removed_api = _symbols_removed_in_window(root, base, head, paths)
    deleted_block_start = re.compile(r"^\s*(?:class\s+\w+|(?:async\s+)?def\s+\w+)")
    for path in paths:
        suffix = Path(path).suffix.lower()
        if suffix not in SOURCE_SUFFIX and not _is_test_path(path, root):
            continue
        diff = _diff_text(root, base, head, path)
        report.checked += 1
        if diff is None:
            report.error(
                "g13::teste-enfraquecido", path,
                "Não foi possível obter o diff deste arquivo.",
                "Verifique a janela base..head e rode de novo.",
            )
            continue
        removed_asserts = 0
        in_deleted_block = False
        for line in diff.splitlines():
            if line.startswith("+++") or line.startswith("---"):
                continue
            if line.startswith("@@"):
                in_deleted_block = False
                continue
            if line.startswith("+"):
                content = line[1:]
                if deleted_block_start.match(content):
                    in_deleted_block = False
                if _silence_or_weaken_hits(content, WEAKEN_ADDED):
                    report.error(
                        "g13::teste-enfraquecido", path,
                        f"Marcador de teste enfraquecido adicionado: {content.strip()[:80]}",
                        "Remova skip/only ou justifique com finding; teste enfraquecido é crítico.",
                    )
                if ASSERT_LINE.search(content):
                    removed_asserts = max(0, removed_asserts - 1)
            elif line.startswith("-"):
                content = line[1:]
                if deleted_block_start.match(content):
                    in_deleted_block = True
                if ASSERT_LINE.search(content):
                    if in_deleted_block or _assert_targets_removed_api(content, removed_api):
                        continue
                    removed_asserts += 1
        if removed_asserts:
            report.error(
                "g13::teste-enfraquecido", path,
                f"{removed_asserts} asserção(ões) removida(s) sem substituição no mesmo arquivo.",
                "Restaure a asserção ou substitua por cobertura equivalente no diff.",
            )


def _source_module_tokens(path: str) -> set[str]:
    """Tokens que um teste tipicamente usa ao cobrir este fonte."""
    norm = path.replace("\\", "/")
    p = Path(norm)
    stem = p.stem
    tokens: set[str] = set()
    if stem and stem != "__init__":
        tokens.add(stem)
        tokens.add(f"test_{stem}")
        tokens.add(f"{stem}_test")
    parts = list(p.with_suffix("").parts)
    if len(parts) >= 2 and parts[0] in {"tools", "src", "lib", "app"}:
        # tools/review/build_prompt → review.build_prompt, build_prompt
        tokens.add(".".join(parts[1:]))
        tokens.add("/".join(parts[1:]))
    elif parts:
        tokens.add(".".join(parts))
    return {t for t in tokens if len(t) >= 4}


def _test_covers_source(source: str, test_path: str, root: Path) -> bool:
    """Correlacao deterministica nome/import entre fonte e teste na janela."""
    stem = Path(source.replace("\\", "/")).stem
    t_stem = Path(test_path.replace("\\", "/")).stem
    if stem and stem != "__init__":
        if t_stem in {f"test_{stem}", f"{stem}_test"}:
            return True
        if len(stem) >= 4 and stem in t_stem:
            return True
    tokens = _source_module_tokens(source)
    if not tokens:
        # __init__.py / stems curtos: qualquer teste no mesmo diretorio cobre.
        src_dir = str(Path(source).parent).replace("\\", "/")
        test_dir = str(Path(test_path).parent).replace("\\", "/")
        return test_dir == src_dir or test_dir.startswith(src_dir + "/")
    path = root / test_path
    if not path.is_file():
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return any(token in text for token in tokens)


def check_comportamento_sem_teste(report: Report, root: Path, *, paths: list[str]) -> None:
    sources = [p for p in paths if _is_source_path(p, root)]
    tests = [p for p in paths if _is_test_path(p, root)]
    if not sources:
        report.checked += 1
        return
    report.checked += 1
    if not tests:
        sample = sources[0]
        report.error(
            "g13::comportamento-sem-teste", sample,
            f"{len(sources)} arquivo(s) de fonte alterado(s) sem nenhum caminho de teste na janela.",
            "Inclua o teste correspondente no mesmo diff (prova-obrigatoria / G2).",
        )
        return

    # Correlacao so para fonte viva com comportamento novo. Delecao, __init__
    # vazio e scripts de skill sob .agents/ nao liberam falso-verde do caso
    # "qualquer teste cobre tudo", mas tambem nao exigem teste dedicado.
    live: list[str] = []
    for src in sources:
        norm = src.replace("\\", "/")
        if norm.startswith(".agents/") or norm.startswith("docs/"):
            continue
        if Path(norm).name == "__init__.py":
            continue
        if not (root / norm).is_file():
            continue
        live.append(src)
    if not live:
        return
    uncovered = [
        src for src in live
        if not any(_test_covers_source(src, t, root) for t in tests)
    ]
    if not uncovered:
        return
    sample = uncovered[0]
    listing = ", ".join(f"`{p}`" for p in uncovered[:5])
    more = f" (+{len(uncovered) - 5})" if len(uncovered) > 5 else ""
    report.error(
        "g13::comportamento-sem-teste", sample,
        f"{len(uncovered)} fonte(s) sem teste correspondente na janela: {listing}{more}.",
        "Inclua teste cujo nome/import correlacione com a fonte, ou declare a "
        "cobertura no plano (prova-obrigatoria / G2).",
    )


def check_sinal_silenciado(report: Report, root: Path, *, base: str, head: str,
                           paths: list[str]) -> None:
    for path in paths:
        if Path(path).suffix.lower() not in SOURCE_SUFFIX | {".sh", ".bash", ".ps1", ".yml", ".yaml"}:
            if not path.endswith(".py"):
                continue
        diff = _diff_text(root, base, head, path)
        report.checked += 1
        if diff is None:
            report.error(
                "g13::sinal-silenciado", path,
                "Não foi possível obter o diff deste arquivo.",
                "Verifique a janela base..head e rode de novo.",
            )
            continue
        # Janela deslizante de contexto para a nota de válvula.
        recent: list[str] = []
        for line in diff.splitlines():
            if line.startswith("+++") or line.startswith("---") or line.startswith("@@"):
                continue
            if not line.startswith("+"):
                continue
            content = line[1:]
            recent.append(content)
            if len(recent) > 8:
                recent.pop(0)
            if not _silence_or_weaken_hits(content, SILENCE_ADDED):
                continue
            neighborhood = "\n".join(recent)
            if ESCAPE_NOTE.search(neighborhood):
                continue
            report.error(
                "g13::sinal-silenciado", path,
                f"Sinal silenciado sem nota de válvula de escape: {content.strip()[:80]}",
                "Corrija a causa raiz, ou marque // GAMBIARRA: … com F-NNN (no-workarounds / G4).",
            )


def check_ledger_append_only(report: Report, root: Path, *, base: str, head: str,
                             paths: list[str]) -> None:
    ledgers = [p for p in paths if p.replace("\\", "/").endswith("EVENTS.jsonl")]
    if not ledgers:
        report.checked += 1
        return
    for path in ledgers:
        report.checked += 1
        before_raw = _show_text(root, base, path)
        after_raw = _show_text(root, head, path)
        if after_raw is None:
            report.error(
                "g13::ledger-append-only", path,
                "EVENTS.jsonl removido na janela.",
                "Ledger não se apaga. Restaure o arquivo.",
            )
            continue
        before = before_raw or ""
        before_lines = before.splitlines(keepends=True)
        after_lines = after_raw.splitlines(keepends=True)
        if len(after_lines) < len(before_lines) or after_lines[:len(before_lines)] != before_lines:
            report.error(
                "g13::ledger-append-only", path,
                "Linha removida ou reescrita em EVENTS.jsonl já gravado.",
                "Ledger é append-only (D-062). Corrija só por normalização de encoding "
                "declarada; não edite evento passado.",
            )
            continue
        diff = _diff_text(root, base, head, path)
        if diff is None:
            continue
        for line in diff.splitlines():
            if line.startswith("-") and not line.startswith("---") and line[1:].strip():
                report.error(
                    "g13::ledger-append-only", path,
                    "Linha removida ou reescrita em EVENTS.jsonl já gravado.",
                    "Ledger é append-only (D-062). Não edite evento passado.",
                )
                break


# Executáveis que um critério de plano pode invocar. A lista é curta de propósito:
# ela existe para que validar um repositório desconhecido não vire execução de
# código arbitrário. Um projeto que precise de outro executável o declara em
# `.agents/policy/validator-scope.yaml`, sob `exec_allowlist:` — e essa política
# é do projeto que HOSPEDA o validador, não do repositório que está sendo lido.
EXEC_ALLOWLIST = frozenset({
    "python", "python3", "py", "pytest", "node", "npm", "npx", "git", "make",
})

# Metacaracteres que só fazem sentido sob um shell. A presença de qualquer um
# significa que o critério pressupõe interpretação de shell — e é exatamente essa
# interpretação que abriria a porta para encadear comandos.
SHELL_METACHARACTERS = frozenset(";&|<>$`\n\r")


def load_exec_allowlist(root: Path) -> frozenset[str]:
    policy = root / ".agents" / "policy" / "validator-scope.yaml"
    if not policy.is_file():
        return EXEC_ALLOWLIST
    extra = {value for value in yaml_list(read(policy), "exec_allowlist") if value}
    return EXEC_ALLOWLIST | frozenset(extra)


def parse_criterion_command(cmd: str,
                            allowlist: frozenset[str] | None = None,
                            ) -> tuple[list[str], str | None]:
    """Converte o comando de um critério em argv seguro.

    Devolve (argv, None) quando o comando pode ser executado sem shell, ou
    ([], motivo) quando deve ser recusado. Recusar é o caminho seguro: um
    critério que o validador não sabe executar com segurança vira erro visível,
    nunca execução silenciosa sob shell.
    """
    import shlex

    allowed = allowlist if allowlist is not None else EXEC_ALLOWLIST
    stripped = cmd.strip()
    if not stripped:
        return [], "comando vazio"
    found = sorted(set(stripped) & SHELL_METACHARACTERS)
    if found:
        visible = " ".join(repr(character) for character in found)
        return [], f"contém metacaractere de shell ({visible})"
    try:
        argv = shlex.split(stripped, posix=True)
    except ValueError as exc:
        return [], f"não é um comando bem formado ({exc})"
    if not argv:
        return [], "comando vazio"
    executable = Path(argv[0]).name.lower()
    for suffix in (".exe", ".cmd", ".bat"):
        executable = executable[: -len(suffix)] if executable.endswith(suffix) else executable
    if executable not in allowed:
        return [], f"executável '{argv[0]}' fora da allowlist"
    return argv, None


def _criteria_checked(plan_text: str) -> list[tuple[str, str]]:
    """Lista (descrição, comando) dos critérios marcados [x]."""
    out: list[tuple[str, str]] = []
    for match in CRITERION_LINE.finditer(plan_text):
        if match.group(1) != "x":
            continue
        out.append((match.group(2).strip(), match.group(3).strip()))
    if out:
        return out
    for match in re.finditer(
        r"^- \[x\] (.+?)\s*comando:\s*`([^`]+)`",
        plan_text, re.M | re.I,
    ):
        out.append((match.group(1).strip(), match.group(2).strip()))
    return out


def check_criteria_shape(report: Report, root: Path, *, plan_path: Path | None,
                         plan_text: str) -> None:
    """Analise estatica da forma dos criterios marcados [x].

    Um criterio que o validador jamais poderia executar com seguranca e um
    defeito do plano HOJE, nao no dia em que alguem usar --exec-criteria: ele
    promete uma prova que nunca sera produzida. Como e analise de texto, roda
    tambem em projeto sem controle de versao.
    """
    if not plan_path:
        return
    checked = _criteria_checked(plan_text)
    if not checked:
        return
    allowlist = load_exec_allowlist(root)
    for _, cmd in checked:
        report.checked += 1
        _, rejection = parse_criterion_command(cmd, allowlist)
        if rejection:
            report.error(
                "g13::criterio-nao-executavel", rel(plan_path, root),
                f"Critério [x] declara um comando que o validador nunca executará: {rejection}",
                "Reescreva como comando único, sem metacaracteres de shell, com o "
                f"executável na allowlist ({', '.join(sorted(allowlist))}): `{cmd}`",
            )


def check_paridade_de_contrato(report: Report, root: Path, *, plan_path: Path | None,
                               plan_text: str, execute: bool) -> None:
    if not plan_path:
        report.checked += 1
        return
    checked = _criteria_checked(plan_text)
    if not checked:
        report.checked += 1
        return
    allowlist = load_exec_allowlist(root)
    if not execute:
        for desc, cmd in checked:
            report.checked += 1
            report.warn(
                "g13::paridade-de-contrato", rel(plan_path, root),
                f"Critério [x] não executado nesta passagem: {desc[:60]}",
                f"Rode com --exec-criteria, em projeto de confiança, para provar: {cmd}",
            )
        return
    for desc, cmd in checked:
        report.checked += 1
        argv, rejection = parse_criterion_command(cmd, allowlist)
        if rejection:
            report.error(
                "g13::criterio-nao-executavel", rel(plan_path, root),
                f"Critério [x] com comando que o validador recusa executar: {rejection}",
                "Reescreva o critério como um comando único, sem metacaracteres de shell, "
                f"e com o executável na allowlist ({', '.join(sorted(allowlist))}): `{cmd}`",
            )
            continue
        try:
            proc = subprocess.run(
                argv, shell=False, cwd=str(root),
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=600,
            )
        except subprocess.TimeoutExpired:
            report.error(
                "g13::paridade-de-contrato", rel(plan_path, root),
                f"Critério [x] estourou 600s: {desc[:80]}",
                f"Reexecute ou desmarque o critério até o comando ser barato: `{cmd}`",
            )
            continue
        except OSError as exc:
            report.error(
                "g13::paridade-de-contrato", rel(plan_path, root),
                f"Critério [x] não executou ({exc}): {desc[:80]}",
                f"Corrija o comando declarado: `{cmd}`",
            )
            continue
        if proc.returncode != 0:
            tail = (proc.stdout + proc.stderr).strip().splitlines()[-3:]
            detail = " | ".join(tail) if tail else f"exit {proc.returncode}"
            report.error(
                "g13::paridade-de-contrato", rel(plan_path, root),
                f"Critério [x] falhou no tip: {desc[:60]} — {detail[:200]}",
                f"Corrija até o comando sair 0, ou desmarque [x]: `{cmd}`",
            )


def check_evidencia(report: Report, root: Path, *, workstream: Path, body: str,
                    validated_commit: str | None) -> None:
    evidence_path = workstream / "EVIDENCE.md"
    evidence_text = read(evidence_path) if evidence_path.is_file() else ""
    blocks = _evidence_blocks(evidence_text)
    tasks = _task_rows(body)
    for tid, (done, rest, line, state) in tasks.items():
        if not done and state != "concluída":
            continue
        report.checked += 1
        refs = re.findall(r"\bE-\d{3}\b", rest)
        if not refs:
            report.error(
                "g13::evidência", rel(workstream / "STATE.md", root),
                f"{tid} concluída sem citar E-NNN.",
                "Aponte EVIDENCE.md#E-NNN com comando + saída + timestamp.",
                line,
            )
            continue
        for eid in refs:
            block = blocks.get(eid)
            if not block:
                report.error(
                    "g13::evidência", rel(workstream / "STATE.md", root),
                    f"{tid} cita {eid}, ausente de EVIDENCE.md.",
                    "Crie o bloco real ou mantenha a tarefa parcial.",
                    line,
                )
                continue
            missing = _evidence_contract(block)
            if missing:
                report.error(
                    "g13::evidência", rel(evidence_path, root),
                    f"{eid} (de {tid}) não prova: {', '.join(missing)}.",
                    "Registre comando, saída, timestamp ISO 8601 e commit Git exato.",
                )
                continue
            ev_commit = _evidence_commit(block)
            if not ev_commit or not validated_commit:
                continue
            resolved = _rev_parse(root, ev_commit)
            validated = _rev_parse(root, validated_commit)
            if not resolved:
                report.error(
                    "g13::evidência", rel(evidence_path, root),
                    f"{eid} cita commit inexistente '{ev_commit}'.",
                    "Use um commit real deste repositório.",
                )
            elif validated and _git_ok(root, "merge-base", "--is-ancestor",
                                       resolved, validated) is None:
                report.error(
                    "g13::evidência", rel(evidence_path, root),
                    f"{eid} prova {resolved[:12]}, que não é ancestral de "
                    f"validated_commit {validated[:12]}.",
                    "Reexecute na linhagem validada ou mantenha a tarefa parcial.",
                )


def check_segredos(report: Report, root: Path, *, base: str, head: str,
                   paths: list[str]) -> None:
    try:
        patterns = load_redaction_patterns(root)
        allowlist = load_redaction_allowlist(root)
    except (OSError, ValueError) as exc:
        report.checked += 1
        report.error(
            "g13::segredos", ".agents/policy/capture-policy.yaml",
            f"Não foi possível carregar a política de redação: {exc}",
            "Restaure capture-policy.yaml (reuso de G9).",
        )
        return
    for path in paths:
        report.checked += 1
        if path in allowlist:
            continue
        # Conteúdo no tip da janela (arquivo novo ou modificado).
        text = _show_text(root, head, path)
        if text is None:
            # Arquivo removido — varre o lado base.
            text = _show_text(root, base, path)
        if text is None:
            continue
        if "\0" in text[:8192]:
            continue
        for name, pattern in patterns:
            hit = pattern.search(text)
            if hit:
                line = text[:hit.start()].count("\n") + 1
                report.error(
                    "g13::segredos", path,
                    f"Possível segredo do tipo '{name}' no diff da janela.",
                    "Trate como comprometido e rotacione na origem (G9 / memory-privacy).",
                    line,
                )
                break


def run_as_validator(root: Path, *, execute_criteria: bool = False) -> Report:
    """Entrada de ``tools/validate.py``: só workstreams active com G13 em pending_gates."""
    report = Report("g13-verify")
    ws_root = root / "project_state" / "workstreams"
    if not ws_root.is_dir():
        return report
    for directory in sorted(d for d in ws_root.iterdir() if d.is_dir()):
        state = directory / "STATE.md"
        if not state.is_file():
            continue
        fm, _ = split_frontmatter(normalize(read(state)))
        if yaml_scalar(fm, "status") != "active":
            continue
        if "G13" not in yaml_list(fm, "pending_gates"):
            continue
        sub = run(
            root, workstream=directory, execute_criteria=execute_criteria,
        )
        report.checked += sub.checked
        report.issues.extend(sub.issues)
    return report


def run(
    root: Path,
    *,
    workstream: Path | None = None,
    ws_id: str | None = None,
    base: str | None = None,
    head: str | None = None,
    execute_criteria: bool = False,
) -> Report:
    """Verifica uma workstream. Sem alvo explícito, delega a ``run_as_validator``."""
    if workstream is None and ws_id is None and base is None and head is None:
        return run_as_validator(root, execute_criteria=execute_criteria)

    report = Report("g13-verify")
    ws = workstream or find_workstream(root, ws_id)
    if ws is None:
        report.error(
            "g13::workstream", "project_state/workstreams",
            "Workstream alvo não encontrada (passe --ws ou deixe exatamente uma active).",
            "Informe --ws WS-NNN.",
        )
        return report

    state_path = ws / "STATE.md"
    if not state_path.is_file():
        report.error(
            "g13::workstream", rel(ws, root),
            "STATE.md ausente.",
            "Workstream sem estado não tem janela verificável.",
        )
        return report

    text = normalize(read(state_path))
    fm, body = split_frontmatter(text)
    base_ref = base or yaml_scalar(fm, "base_commit")
    head_ref = head or _git_ok(root, "rev-parse", "HEAD")
    validated = yaml_scalar(fm, "validated_commit") or yaml_scalar(fm, "current_commit")
    plan_id = yaml_scalar(fm, "active_plan")
    plan_file = _plan_path(root, plan_id)
    plan_text = normalize(read(plan_file)) if plan_file else ""

    # Analise ESTATICA dos criterios: nao depende de janela nem de Git, e por isso
    # roda antes da guarda abaixo. Um criterio malformado ou hostil e defeito do
    # plano em qualquer projeto — inclusive nos que operam sem controle de versao.
    check_criteria_shape(report, root, plan_path=plan_file, plan_text=plan_text)

    # Projeto sem controle de versao declara base_commit `none` e nao tem HEAD.
    # G13 e uma verificacao DIFERENCIAL: sem duas pontas nao ha diferenca para
    # verificar. Reportar isso como erro puniria a ausencia de Git, que o
    # protocolo permite e declara como modo degradado — e a garantia que se perde
    # ja esta escrita la, em vez de virar um erro sem acao possivel.
    if base_ref == "none" or head_ref == "none" or not _git_ok(root, "rev-parse", "--git-dir"):
        return report

    if not base_ref or not head_ref:
        report.error(
            "g13::window", rel(state_path, root),
            "base_commit ou HEAD ausente — janela indefinida.",
            "Declare base_commit no STATE.md e opere num repositório Git.",
        )
        return report

    base_sha = _rev_parse(root, base_ref)
    head_sha = _rev_parse(root, head_ref)
    if not base_sha or not head_sha:
        report.error(
            "g13::window", rel(state_path, root),
            f"Referência inválida: base={base_ref!r} head={head_ref!r}.",
            "Use SHAs reais deste repositório.",
        )
        return report

    paths = window_paths(root, base_sha, head_sha)
    if paths is None:
        report.error(
            "g13::window", rel(ws, root),
            f"git diff --name-only {base_sha[:12]}..{head_sha[:12]} falhou.",
            "Corrija o Git ou a janela e rode de novo (fail-closed).",
        )
        return report

    # Árvore suja não entra na janela tipada — avisa, não falha.
    status = _git_ok(root, "status", "--short") or ""
    dirty = parse_status_paths(status)
    if dirty:
        report.warn(
            "g13::window", rel(ws, root),
            f"{len(dirty)} caminho(s) sujo(s) fora da janela base..HEAD — G13 não os viu.",
            "Commite (ou descarte) antes de tratar o veredito como cobertura do tip.",
        )

    if plan_file and plan_text and not any(
        fold(line[2:].strip()).startswith(fold("Critérios de validação"))
        for line in plan_text.splitlines() if line.startswith("##")
    ):
        report.warn(
            "g13::paridade-de-contrato", rel(plan_file, root),
            "Plano ativo sem seção de critérios de validação detectável.",
            "Todo plano declara ## Critérios de validação com comando: `...`.",
        )

    ledger_path = ws / "EVENTS.jsonl"
    if ledger_path.is_file():
        read_ledger(ledger_path)

    check_escopo(
        report, root, paths=paths, workstream=ws, body=body, plan_text=plan_text,
        plan_path=plan_file,
    )
    check_teste_enfraquecido(report, root, base=base_sha, head=head_sha, paths=paths)
    check_comportamento_sem_teste(report, root, paths=paths)
    check_sinal_silenciado(report, root, base=base_sha, head=head_sha, paths=paths)
    check_ledger_append_only(report, root, base=base_sha, head=head_sha, paths=paths)
    check_paridade_de_contrato(
        report, root, plan_path=plan_file, plan_text=plan_text, execute=execute_criteria,
    )
    check_evidencia(report, root, workstream=ws, body=body, validated_commit=validated)
    check_segredos(report, root, base=base_sha, head=head_sha, paths=paths)
    return report


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError, AttributeError):
                pass

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ws", help="ID da workstream (WS-NNN)")
    ap.add_argument("--base", help="Limite inferior da janela (default: base_commit)")
    ap.add_argument("--head", help="Limite superior da janela (default: HEAD)")
    ap.add_argument("--exec-criteria", action="store_true",
                    help="EXECUTA os critérios [x] do plano. Só use em projeto de "
                         "confiança: o comando vem de um arquivo do repositório lido")
    ap.add_argument("--no-exec", action="store_true",
                    help=argparse.SUPPRESS)  # compatibilidade: o padrão já é não executar
    ap.add_argument("--json", action="store_true", help="saída estruturada")
    ap.add_argument("--quiet", action="store_true", help="só o resumo")
    args = ap.parse_args(argv)

    root = Path(__file__).resolve().parent.parent

    report = run(
        root,
        ws_id=args.ws,
        base=args.base,
        head=args.head,
        execute_criteria=args.exec_criteria and not args.no_exec,
    )

    if args.json:
        print(json.dumps({
            "name": report.name,
            "checks": report.checked,
            "errors": len(report.errors),
            "warnings": len(report.warns),
            "issues": [i.as_dict() for i in report.issues],
            "detectors": list(DETECTORS),
        }, ensure_ascii=False, indent=2))
        return 1 if report.errors else 0

    print("G13 — verificação diferencial")
    print(f"raiz: {root}\n")
    print_report(report, verbose=not args.quiet)
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
