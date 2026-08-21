#!/usr/bin/env python3
"""Monta o prompt unico da Revisao de Ciclo (RC) — VLAEG 4.0 / D-064.

    python -B tools/review/build_prompt.py --gate RC --ws WS-009 \\
        --author "cursor/grok-4.5" --engine "opencode/openai/gpt-5.6-sol" --effort high

Uma rodada de julgamento, duas secoes, G13 + validate.py embutidos e assinados.
Prompt manuscrito e rodada invalida. `run_engine.py` permanece o runner (stall
600 s / teto duro 1800 s).
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from review import contract as C  # noqa: E402

GATE = {
    "template": ".agents/skills/protocol/cycle-review/references/rc-prompt.md",
    "prompt": "rc-prompt.md",
    "diff": "rc-diff.patch",
    "log_prefix": "rc",
    "role": "revisor de ciclo",
}

NEXT_AUD_RE = re.compile(r"\*\*Pr[oó]ximo ID:\*\*\s*(AUD-(\d+))", re.I)
WS_SLUG_RE = re.compile(r"^WS-\d+-(.+)$")

MAX_LINES, MAX_FILES = 1500, 25
PROMPT_MARK = "<!-- PROMPT -->"
ROUND_META = "round-meta.json"

SCAN_EXEMPT = "wip-scan: definicao"
WIP = (                                                   # wip-scan: definicao
    ("conflito de merge nao resolvido", "<<<<<<< "),      # wip-scan: definicao
    ("statement de depuracao", "debugger;"),              # wip-scan: definicao
    ("TODO marcado como WIP", "TODO(WIP)"),               # wip-scan: definicao
)

RULE_FILES = [
    "AGENTS.md",
    "project_state/PROJECT.md",
    "project_state/DECISIONS.md",
    "docs/ai-ready/quality-gates.md",
    "docs/ai-ready/cycle-review.md",
    "docs/ai-ready/protocol.md",
]


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, capture_output=True,
        text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0 and not result.stdout:
        raise SystemExit(f"git {' '.join(args)} falhou:\n{result.stderr.strip()}")
    return result.stdout


def diff_command(base: str, paths: list[str], *, name_only: bool = False) -> list[str]:
    args = ["diff", "--no-ext-diff"]
    if name_only:
        args.append("--name-only")
    args.append(base)
    if paths:
        args += ["--", *paths]
    return args


def render(template: str, fields: dict[str, object]) -> str:
    for key, value in fields.items():
        template = template.replace("{" + key + "}", str(value))
    return template


def propose_shards(files: list[str], *, max_files: int = MAX_FILES) -> list[str]:
    if not files:
        return []
    buckets: dict[str, list[str]] = {}
    for path in files:
        parts = path.replace("\\", "/").split("/")
        key = "/".join(parts[:2]) if len(parts) > 1 else parts[0]
        buckets.setdefault(key, []).append(path)
    tips: list[str] = []
    for key, group in sorted(buckets.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        if len(group) <= max_files:
            tips.append(f"--paths {key}   # {len(group)} arquivo(s)")
            continue
        for i in range(0, len(group), max_files):
            chunk = group[i:i + max_files]
            tips.append(
                "--paths " + " ".join(chunk[:3])
                + (" …" if len(chunk) > 3 else "")
                + f"   # shard {i // max_files + 1}, {len(chunk)} arquivo(s)"
            )
    return tips


EXIT_CODE_RE = re.compile(r"^#\s*exit_code:\s*(-?\d+)\s*$", re.M)
CAPTURE_SHA_RE = re.compile(r"^#\s*sha:\s*([0-9a-f]{7,40})\s*$", re.M | re.I)
ENVELOPED_MARKERS = (
    "### Fatia A — estrutural",
    "### G13 — verificacao diferencial",
)


def format_fatia_a(*, command: str, sha: str, digest: str, tail: str) -> str:
    body = tail.strip() or "(saida vazia)"
    return "\n".join([
        "### Fatia A — estrutural (assinada pelo coordenador)",
        "",
        f"- Comando: `{command}`",
        f"- SHA: `{sha}`",
        f"- Digest SHA-256 da saida: `{digest}`",
        "",
        "**Nao reexecute o validador.** A fatia A esta assinada abaixo para este SHA.",
        "Se o SHA auditado divergir deste, a rodada e invalida.",
        "",
        "```text",
        body,
        "```",
    ])


def format_g13(*, command: str, sha: str, digest: str, tail: str) -> str:
    body = tail.strip() or "(saida vazia)"
    return "\n".join([
        "### G13 — verificacao diferencial (assinada pelo coordenador)",
        "",
        f"- Comando: `{command}`",
        f"- SHA: `{sha}`",
        f"- Digest SHA-256 da saida: `{digest}`",
        "",
        "**Nao reexecute `tools/verify.py`.** O G13 esta assinado abaixo para este SHA.",
        "",
        "```text",
        body,
        "```",
    ])


def _tail_text(text: str, *, max_lines: int = 80) -> str:
    lines = text.splitlines()
    return "\n".join(lines[-max_lines:] if len(lines) > max_lines else lines)


def _sha_matches(declared: str, expected: str) -> bool:
    a, b = declared.lower(), expected.lower()
    return a == b or a.startswith(b) or b.startswith(a)


def authenticate_gate_output(
    text: str, *, expected_sha: str, label: str,
) -> tuple[str, int]:
    """Valida proveniencia da saida bruta do gate. Devolve (texto, exit_code)."""
    if any(marker in text for marker in ENVELOPED_MARKERS):
        raise SystemExit(
            f"pre-voo: {label} ja esta envelopada — passe a saida bruta "
            f"(com `# sha:` e `# exit_code:`), nao o bloco assinado"
        )
    sha_hits = list(CAPTURE_SHA_RE.finditer(text))
    if not sha_hits:
        raise SystemExit(
            f"pre-voo: {label} sem `# sha: <commit>` — proveniencia incompleta"
        )
    declared = sha_hits[-1].group(1)
    if not _sha_matches(declared, expected_sha):
        raise SystemExit(
            f"pre-voo: {label} declara sha `{declared}` mas o HEAD e "
            f"`{expected_sha}` — recuse relabeling (quality-gates.md §3)"
        )
    code_hits = list(EXIT_CODE_RE.finditer(text))
    if not code_hits:
        raise SystemExit(
            f"pre-voo: {label} sem `# exit_code: N` — proveniencia incompleta"
        )
    exit_code = int(code_hits[-1].group(1))
    if exit_code != 0:
        raise SystemExit(
            f"pre-voo: {label} exit_code={exit_code} — RC abortada com gate vermelho "
            f"(cycle-review.md §5)"
        )
    return text, exit_code


def _stamp_capture(text: str, *, sha: str, exit_code: int) -> str:
    body = text.rstrip() + "\n"
    if not CAPTURE_SHA_RE.search(body):
        body += f"# sha: {sha}\n"
    if not EXIT_CODE_RE.search(body):
        body += f"# exit_code: {exit_code}\n"
    else:
        body = EXIT_CODE_RE.sub(f"# exit_code: {exit_code}", body)
        if not _sha_matches(CAPTURE_SHA_RE.findall(body)[-1], sha):
            body += f"# sha: {sha}\n"
    return body


def load_or_run_fatia_a(root: Path, sha: str, source: Path | None) -> tuple[str, str]:
    command = "python -B tools/validate.py"
    if source is not None:
        text = source.read_text(encoding="utf-8", errors="replace")
        text, _ = authenticate_gate_output(text, expected_sha=sha, label="--fatia-a")
    else:
        proc = subprocess.run(
            [sys.executable, "-B", str(root / "tools" / "validate.py")],
            cwd=root, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        text = proc.stdout or ""
        if proc.stderr:
            text = text + ("\n" if text and not text.endswith("\n") else "") + proc.stderr
        text = _stamp_capture(text, sha=sha, exit_code=proc.returncode)
        text, _ = authenticate_gate_output(text, expected_sha=sha, label="validate.py")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return format_fatia_a(
        command=command, sha=sha, digest=digest, tail=_tail_text(text),
    ), digest


def load_or_run_g13(root: Path, sha: str, *, ws: str, base: str | None,
                    source: Path | None) -> tuple[str, str]:
    cmd_parts = ["python", "-B", "tools/verify.py", "--ws", ws]
    if base:
        cmd_parts += ["--base", base]
    command = " ".join(cmd_parts)
    if source is not None:
        text = source.read_text(encoding="utf-8", errors="replace")
        text, _ = authenticate_gate_output(text, expected_sha=sha, label="--g13")
    else:
        argv = ["--ws", ws]
        if base:
            argv += ["--base", base]
        buf = io.StringIO()
        old_out, old_err = sys.stdout, sys.stderr
        try:
            sys.stdout = buf
            sys.stderr = buf
            from verify import main as verify_main  # noqa: WPS433
            code = verify_main(argv)
        finally:
            sys.stdout, sys.stderr = old_out, old_err
        text = _stamp_capture(buf.getvalue(), sha=sha, exit_code=code)
        text, _ = authenticate_gate_output(text, expected_sha=sha, label="verify.py")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return format_g13(
        command=command, sha=sha, digest=digest,
        tail=_tail_text(text, max_lines=120),
    ), digest


def fatia_a_block_for_prompt(*, root: Path, sha: str,
                             source: Path | None = None) -> tuple[str, str | None]:
    block, digest = load_or_run_fatia_a(root, sha, source)
    return block, digest


def g13_block_for_prompt(*, root: Path, sha: str, ws: str,
                         base: str | None = None,
                         source: Path | None = None) -> tuple[str, str | None]:
    block, digest = load_or_run_g13(root, sha, ws=ws, base=base, source=source)
    return block, digest


def next_audit_id(root: Path) -> str:
    path = root / "project_state" / "AUDITS.md"
    if not path.is_file():
        raise SystemExit(f"indice de auditorias ausente: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    match = NEXT_AUD_RE.search(text)
    if not match:
        raise SystemExit(f"{path}: nao achei 'Proximo ID: AUD-NNN'")
    return match.group(1)


def default_slug(ws: str) -> str:
    match = WS_SLUG_RE.match(ws)
    return match.group(1) if match else ws.lower()


def rc_format_block(*, audit_id: str, ws: str, engine: str, commit: str,
                    patch_sha256: str) -> str:
    return "\n".join([
        "```markdown",
        "---",
        f"id: {audit_id}",
        "status: vigente",
        "tipo: revisao-de-ciclo",
        f"ws: {ws}",
        f"engine: {engine}",
        "independence: cross-LLM — <modelo do autor> → <modelo do revisor>",
        f"commit: {commit}",
        f"patch_sha256: {patch_sha256}",
        "verdict: SHIP | FIX_BEFORE_SHIP | BLOCKED",
        "findings: <n>",
        "---",
        "",
        f"# {audit_id} — Revisao de Ciclo · {ws}",
        "",
        "## Diagnostico",
        "",
        "<leitura adversarial da janela; nunca vazio>",
        "",
        "## Achados",
        "",
        "### R-01 — <titulo>",
        "- **Severidade:** critica | alta | media | baixa | informativa",
        "- **Tipo:** defeito | estrutural",
        "- Classe: critico | prova-obrigatoria | contrato | cobertura-adicional | risco | nit",
        "- Arquivo: <caminho>:<linha>",
        "- Problema: <o que esta errado>",
        "- Por que importa: <regra ou restricao violada>",
        "- Correcao sugerida: <direcao, nao patch pronto>",
        "",
        "(zero achados: escreva prosa sob ## Achados, sem nenhum `R-<n>`)",
        "",
        "## Paridade de contrato",
        "",
        "| Campo do contrato | Esperado | Entregue | Confere |",
        "|---|---|---|---|",
        "| <campo do plano/spec> | <esperado> | <entregue> | sim | nao | n/a |",
        "",
        "(sem plano/spec na secao Contrato: uma linha `n/a` com motivo; "
        "SHIP com tabela vazia quando havia contrato e rodada invalida)",
        "",
        "## O que nao consegui verificar",
        "",
        "<conteudo; nunca vazio por conveniencia — escreva `nada` se verificou tudo>",
        "```",
    ])


def rc_output_rules() -> str:
    return "\n".join([
        "- Escreva **exatamente um** arquivo, no caminho indicado. Nenhum outro.",
        "- Arquivo-alvo ainda inexistente: crie-o. Recuse só se o diretório-pai "
        "não existir, o caminho for ambíguo, sair da árvore ou não for gravável "
        "— nunca use stdout/chat como artefato.",
        "- Todo achado tem ID local `R-NN`, severidade, tipo e classe (findings-triage.md).",
        "- Contador `findings` do frontmatter bate com a contagem de `R-<n>` no corpo.",
        "- `commit` e `patch_sha256` sao a fotografia: copie do bloco acima, sem alterar.",
        "- Veredito `SHIP` exige zero achados `critico`/`prova-obrigatoria` e tabela "
        "de paridade preenchida quando havia plano/spec no prompt.",
        "- Engenharia elegante que nao entrega o campo do plano nao e `SHIP`.",
        "- Nao existe rodada 2: o que nao couber nesta passagem vai em "
        "`## O que nao consegui verificar` ou como `risco`/`nit` para a WS seguinte.",
        "- Sem `TBD`, `TODO` ou caminho inventado.",
    ])


def preflight(diff: str, files: list[str]) -> list[str]:
    fails = []
    if not diff.strip():
        fails.append("diff vazio: nao ha o que revisar")
    lines = diff.count("\n")
    if lines > MAX_LINES:
        fails.append(
            f"diff com {lines} linhas (teto {MAX_LINES}) — divida em shards por "
            f"modulo, fronteira arquitetural ou tarefa do plano, com --paths; "
            f"os shards alimentam a mesma auditoria"
        )
    if len(files) > MAX_FILES:
        fails.append(
            f"{len(files)} arquivos (teto {MAX_FILES}) — divida em shards pela "
            f"mesma regra, com --paths"
        )
    added = [
        line for line in diff.splitlines()
        if line.startswith("+") and not line.startswith("+++")
        and SCAN_EXEMPT not in line
    ]
    for label, marker in WIP:
        hit = next((line for line in added if _wip_marker_active(line, marker)), None)
        if hit:
            fails.append(f"{label} numa linha adicionada: {hit.strip()[:70]}")
    return fails


def _wip_marker_active(line: str, marker: str) -> bool:
    """True se o marcador e codigo/WIP real, nao documentacao ou teste do scanner."""
    content = line[1:] if line.startswith("+") else line
    if marker not in content:
        return False
    # Norma/docs citando o marcador entre backticks.
    bare = marker.rstrip(";")
    if f"`{marker}`" in content or f"`{bare}`" in content:
        return False
    # Teste do proprio preflight (assert + string com o marcador).
    if "preflight" in content and ("assert" in content or "SCAN_EXEMPT" in content):
        return False
    if "SCAN_EXEMPT" in content:
        return False
    return True


def photograph_window(files: list[str], full_files: list[str]) -> dict[str, object]:
    """Rótulo e lista da fotografia: fatia nunca se chama patch completo (AUD-017 R-01)."""
    omitted = sorted(set(full_files) - set(files))
    listed = "\n".join(f"- `{f}`" for f in files) or "- (nenhum)"
    if omitted:
        listed += (
            f"\n\nArquivos de base..HEAD omitidos desta fatia ({len(omitted)}):\n"
            + "\n".join(f"- `{f}`" for f in omitted)
        )
        heading = (
            f"Patch desta fatia ({len(files)} de {len(full_files)} "
            "arquivos da janela)"
        )
    else:
        heading = "Patch completo"
    return {
        "omitted_files": omitted,
        "patch_heading": heading,
        "changed_files": listed,
        "partial_window": bool(omitted),
    }


def scope_manifest(files: list[str], diff: str, base: str, head: str) -> dict[str, object]:
    return {
        "base_commit": base,
        "head_commit": head,
        "patch_sha256": hashlib.sha256(diff.encode("utf-8")).hexdigest(),
        "files": files,
        "lines": diff.count("\n"),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def resolve_ws_dir(root: Path, ws: str) -> Path:
    exact = root / "project_state" / "workstreams" / ws
    if exact.is_dir():
        return exact
    matches = sorted(
        d for d in (root / "project_state" / "workstreams").iterdir()
        if d.is_dir() and d.name.startswith(ws)
    )
    if len(matches) == 1:
        return matches[0]
    raise SystemExit(f"workstream inexistente ou ambigua: {ws}")


def fail_preflight(fails: list[str], files: list[str]) -> int:
    print("PRE-VOO REPROVADO — RC nao foi aberta:", file=sys.stderr)
    for fail in fails:
        print(f"  - {fail}", file=sys.stderr)
    tips = propose_shards(files)
    if tips and any("shard" in f or "teto" in f for f in fails):
        print(
            "\n  Sugestoes de corte (--paths); os shards alimentam a mesma auditoria:",
            file=sys.stderr,
        )
        for tip in tips[:12]:
            print(f"    {tip}", file=sys.stderr)
    print("\n  Falha de pre-voo nao consome orcamento: nada foi invocado.",
          file=sys.stderr)
    return 1


def main() -> int:
    from _common import yaml_list, yaml_scalar  # noqa: WPS433

    root = Path(__file__).resolve().parent.parent.parent
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--gate", required=True, choices=["RC"],
                    help="apenas RC apos T-200; G11/G12 aposentados")
    ap.add_argument("--ws", required=True)
    ap.add_argument("--task", help="usa active_tasks do STATE se omitido")
    ap.add_argument("--author", required=True)
    ap.add_argument("--engine", required=True)
    ap.add_argument("--base", help="limite inferior da janela (default: base_commit)")
    ap.add_argument("--paths", nargs="*", default=[])
    ap.add_argument("--contract-paths", nargs="*", default=[])
    ap.add_argument(
        "--allow-partial-window",
        action="store_true",
        help="permite --paths omitir arquivos de base..HEAD (shards); default exige cobertura total",
    )
    ap.add_argument("--fatia-a", type=Path,
                    help="saida assinada de tools/validate.py; se omitido, embute agora")
    ap.add_argument("--g13", type=Path,
                    help="saida assinada de tools/verify.py; se omitido, embute agora")
    ap.add_argument("--slug", help="sufixo de audits/AUD-NNN-<slug>.md")
    ap.add_argument("--effort", default="high", choices=["high", "High", "HIGH"])
    args = ap.parse_args()
    args.effort = args.effort.lower()

    ws_dir = resolve_ws_dir(root, args.ws)
    state = ws_dir / "STATE.md"
    fm = ""
    if state.is_file():
        fm, _ = C.split_frontmatter(state.read_text(encoding="utf-8", errors="replace"))
    ws_id = (yaml_scalar(fm, "id") if fm else None) or args.ws
    if not args.task and fm:
        tasks = yaml_list(fm, "active_tasks")
        if tasks:
            args.task = tasks[0]
    args.task = args.task or "RC"

    base = args.base
    if base is None and fm:
        base = yaml_scalar(fm, "base_commit")

    head = git(root, "rev-parse", "HEAD").strip()
    diff_base = base or head
    full_files = [
        f for f in git(root, *diff_command(diff_base, [], name_only=True)).splitlines()
        if f
    ]
    diff = git(root, *diff_command(diff_base, args.paths))
    files = [
        f for f in git(root, *diff_command(diff_base, args.paths, name_only=True)).splitlines()
        if f
    ]
    if args.paths and not args.allow_partial_window:
        omitted = sorted(set(full_files) - set(files))
        if omitted:
            sample = ", ".join(omitted[:5])
            more = f" (+{len(omitted) - 5})" if len(omitted) > 5 else ""
            fails_partial = [
                f"--paths omite {len(omitted)} arquivo(s) de {diff_base}..HEAD "
                f"({sample}{more}) — passe o restante em shards com "
                f"--allow-partial-window e alimente a mesma auditoria, ou remova --paths"
            ]
            return fail_preflight(fails_partial, full_files)

    fails = preflight(diff, files)
    status_before = git(root, "status", "--short")
    dirty = C.substantive_dirty_paths(
        status_before, ws=ws_dir.name, path_filters=args.paths, reviewed_files=files,
    )
    if dirty:
        sample = ", ".join(dirty[:5])
        more = f" (+{len(dirty) - 5})" if len(dirty) > 5 else ""
        fails.append(
            f"escopo sujo ({len(dirty)} caminho(s)): {sample}{more} — "
            f"limpe ou exclua do escopo antes da RC (cycle-review.md §5)"
        )
    if fails:
        return fail_preflight(fails, files)

    audit_id = next_audit_id(root)
    slug = args.slug or default_slug(ws_dir.name)
    artifact_rel = Path("audits") / f"{audit_id}-{slug}.md"

    out_dir = ws_dir / "_inflight" / "rc"
    out_dir.mkdir(parents=True, exist_ok=True)
    diff_path = out_dir / GATE["diff"]
    diff_path.write_text(diff, encoding="utf-8", newline="\n")
    (out_dir / "status-before-rc.txt").write_text(
        status_before, encoding="utf-8", newline="\n",
    )

    photo = photograph_window(files, full_files)
    manifest = scope_manifest(files, diff, base or head, head)
    manifest["audit_id"] = audit_id
    manifest["artifact"] = artifact_rel.as_posix()
    manifest["effort"] = args.effort
    manifest["omitted_files"] = photo["omitted_files"]
    manifest["partial_window"] = photo["partial_window"]

    fatia_a_block, fatia_digest = fatia_a_block_for_prompt(
        root=root, sha=head, source=args.fatia_a,
    )
    g13_block, g13_digest = g13_block_for_prompt(
        root=root, sha=head, ws=ws_id, base=base, source=args.g13,
    )
    if fatia_digest:
        (out_dir / "fatia-a-signed.txt").write_text(
            fatia_a_block, encoding="utf-8", newline="\n",
        )
        manifest["fatia_a_sha256"] = fatia_digest
    if g13_digest:
        (out_dir / "g13-signed.txt").write_text(
            g13_block, encoding="utf-8", newline="\n",
        )
        manifest["g13_sha256"] = g13_digest

    (out_dir / "scope-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )
    (out_dir / ROUND_META).write_text(
        json.dumps({
            "gate": "RC", "mode": "SINGLE",
            "engine": args.engine, "author": args.author, "task": args.task,
            "effort": args.effort, "dirty_paths": len(dirty),
            **manifest,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )

    template_path = root / GATE["template"]
    if not template_path.is_file():
        raise SystemExit(f"template ausente: {template_path}")
    template = template_path.read_text(encoding="utf-8")
    if PROMPT_MARK in template:
        template = template.split(PROMPT_MARK, 1)[1].lstrip("\n")

    rules = [f"- `{f}`" for f in RULE_FILES if (root / f).is_file()]
    contract_paths = [f"- `{p}`" for p in args.contract_paths] or [
        "- (nenhum artefato de contrato foi passado — avise se isso "
        "impedir a avaliacao de paridade)"
    ]

    fields = {
        "role": GATE["role"],
        "task": args.task,
        "ws": ws_id,
        "author": args.author,
        "engine": args.engine,
        "commit": head,
        "base": base or "(sem base: diff contra HEAD)",
        "audit_id": audit_id,
        "artifact_path": artifact_rel.as_posix(),
        "diff_path": diff_path.relative_to(root).as_posix(),
        "changed_files": photo["changed_files"],
        "patch_heading": photo["patch_heading"],
        "project_rules": "\n".join(rules),
        "context_paths": "\n".join(contract_paths),
        "g13_block": g13_block,
        "fatia_a_block": fatia_a_block,
        "format_block": rc_format_block(
            audit_id=audit_id, ws=ws_id, engine=args.engine,
            commit=head, patch_sha256=str(manifest["patch_sha256"]),
        ),
        "output_rules": rc_output_rules(),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    missing = [
        k for k in ("{format_block}", "{output_rules}", "{g13_block}", "{fatia_a_block}")
        if k not in template
    ]
    if missing:
        raise SystemExit(f"template RC sem os marcadores {missing}")

    prompt = render(template, fields)
    leftover = re.findall(r"\{([a-z_]+)\}", prompt)
    if leftover:
        raise SystemExit(
            f"marcadores nao substituidos no prompt: {sorted(set(leftover))}. "
            f"Prompt incompleto nunca vai para o motor."
        )
    prompt = "<!-- validate-links: illustrative-paths -->\n" + prompt
    prompt_path = out_dir / GATE["prompt"]
    prompt_path.write_text(prompt, encoding="utf-8", newline="\n")

    print(f"RC preparada — uma rodada de julgamento ({audit_id})")
    print(f"  prompt    {prompt_path.relative_to(root).as_posix()}")
    print(f"  diff      {diff_path.relative_to(root).as_posix()} "
          f"({len(files)} arquivo(s), {diff.count(chr(10))} linha(s))")
    print(f"  commit    {head}")
    print(f"  base      {base or '(HEAD)'}")
    print(f"  patch     sha256:{manifest['patch_sha256'][:16]}…")
    if photo["partial_window"]:
        print(
            f"  janela    PARCIAL — {len(photo['omitted_files'])} omitido(s) "
            "listados no prompt; o diff nao e patch completo"
        )
    print(f"  g13       sha256:{(g13_digest or '—')[:16]}…")
    print(f"  fatia A   sha256:{(fatia_digest or '—')[:16]}…")
    print(f"  artefato  {artifact_rel.as_posix()}")
    print()
    stdout_log = out_dir / "rc.stdout.log"
    stderr_log = out_dir / "rc.stderr.log"
    prompt_rel = prompt_path.relative_to(root).as_posix()
    print(
        f"  Invoque o motor '{args.engine}' (effort {args.effort}) apontando para o "
        f"prompt, sem --auto (D-044). Preferivel via runner:"
    )
    print("    python -B tools/review/run_engine.py \\")
    print(f"      --stdout {stdout_log.relative_to(root).as_posix()} \\")
    print(f"      --stderr {stderr_log.relative_to(root).as_posix()} \\")
    print(f"      --meta {out_dir.relative_to(root).as_posix()}/run-engine.json \\")
    print(
        f"      -- <comando do motor> \"Leia e execute exatamente o prompt em "
        f"{prompt_rel}. Escreva somente o artefato em {artifact_rel.as_posix()}.\""
    )
    print()
    print("  Relogios: stall 600s / teto duro 1800s. Sem rodada 2. Sem terceiro fallback.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
