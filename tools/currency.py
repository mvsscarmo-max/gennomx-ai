"""Passagem de vigência — PLAN-022 / T-178 · norma docs/rules/state-currency.md.

Códigos (erros):
  state::decision-supersede-reciprocity
  state::decision-scope-expired
  state::canon-retired-value
  state::impact-path-missing
  state::currency-change-unlogged
  state::future-date
  state::frozen-no-banner
  state::plan-duplicate
  state::ledger-encoding

Códigos (avisos — §8, nunca erros sem calibragem):
  state::finding-stale
  state::ws-paused-stale
  state::plan-orphan
  state::changelog-stale
  state::decision-cluster

Inventário (T-182): build_inventory() imprime o retrato §8 da auditoria round 5.
"""
from __future__ import annotations

import json
import re
import subprocess
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from _common import (
    Report,
    decode_bytes,
    excluded_parts,
    read,
    read_ledger,
    rel,
    split_frontmatter,
    walk_files,
    yaml_list,
    yaml_scalar,
)

STALE_DAYS = 45
CHANGELOG_DECISION_GAP = 10
FROZEN_BANNER = re.compile(r"^<!--\s*vlaeg:frozen\b")
FROZEN_ROOTS = ("docs/legacy", "docs/historico")

TASK_RE = re.compile(r"^- \[( |x)\] (T-\d{3}) — (.+)$", re.M)
DECISION_SPLIT = re.compile(r"^## (D-\d+)", re.M)
FINDING_SPLIT = re.compile(r"^## (F-\d+)", re.M)
STATUS_LINE = re.compile(r"\*\*Status:\*\*\s*([^\n]+)", re.I)
IMPACTO_LINE = re.compile(r"\*\*Impacto:\*\*\s*([^\n]+)", re.I)
SUBST_LINE = re.compile(r"\*\*Substitui/substitu[ií]da por:\*\*\s*([^\n]+)", re.I)
DATA_LINE = re.compile(r"\*\*Data:\*\*\s*(\d{4}-\d{2}-\d{2})")
ISO_TS = re.compile(r"\b(\d{4}-\d{2}-\d{2})(?:T\d{2}:\d{2}:\d{2}Z)?\b")
PLAN_ID_RE = re.compile(r"\bPLAN-\d{3}\b")
DEC_ID_RE = re.compile(r"\bD-\d+\b")
FIND_ID_RE = re.compile(r"\bF-\d+\b")
# Caminhos citados entre crases que este validador reconhece como referencia a
# arquivo do projeto. O prefixo do protocolo e fixo; o resto vem de
# validator-scope.yaml (`core_paths:`), porque cada projeto tem os seus. Fixar
# nomes de aplicacao aqui amarraria o validador ao layout de um repositorio so.
PROTOCOL_PATH_PREFIXES = (
    r"\.agents", "docs", "tools", "project_state", "audits",
    r"AGENTS\.md", r"CLAUDE\.md", r"CHANGELOG\.md", r"README\.md",
)


def backtick_path_re(root: Path | None = None) -> re.Pattern[str]:
    """Regex de caminho em prosa, com os caminhos declarados pelo projeto."""
    extra: list[str] = []
    if root is not None:
        policy = root / ".agents" / "policy" / "validator-scope.yaml"
        if policy.is_file():
            extra = [re.escape(value) for value in yaml_list(read(policy), "core_paths") if value]
    alternatives = "|".join((*PROTOCOL_PATH_PREFIXES, *extra))
    return re.compile(rf"`((?:{alternatives})[A-Za-z0-9_./§ -]*?)`")
SCOPE_BIND = re.compile(
    r"(?:somente|apenas|s[oó]|exclusivamente)\s+para\s+(T-\d{3})"
    r"|(?:nesta|desta)\s+passagem[^\n.]{0,100}?(T-\d{3})"
    r"|atualiza[^\n.]{0,80}?somente\s+para\s+(T-\d{3})"
    r"|at[eé]\s+(?:o\s+)?fechamento\s+de\s+(T-\d{3})",
    re.I,
)
SUPERSEDED_STATUS = re.compile(
    r"(?:substitu[ií]da|revogada)\s+por\s+(D-\d+)"
    r"|parcialmente-revogada\s+por\s+(D-\d+)",
    re.I,
)
DISMISSAL = re.compile(
    r"aposentad|invalid|obsolet|deprecat|destru[ií]|destroyed|legado|fallback|"
    r"compatib|congelad|hist[oó]ric|n[aã]o usar|alias|substitu[ií]d|"
    r"revogad|antes\s+d[eo]|at[eé]\s+ent[aã]o|migr|n[aã]o\s+como|"
    r"s[oó]\s+fallback|fora\s+de\s+vigor|n[aã]o\s+vigente",
    re.I,
)
TERMINAL_PLAN = re.compile(
    r"\b(conclu[ií]d[oa]|implementado|cancelad[oa]|arquivad[oa]|"
    r"pausad[oa]|bloquead[oa]|cumprid[oa])\b",
    re.I,
)
ACTIVE_PLAN = re.compile(r"\b(em\s+execu[cç][aã]o|propost[oa]|aprovad[oa])\b", re.I)
OPEN_FINDING_MARK = re.compile(
    r"RESOLVIDO|PARCIAL|superado-por|Resolvido em:|\*\*Resolu[cç]",
    re.I,
)


def _git(root: Path, *args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True, timeout=30,
        )
        if out.returncode != 0:
            return None
        return out.stdout.decode("utf-8", errors="replace")
    except (OSError, subprocess.SubprocessError):
        return None


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _parse_decisions(text: str) -> dict[str, dict]:
    parts = DECISION_SPLIT.split(text)
    out: dict[str, dict] = {}
    for i in range(1, len(parts), 2):
        did, body = parts[i], parts[i + 1]
        title = body.split("\n", 1)[0].strip(" —").strip()
        status_m = STATUS_LINE.search(body)
        status = status_m.group(1).split("|", 1)[0].strip() if status_m else ""
        impacto_m = IMPACTO_LINE.search(body)
        subst_m = SUBST_LINE.search(body)
        data_m = DATA_LINE.search(body)
        out[did] = {
            "title": title,
            "status": status,
            "body": body,
            "impacto": impacto_m.group(1).strip() if impacto_m else "",
            "subst": subst_m.group(1).strip() if subst_m else "",
            "date": data_m.group(1) if data_m else None,
            "line": text[: text.find(f"## {did}")].count("\n") + 1 if f"## {did}" in text else None,
        }
    return out


def _parse_findings(text: str) -> dict[str, dict]:
    parts = FINDING_SPLIT.split(text)
    out: dict[str, dict] = {}
    for i in range(1, len(parts), 2):
        fid, body = parts[i], parts[i + 1]
        title = body.split("\n", 1)[0]
        data_m = DATA_LINE.search(body)
        open_ = OPEN_FINDING_MARK.search(title) is None and OPEN_FINDING_MARK.search(body) is None
        # Permanent constraints without resolution markers but with "Consequência" and no bug tone:
        # still count as open for stale warning only when explicitly lacking closure.
        out[fid] = {
            "title": title.strip(),
            "body": body,
            "date": data_m.group(1) if data_m else None,
            "open": open_,
            "line": text[: text.find(f"## {fid}")].count("\n") + 1 if f"## {fid}" in text else None,
        }
    return out


def _concluded_tasks(root: Path) -> set[str]:
    done: set[str] = set()
    ws_dir = root / "project_state" / "workstreams"
    if not ws_dir.is_dir():
        return done
    for state in ws_dir.glob("*/STATE.md"):
        text = read(state)
        for m in TASK_RE.finditer(text):
            if "conclu" in m.group(3).lower() or (
                m.group(1) == "x" and "cancel" not in m.group(3).lower()
            ):
                # Prefer explicit concluída in the state column.
                if "conclu" in m.group(0).lower():
                    done.add(m.group(2))
                elif m.group(1) == "x" and "em andamento" not in m.group(0).lower():
                    done.add(m.group(2))
    return done


def _claimed_plans(root: Path) -> set[str]:
    claimed: set[str] = set()
    ws_dir = root / "project_state" / "workstreams"
    if not ws_dir.is_dir():
        return claimed
    for state in ws_dir.glob("*/STATE.md"):
        text = read(state)
        fm, _ = split_frontmatter(text)
        plan = yaml_scalar(fm, "active_plan")
        if plan and plan.strip().lower() not in {"", "null", "none", "—", "-"}:
            claimed.add(plan.strip())
        for m in TASK_RE.finditer(text):
            if any(s in m.group(0).lower() for s in ("aberta", "em andamento", "bloqueada", "parcial")):
                claimed.update(PLAN_ID_RE.findall(m.group(0)))
    return claimed


def _plan_is_live(status: str) -> bool:
    """Status de plano ainda em curso — âncora no início da linha (não no meio)."""
    return bool(re.match(
        r"^(em\s+execu[cç][aã]o|propost[oa]|aprovad[oa])\b",
        status.strip(),
        re.I,
    ))


def _nullish(value: str | None) -> bool:
    return value is None or value.strip().lower() in {"", "null", "none", "—", "-"}


def _body_bullets(text: str, heading: str) -> list[str]:
    """Itens `- …` sob um heading markdown de nível 2."""
    m = re.search(
        rf"^## {re.escape(heading)}\s*\n(.*?)(?=^## |\Z)",
        text, re.M | re.S,
    )
    if not m:
        return []
    return [
        item.strip().strip("\"'")
        for item in re.findall(r"^-\s+(.+)$", m.group(1), re.M)
        if item.strip() and item.strip() not in {"nenhum", "[]", "—", "-"}
    ]


def _all_events(root: Path) -> list[dict]:
    events: list[dict] = []
    ws_dir = root / "project_state" / "workstreams"
    if not ws_dir.is_dir():
        return events
    for ledger in ws_dir.glob("*/EVENTS.jsonl"):
        text, _enc = read_ledger(ledger)
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(ev, dict):
                events.append(ev)
    return events


def check_ledger_encoding(root: Path, report: Report) -> None:
    """Ledger deve ser UTF-8 puro — híbrido/UTF-16 cega o validador (F-027)."""
    ws_dir = root / "project_state" / "workstreams"
    if not ws_dir.is_dir():
        return
    for ledger in sorted(ws_dir.glob("*/EVENTS.jsonl")):
        raw = ledger.read_bytes()
        report.checked += 1
        _text, enc = decode_bytes(raw)
        if enc in {"utf-8", "utf-8-sig"}:
            # C1 controls (ex. U+0097 de em-dash CP1252 mal promovido) também reprovam.
            if any(0x80 <= ord(ch) <= 0x9F for ch in _text):
                report.error(
                    "state::ledger-encoding",
                    rel(ledger, root),
                    "EVENTS.jsonl UTF-8 contém controles C1 (U+0080–U+009F) — "
                    "transcodificação corrupta.",
                    "Restaure o caractere (ex. U+2014 —) e regrave como UTF-8 (D-062/F-027).",
                )
            continue
        report.error(
            "state::ledger-encoding",
            rel(ledger, root),
            f"EVENTS.jsonl em encoding {enc!r}; o validador exige UTF-8.",
            "Normalize para UTF-8 sob D-062 (decode por BOM/linha) e registre currency_change.",
        )


def _retired_values(project_md: str) -> list[str]:
    if "## Fatos canônicos" not in project_md:
        return []
    sec = project_md.split("## Fatos canônicos", 1)[1].split("\n## ", 1)[0]
    values: list[str] = []
    for line in sec.splitlines():
        if not line.startswith("|") or "Aposentado" in line or set(line.replace("|", "").strip()) <= {"-", " "}:
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 4:
            continue
        apo = cols[3]
        if not apo or apo.startswith("—") or apo == "-":
            continue
        for m in re.finditer(r"`([^`]+)`|\"([^\"]+)\"|'([^']+)'", apo):
            val = next(g for g in m.groups() if g)
            val = val.split("(", 1)[0].strip()
            if val and val not in values:
                values.append(val)
        # Bare token VLAEG 2.0 (sem aspas) na coluna.
        bare = re.sub(r"`[^`]+`|\"[^\"]+\"|'[^']+'|\([^)]*\)", "", apo)
        for part in re.split(r"\s*/\s*", bare):
            part = part.strip(" ,;")
            if part in {"VLAEG 2.0"} and part not in values:
                values.append(part)
    # Longer first to avoid partial double-counts in reporting.
    return sorted(values, key=len, reverse=True)


def _is_dismissed(text: str, start: int, end: int) -> bool:
    window = text[max(0, start - 160): min(len(text), end + 160)]
    return DISMISSAL.search(window) is not None


def _events_cover(events: list[dict], entity: str) -> bool:
    for ev in events:
        if ev.get("type") not in {"currency_change", "status_change", "decision", "finding"}:
            continue
        blob = f"{ev.get('summary', '')} {ev.get('detail', '')} {ev.get('task', '')}"
        if entity not in blob:
            continue
        if ev.get("type") == "currency_change":
            return True
        detail = str(ev.get("detail") or "")
        if "Motivo" in detail or "motivo" in detail.lower() or "reason" in detail.lower():
            return True
    return False


def check_supersede_reciprocity(decisions: dict[str, dict], report: Report) -> None:
    for did, meta in decisions.items():
        blob = f"{meta['status']} {meta['subst']}"
        for m in SUPERSEDED_STATUS.finditer(blob):
            other = next(g for g in m.groups() if g)
            report.checked += 1
            other_meta = decisions.get(other)
            if not other_meta:
                report.error(
                    "state::decision-supersede-reciprocity",
                    "project_state/DECISIONS.md",
                    f"{did} declara relação com {other}, mas {other} não existe.",
                    f"Crie {other} ou corrija a referência em {did}.",
                    meta["line"],
                )
                continue
            back = f"{other_meta['status']} {other_meta['subst']} {other_meta['body'][:400]}"
            if did not in back:
                report.error(
                    "state::decision-supersede-reciprocity",
                    "project_state/DECISIONS.md",
                    f"{did} diz relação com {other}, mas {other} não cita {did} de volta.",
                    f"Atualize o Status ou Substitui/substituída por de {other}.",
                    other_meta["line"],
                )
        # Direção inversa: "substitui/revoga D-Y" no campo Substitui de quem prevalece.
        for m in re.finditer(r"(?:substitui|revoga)\s+(D-\d+)", meta["subst"], re.I):
            other = m.group(1)
            if other == did:
                continue
            report.checked += 1
            other_meta = decisions.get(other)
            if not other_meta:
                continue
            back = f"{other_meta['status']} {other_meta['subst']}"
            if did not in back and not SUPERSEDED_STATUS.search(other_meta["status"]):
                # D-Y deve reconhecer a revogação/substituição.
                if did not in back:
                    report.error(
                        "state::decision-supersede-reciprocity",
                        "project_state/DECISIONS.md",
                        f"{did} declara que substitui/revoga {other}, sem reciprocidade em {other}.",
                        f"Marque {other} como substituída/revogada por {did}.",
                        other_meta["line"],
                    )


def check_scope_expired(
    decisions: dict[str, dict], concluded: set[str], report: Report,
) -> None:
    for did, meta in decisions.items():
        status = meta["status"].strip()
        if not re.match(r"ativa\b", status, re.I):
            continue
        for m in SCOPE_BIND.finditer(meta["body"]):
            tid = next(g for g in m.groups() if g)
            report.checked += 1
            if tid in concluded:
                report.error(
                    "state::decision-scope-expired",
                    "project_state/DECISIONS.md",
                    f"{did} está ativa mas limita escopo a {tid}, já concluída.",
                    f"Marque {did} como expirada-por-escopo ({tid}) e registre currency_change.",
                    meta["line"],
                )


def check_canon_retired(root: Path, report: Report) -> None:
    """Varre docs operacionais vivos — não o ledger histórico.

    DECISIONS/FINDINGS/plans/EVIDENCE registram o passado e citam valores
    aposentados por desenho. A contradição que importa é repetir o valor
    aposentado em norma viva (docs/rules, PROJECT, índice) como se vigorasse.
    """
    proj = root / "project_state" / "PROJECT.md"
    if not proj.is_file():
        return
    retired = _retired_values(read(proj))
    if not retired:
        return

    targets: list[Path] = []
    rules = root / "docs" / "rules"
    if rules.is_dir():
        targets.extend(p for p in rules.rglob("*") if p.is_file())
    targets.append(proj)
    ws_index = root / "project_state" / "WORKSTREAMS.md"
    if ws_index.is_file():
        targets.append(ws_index)

    for path in targets:
        if path.suffix.lower() not in {".md", ".yaml", ".yml", ".txt"}:
            continue
        text = read(path)
        # Em PROJECT.md, a coluna Aposentado da tabela de fatos é a SSOT — não flagra.
        if path.resolve() == proj.resolve() and "## Fatos canônicos" in text:
            head, rest = text.split("## Fatos canônicos", 1)
            tail = rest.split("\n## ", 1)
            mid = tail[0]
            # Zera células da coluna Aposentado para a varredura.
            cleaned_rows = []
            for line in mid.splitlines():
                if line.startswith("|") and "Aposentado" not in line and not (
                    set(line.replace("|", "").strip()) <= {"-", " "}
                ):
                    cols = line.strip("|").split("|")
                    if len(cols) >= 4:
                        cols[3] = " "
                        line = "|" + "|".join(cols) + "|"
                cleaned_rows.append(line)
            text = head + "## Fatos canônicos" + "\n".join(cleaned_rows)
            if len(tail) > 1:
                text += "\n## " + tail[1]
        p = rel(path, root)
        for val in retired:
            start = 0
            while True:
                idx = text.find(val, start)
                if idx < 0:
                    break
                report.checked += 1
                if not _is_dismissed(text, idx, idx + len(val)):
                    line = text[:idx].count("\n") + 1
                    report.error(
                        "state::canon-retired-value",
                        p,
                        f"Valor aposentado {val!r} aparece como se ainda vigorasse.",
                        "Remova, reescreva com o valor vigente, ou cite-o só como aposentado "
                        "(invalidado/legado/fallback) — ver PROJECT.md § Fatos canônicos.",
                        line,
                    )
                start = idx + len(val)


def check_impact_paths(root: Path, decisions: dict[str, dict],
                       findings: dict[str, dict], report: Report) -> None:
    placeholder = re.compile(r"<|\*|\bNNN\b|§|\.\.\.")
    backtick_path = backtick_path_re(root)

    def check_impacto(oid: str, impacto: str, line: int | None, path: str) -> None:
        if not impacto:
            return
        for m in backtick_path.finditer(impacto):
            raw = m.group(1).strip()
            target = re.split(r"[§#]", raw, 1)[0].strip().rstrip("/")
            target = target.split(" (", 1)[0].strip()
            if not target or placeholder.search(target):
                continue
            # Comando com flags ou argumentos — não é caminho.
            if " " in target or "--" in target:
                continue
            if "/" not in target and not re.search(r"\.\w+$", target) and target not in {
                "AGENTS.md", "CLAUDE.md", "CHANGELOG.md",
            }:
                continue
            report.checked += 1
            resolved = root / target
            if not resolved.exists():
                report.error(
                    "state::impact-path-missing",
                    path,
                    f"{oid} Impacto cita '{target}', que não existe.",
                    "Corrija o caminho no Impacto ou crie o alvo.",
                    line,
                )

    for did, meta in decisions.items():
        check_impacto(did, meta["impacto"], meta["line"], "project_state/DECISIONS.md")
    for fid, meta in findings.items():
        impacto_m = IMPACTO_LINE.search(meta["body"])
        if not impacto_m:
            continue
        check_impacto(fid, impacto_m.group(1), meta["line"], "project_state/FINDINGS.md")


def check_future_dates(root: Path, decisions: dict[str, dict],
                       findings: dict[str, dict], report: Report) -> None:
    today = _today()

    def flag(path: str, label: str, raw: str, line: int | None = None) -> None:
        try:
            d = datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            return
        report.checked += 1
        if d > today:
            report.error(
                "state::future-date",
                path,
                f"{label} tem data futura {raw} (hoje UTC {today.isoformat()}).",
                "Corrija a data para o dia real do registro.",
                line,
            )

    for did, meta in decisions.items():
        if meta["date"]:
            flag("project_state/DECISIONS.md", did, meta["date"], meta["line"])
    for fid, meta in findings.items():
        if meta["date"]:
            flag("project_state/FINDINGS.md", fid, meta["date"], meta["line"])

    ws_dir = root / "project_state" / "workstreams"
    if ws_dir.is_dir():
        for state in ws_dir.glob("*/STATE.md"):
            fm, body = split_frontmatter(read(state))
            p = rel(state, root)
            for key in ("created_at", "updated_at"):
                raw = yaml_scalar(fm, key)
                if raw:
                    flag(p, key, raw[:10])
            for m in ISO_TS.finditer(fm + "\n" + body[:2000]):
                # Evita varrer evidências inteiras; frontmatter + cabeçalho bastam.
                if m.start() < len(fm) + 500:
                    flag(p, "registro", m.group(1))

    for ev in _all_events(root):
        ts = str(ev.get("ts") or "")
        m = ISO_TS.match(ts)
        if m:
            flag("EVENTS.jsonl", f"evento {ev.get('type')}", m.group(1))


def check_currency_unlogged(root: Path, report: Report) -> None:
    """Transição de Status na working tree (vs HEAD) sem evento com motivo.

    Só a árvore suja: exigir evento para todo HEAD~1…HEAD histórico
    reprovaria o ledger legado. A obrigação é prospectiva (D-059 / T-178).
    """
    events = _all_events(root)

    def compare_maps(before: dict[str, str], after: dict[str, str],
                     path: str) -> None:
        for eid in set(before) | set(after):
            if before.get(eid) == after.get(eid):
                continue
            report.checked += 1
            if not _events_cover(events, eid):
                report.error(
                    "state::currency-change-unlogged",
                    path,
                    f"Transição de status de {eid} sem evento "
                    f"currency_change/status_change com motivo "
                    f"({before.get(eid)!r} -> {after.get(eid)!r}).",
                    "Grave type=currency_change (ou status_change legado com Motivo) "
                    "no EVENTS.jsonl.",
                )

    for rel_path, parse in (
        ("project_state/DECISIONS.md",
         lambda t: {k: v["status"] for k, v in _parse_decisions(t).items()}),
        ("project_state/FINDINGS.md",
         lambda t: {
             k: ("aberto" if v["open"] else "fechado")
             for k, v in _parse_findings(t).items()
         }),
    ):
        path = root / rel_path
        if not path.is_file():
            continue
        head_text = _git(root, "show", f"HEAD:{rel_path}")
        if head_text is None:
            continue
        compare_maps(parse(head_text), parse(read(path)), rel_path)

    ws_dir = root / "project_state" / "workstreams"
    if not ws_dir.is_dir():
        return
    for state in ws_dir.glob("*/STATE.md"):
        fm, _ = split_frontmatter(read(state))
        ws_id = (yaml_scalar(fm, "id") or "").strip()
        status = (yaml_scalar(fm, "status") or "").strip()
        if not ws_id:
            continue
        rel_state = rel(state, root).replace("\\", "/")
        head_text = _git(root, "show", f"HEAD:{rel_state}")
        if head_text is None:
            continue
        ofm, _ = split_frontmatter(head_text)
        compare_maps(
            {(yaml_scalar(ofm, "id") or ws_id).strip():
             (yaml_scalar(ofm, "status") or "").strip()},
            {ws_id: status},
            rel_state,
        )


def check_finding_stale(findings: dict[str, dict], events: list[dict],
                        report: Report) -> None:
    today = _today()
    cutoff = today - timedelta(days=STALE_DAYS)
    for fid, meta in findings.items():
        if not meta["open"] or not meta["date"]:
            continue
        try:
            d = datetime.strptime(meta["date"], "%Y-%m-%d").date()
        except ValueError:
            continue
        report.checked += 1
        if d > cutoff:
            continue
        cited = any(fid in f"{e.get('summary', '')} {e.get('detail', '')}" for e in events)
        if not cited:
            report.warn(
                "state::finding-stale",
                "project_state/FINDINGS.md",
                f"{fid} aberto há mais de {STALE_DAYS} dias sem evento que o cite.",
                "Revalide, feche com evidência, ou registre evento de revisão.",
                meta["line"],
            )


def check_ws_paused_stale(root: Path, report: Report) -> None:
    today = _today()
    cutoff = today - timedelta(days=STALE_DAYS)
    ws_dir = root / "project_state" / "workstreams"
    if not ws_dir.is_dir():
        return
    for state in ws_dir.glob("*/STATE.md"):
        fm, _ = split_frontmatter(read(state))
        status = (yaml_scalar(fm, "status") or "").strip().lower()
        if status not in {"paused", "blocked"}:
            continue
        updated = yaml_scalar(fm, "updated_at") or yaml_scalar(fm, "created_at") or ""
        report.checked += 1
        try:
            d = datetime.strptime(updated[:10], "%Y-%m-%d").date()
        except ValueError:
            continue
        if d <= cutoff:
            report.warn(
                "state::ws-paused-stale",
                rel(state, root),
                f"Workstream {status} há mais de {STALE_DAYS} dias sem revisão "
                f"(updated_at={updated[:10]}).",
                "Retome, cancele, ou registre revisão com updated_at novo.",
            )


def check_plan_orphan(root: Path, claimed: set[str], report: Report) -> None:
    plans = root / "project_state" / "plans"
    if not plans.is_dir():
        return
    for pl in sorted(plans.glob("PLAN-*.md")):
        text = read(pl)
        status_m = re.search(r"^\*\*Status:\*\*\s*([^\n]+)", text, re.M)
        status = status_m.group(1).strip() if status_m else ""
        pid_m = re.match(r"(PLAN-\d+)", pl.name)
        if not pid_m:
            continue
        pid = pid_m.group(1)
        report.checked += 1
        if pid in claimed:
            continue
        # Terminal só silencia se não estiver "em curso" pelo helper único (R2/G11).
        if TERMINAL_PLAN.search(status) and not _plan_is_live(status):
            continue
        if _plan_is_live(status) or not status:
            report.warn(
                "state::plan-orphan",
                rel(pl, root),
                f"{pid} sem workstream que o reivindique e sem status terminal ({status!r}).",
                "Ligue a uma WS (active_plan/tarefa) ou marque status terminal.",
            )


def check_changelog_stale(root: Path, decisions: dict[str, dict], report: Report) -> None:
    changelog = root / "CHANGELOG.md"
    report.checked += 1
    if not changelog.is_file():
        report.warn(
            "state::changelog-stale",
            "CHANGELOG.md",
            "CHANGELOG.md ausente — consolidação de decisões sem destino.",
            "Crie CHANGELOG.md e consolide as decisões recentes.",
        )
        return
    text = read(changelog)
    mentioned = set(DEC_ID_RE.findall(text))
    # Distância: decisões cujo ID numérico é maior que a maior citada no changelog.
    def num(did: str) -> int:
        return int(did.split("-", 1)[1])

    if not decisions:
        return
    max_dec = max(num(d) for d in decisions)
    max_logged = max((num(d) for d in mentioned), default=0)
    gap = max_dec - max_logged
    if gap > CHANGELOG_DECISION_GAP:
        report.warn(
            "state::changelog-stale",
            "CHANGELOG.md",
            f"Mais de {CHANGELOG_DECISION_GAP} decisões desde a última consolidação "
            f"(gap={gap}: D-{max_logged:03d}…D-{max_dec:03d}).",
            "Consolide as decisões recentes no CHANGELOG.md.",
        )


def check_decision_cluster(decisions: dict[str, dict], report: Report) -> None:
    """Aviso: 3+ decisões ativas com o mesmo bigrama de título, sem consolidadora."""
    active = {
        did: meta for did, meta in decisions.items()
        if re.match(r"ativa\b", meta["status"].strip(), re.I)
    }
    buckets: dict[str, list[str]] = defaultdict(list)
    stop = {
        "a", "o", "os", "as", "de", "da", "do", "das", "dos", "e", "em", "no", "na",
        "para", "com", "por", "um", "uma", "como", "ao", "à", "the", "and",
    }
    for did, meta in active.items():
        words = [
            w for w in re.findall(r"[a-zà-ü0-9]+", meta["title"].lower())
            if w not in stop and len(w) > 3
        ]
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i + 1]}"
            buckets[bigram].append(did)
    report.checked += 1
    seen_groups: set[frozenset[str]] = set()
    for bigram, ids in buckets.items():
        uniq = sorted(set(ids))
        if len(uniq) < 3:
            continue
        key = frozenset(uniq)
        if key in seen_groups:
            continue
        seen_groups.add(key)
        bodies = " ".join(active[i]["body"][:300].lower() for i in uniq)
        if "consolida" in bodies:
            continue
        report.warn(
            "state::decision-cluster",
            "project_state/DECISIONS.md",
            f"{len(uniq)} decisões ativas no tema {bigram!r}: {', '.join(uniq)}.",
            "Considere uma decisão consolidadora ou marque as cobertas como substituídas.",
        )


def check_frozen_banners(root: Path, report: Report) -> None:
    for rel_root in FROZEN_ROOTS:
        base = root / rel_root
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            raw = path.read_bytes()
            if b"\x00" in raw[:1024]:
                continue
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                continue
            report.checked += 1
            first = text.splitlines()[0] if text else ""
            if not FROZEN_BANNER.match(first):
                report.error(
                    "state::frozen-no-banner",
                    rel(path, root),
                    "Arquivo congelado sem banner vlaeg:frozen na primeira linha.",
                    'Insira <!-- vlaeg:frozen at=AAAA-MM-DD by=D-NNN reason="..." --> '
                    "como primeira linha (D-040 / state-currency.md).",
                    1,
                )


def check_plan_duplicate(root: Path, report: Report) -> None:
    """Mesmo arquivo de plano (basename) em dois caminhos vivos reprova."""
    scope = excluded_parts(root)
    locations: dict[str, list[Path]] = defaultdict(list)
    for path in walk_files(root, {".md"}, scope):
        if not re.match(r"PLAN-\d+", path.name):
            continue
        if "anexos" in path.parts:
            continue
        locations[path.name].append(path)

    for name, paths in sorted(locations.items()):
        if len(paths) < 2:
            continue
        report.checked += 1
        live = []
        for path in paths:
            text = read(path)
            first = text.splitlines()[0] if text else ""
            if not FROZEN_BANNER.match(first):
                live.append(path)
        if len(live) >= 2:
            shown = ", ".join(rel(p, root) for p in live)
            report.error(
                "state::plan-duplicate",
                rel(live[0], root),
                f"{name} aparece em {len(live)} caminhos vivos sem banner: {shown}.",
                "Congelé a cópia histórica com vlaeg:frozen ou remova o duplicado.",
            )


def _ws_rows(root: Path) -> list[dict]:
    """Retrato por workstream (STATE.md + propostas só no índice)."""
    rows: list[dict] = []
    seen: set[str] = set()
    ws_dir = root / "project_state" / "workstreams"
    if ws_dir.is_dir():
        for state in sorted(ws_dir.glob("*/STATE.md")):
            text = read(state)
            fm, _ = split_frontmatter(text)
            ws_id = (yaml_scalar(fm, "id") or state.parent.name.split("-")[0]).strip()
            status = (yaml_scalar(fm, "status") or "?").strip()
            plan_raw = yaml_scalar(fm, "active_plan")
            plan = "—" if _nullish(plan_raw) else plan_raw.strip()
            tasks = yaml_list(fm, "active_tasks") if fm else []
            task = ", ".join(tasks) if tasks else "—"
            title = (yaml_scalar(fm, "title") or "").strip()
            obj = (yaml_scalar(fm, "objective") or title or "").strip()
            note = obj[:80] + ("…" if len(obj) > 80 else "") if obj else "—"
            rows.append({
                "id": ws_id, "status": status, "plan": plan,
                "task": task or "—", "note": note,
            })
            seen.add(ws_id)

    index = root / "project_state" / "WORKSTREAMS.md"
    if index.is_file():
        text = read(index)
        section = re.search(
            r"^## Propostas\s*\n(.*?)(?=^## |\Z)", text, re.M | re.S,
        )
        if section:
            for m in re.finditer(
                r"\|\s*(?:\[)?(WS-\d+)(?:\]\([^)]*\))?\s*\|\s*([^|]+)\|",
                section.group(1),
            ):
                ws_id = m.group(1)
                if ws_id in seen:
                    continue
                rows.append({
                    "id": ws_id,
                    "status": "proposed",
                    "plan": "—",
                    "task": "—",
                    "note": m.group(2).strip()[:80],
                })
                seen.add(ws_id)
    return rows


def _plan_status_map(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    plans = root / "project_state" / "plans"
    if not plans.is_dir():
        return out
    for path in sorted(plans.glob("PLAN-*.md")):
        if "anexos" in path.parts:
            continue
        text = read(path)
        first = text.splitlines()[0] if text else ""
        if FROZEN_BANNER.match(first):
            continue
        m = re.search(r"^\*\*Status:\*\*\s*([^\n]+)", text, re.M)
        pid = PLAN_ID_RE.search(path.name)
        if pid and m:
            out[pid.group(0)] = m.group(1).strip()
    return out


def _bucket_decisions(decisions: dict[str, dict]) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = {
        "ativa": [],
        "parcialmente-revogada": [],
        "expirada-por-escopo": [],
        "substituída/revogada": [],
        "histórica": [],
        "outro": [],
    }
    for did, meta in sorted(decisions.items(), key=lambda x: x[0]):
        st = meta["status"].strip().lower()
        if re.match(r"ativa\b", st):
            buckets["ativa"].append(did)
        elif "parcialmente-revogad" in st:
            buckets["parcialmente-revogada"].append(did)
        elif "expirad" in st:
            buckets["expirada-por-escopo"].append(did)
        elif re.search(r"substitu[ií]d|revogad", st):
            buckets["substituída/revogada"].append(did)
        elif "histór" in st or "histor" in st:
            buckets["histórica"].append(did)
        else:
            buckets["outro"].append(did)
    return buckets


def build_inventory(root: Path, report: Report | None = None) -> str:
    """Retrato SSOT no formato §8 da auditoria round 5 (T-182)."""
    ps = root / "project_state"
    decisions_text = read(ps / "DECISIONS.md") if (ps / "DECISIONS.md").is_file() else ""
    findings_text = read(ps / "FINDINGS.md") if (ps / "FINDINGS.md").is_file() else ""
    decisions = _parse_decisions(decisions_text) if decisions_text else {}
    findings = _parse_findings(findings_text) if findings_text else {}
    claimed = _claimed_plans(root)
    plans = _plan_status_map(root)
    rows = _ws_rows(root)

    lines: list[str] = [
        "## Inventário de vigência",
        "",
        "Retrato da SSOT no formato §8 da auditoria round 5 "
        "(`audits/round5/auditoria-vigencia-do-estado.md`).",
        "",
        "### 8.1 Workstreams",
        "",
        "| ID | Status | Plano | Tarefa atual | Observação |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['id']} | `{row['status']}` | {row['plan']} | "
            f"{row['task']} | {row['note']} |"
        )

    lines += ["", "### 8.2 Planos vigentes", ""]
    claimed_sorted = sorted(claimed)
    if claimed_sorted:
        lines.append(
            "Reivindicados por workstream: "
            + " · ".join(f"`{p}`" for p in claimed_sorted)
        )
    active_plans = [
        pid for pid, st in sorted(plans.items())
        if _plan_is_live(st) and pid not in claimed
    ]
    if active_plans:
        lines.append(
            "Com status ativo sem WS: "
            + " · ".join(f"`{p}` ({plans[p]})" for p in active_plans)
        )
    if not claimed_sorted and not active_plans:
        lines.append("_nenhum_")

    buckets = _bucket_decisions(decisions)
    lines += ["", "### 8.3 Decisões em vigor, por status", ""]
    labels = [
        ("ativa", "Em vigor (`ativa`)"),
        ("parcialmente-revogada", "Parcialmente-revogadas"),
        ("expirada-por-escopo", "Expiradas por escopo"),
        ("substituída/revogada", "Substituídas/revogadas (registro)"),
        ("histórica", "Históricas"),
        ("outro", "Outro status"),
    ]
    for key, label in labels:
        ids = buckets[key]
        if not ids:
            continue
        lines.append(f"- **{label}:** " + ", ".join(f"`{i}`" for i in ids))

    open_f = sorted(fid for fid, meta in findings.items() if meta["open"])
    closed_f = sorted(fid for fid, meta in findings.items() if not meta["open"])
    lines += ["", "### 8.4 Findings ainda válidos", ""]
    if open_f:
        lines.append(", ".join(f"`{f}`" for f in open_f) + ".")
    else:
        lines.append("_nenhum finding aberto_.")
    if closed_f:
        lines.append(
            "Resolvidos/marcados: " + ", ".join(f"`{f}`" for f in closed_f) + "."
        )

    lines += ["", "### 8.5 Pendências relevantes", ""]
    if report and report.issues:
        for i, issue in enumerate(report.issues, 1):
            tag = "erro" if issue.severity == "error" else "aviso"
            lines.append(f"{i}. [{tag}] `{issue.check}` — {issue.message}")
    else:
        lines.append("_nenhuma pendência detectada pela passagem de vigência_.")

    lines += ["", "### 8.6 Riscos abertos", ""]
    risk_lines: list[str] = []
    ws_dir = root / "project_state" / "workstreams"
    if ws_dir.is_dir():
        for state in sorted(ws_dir.glob("*/STATE.md")):
            text = read(state)
            fm, _ = split_frontmatter(text)
            ws_id = yaml_scalar(fm, "id") or state.parent.name
            status = (yaml_scalar(fm, "status") or "").strip()
            if status not in {"active", "paused", "blocked"}:
                continue
            items: list[str] = []
            m = re.search(r"^risks:\s*\n((?:[ \t]*-[ \t].+\n?)*)", fm, re.M)
            if m:
                items.extend(
                    item.strip().strip("\"'")
                    for item in re.findall(r"^-\s+(.+)$", m.group(1), re.M)
                    if item.strip() and item.strip() not in {"[]", "nenhum", "-", "—"}
                )
            items.extend(_body_bullets(text, "Riscos abertos"))
            for item in items:
                risk_lines.append(f"- `{ws_id}`: {item}")
    if risk_lines:
        lines.extend(risk_lines)
    else:
        lines.append("_nenhum risco declarado em STATE.md de WS ativa/pausada/bloqueada_.")

    lines += ["", "### 8.7 Dependências ativas", ""]
    lines.append("| Dependência | Bloqueia | Natureza |")
    lines.append("|---|---|---|")
    dep_rows = 0
    if ws_dir.is_dir():
        for state in sorted(ws_dir.glob("*/STATE.md")):
            text = read(state)
            fm, _ = split_frontmatter(text)
            ws_id = yaml_scalar(fm, "id") or state.parent.name
            status = (yaml_scalar(fm, "status") or "").strip()
            if status not in {"active", "blocked"}:
                continue
            m = re.search(
                r"^open_questions:\s*\n((?:[ \t]*-[ \t].+\n?)*)", fm, re.M,
            )
            if m:
                for item in re.findall(r"^-\s+(.+)$", m.group(1), re.M):
                    item = item.strip().strip("\"'")
                    if item and item not in {"[]"}:
                        lines.append(f"| {item} | {ws_id} | questão aberta |")
                        dep_rows += 1
            for g in yaml_list(fm, "pending_gates"):
                lines.append(f"| gate `{g}` | {ws_id} | gate pendente |")
                dep_rows += 1
    if dep_rows == 0:
        lines.append("| — | — | nenhuma questão/gate pendente |")

    lines.append("")
    return "\n".join(lines)


def run(root: Path) -> Report:
    r = Report("currency")
    ps = root / "project_state"
    if not ps.is_dir():
        r.error("state::missing", "project_state",
                "Diretório de estado ausente — passagem de vigência não roda.",
                "Crie project_state/.")
        return r

    decisions_text = read(ps / "DECISIONS.md") if (ps / "DECISIONS.md").is_file() else ""
    findings_text = read(ps / "FINDINGS.md") if (ps / "FINDINGS.md").is_file() else ""
    decisions = _parse_decisions(decisions_text) if decisions_text else {}
    findings = _parse_findings(findings_text) if findings_text else {}
    concluded = _concluded_tasks(root)
    claimed = _claimed_plans(root)
    events = _all_events(root)

    check_supersede_reciprocity(decisions, r)
    check_scope_expired(decisions, concluded, r)
    check_canon_retired(root, r)
    check_impact_paths(root, decisions, findings, r)
    check_future_dates(root, decisions, findings, r)
    check_currency_unlogged(root, r)
    check_frozen_banners(root, r)
    check_plan_duplicate(root, r)
    check_ledger_encoding(root, r)

    check_finding_stale(findings, events, r)
    check_ws_paused_stale(root, r)
    check_plan_orphan(root, claimed, r)
    check_changelog_stale(root, decisions, r)
    check_decision_cluster(decisions, r)

    return r
