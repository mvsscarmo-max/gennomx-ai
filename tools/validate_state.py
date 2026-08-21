"""Valida o estado operacional: workstreams, tarefas, planos, decisoes, findings, ledger e handoffs."""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from _common import Report, read, read_ledger, rel, split_frontmatter, yaml_list, yaml_scalar

WS_STATUS = {"proposed", "active", "paused", "blocked", "completed", "cancelled"}
TASK_STATES = {"aberta", "em andamento", "bloqueada", "parcial", "concluída", "cancelada"}
EVENT_TYPES = {"user_message", "agent_message", "tool_call", "tool_result", "command_run",
               "test_run", "git_checkpoint", "decision", "finding", "status_change",
               "currency_change",
               "skill_selected", "skill_skipped", "gate_result", "handoff",
               "knowledge_proposed", "knowledge_approved", "divergence",
               "coordination_message", "coordination_ack", "coordination_claim",
               "coordination_conflict", "provider_status"}
AUTHORITIES = {"normative", "approved-decision", "verified-knowledge", "operational-state",
               "evidence", "hypothesis", "historical", "superseded"}
EVENT_REQUIRED = ["ts", "ws", "agent", "session", "task", "commit", "type", "authority", "origin", "summary", "detail"]
TASK_RE = re.compile(r"^- \[( |x)\] (T-\d{3}) — (.+)$", re.M)
EVIDENCE_RE = re.compile(r"^## (E-\d{3})\b.*?(?=^## E-\d{3}\b|\Z)", re.M | re.S)


@lru_cache(maxsize=None)
def _git_cached(root: str, args: tuple[str, ...]) -> str | None:
    """Executa uma consulta Git uma vez por raiz e conjunto de argumentos."""
    try:
        out = subprocess.run(["git", "-C", root, *args], capture_output=True,
                             text=True, timeout=20)
        return out.stdout.strip() if out.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def _git(root: Path, *args: str) -> str | None:
    return _git_cached(str(root.resolve()), tuple(args))


def _evidence_blocks(text: str) -> dict[str, str]:
    return {m.group(1): m.group(0) for m in EVIDENCE_RE.finditer(text)}


def _evidence_contract(block: str) -> list[str]:
    missing = []
    when = re.search(r"\*\*Quando:\*\*\s*([^·\n]+)", block)
    if not when:
        missing.append("timestamp")
    else:
        timestamp = when.group(1).strip()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", timestamp):
            missing.append("timestamp ISO 8601")
        else:
            try:
                datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                missing.append("timestamp ISO 8601")

    commit = re.search(r"\*\*(?:Repo commit|Commit):\*\*\s*`([0-9a-fA-F]{7,40}|none)`", block)
    if not commit:
        # `none` e o valor que o protocolo define para projeto sem controle de
        # versao (memory-model, campo commit do ledger). Exigir SHA aqui e no
        # ledger nao contradizia so a norma: tornava impossivel fechar tarefa
        # nesses projetos, apesar de o modo degradado ser piso de conformidade.
        # A evidencia continua exigindo comando, saida e timestamp.
        missing.append("commit Git exato, ou `none` em projeto sem controle de versao")

    consoles = re.findall(r"```console\s*\n(.*?)```", block, re.S)
    if not any(re.search(r"^\$\s+\S", console, re.M) for console in consoles):
        missing.append("comando")
    if not any(line for console in consoles for line in console.splitlines()
               if line.strip() and not line.lstrip().startswith("$")):
        missing.append("saída")
    return missing


def _evidence_commit(block: str) -> str | None:
    """SHA da evidencia, ou None quando ela declara `none`.

    None desliga as verificacoes de ancestralidade a jusante, em vez de reprovar
    o que nao existe em projeto sem controle de versao.
    """
    match = re.search(r"\*\*(?:Repo commit|Commit):\*\*\s*`([0-9a-fA-F]{7,40})`", block)
    return match.group(1) if match else None


def _plan_path(plans: Path, plan_id: str) -> Path | None:
    matches = sorted(plans.glob(f"{plan_id}-*.md")) if plans.is_dir() else []
    return matches[0] if len(matches) == 1 else None


@dataclass
class GateStatus:
    ok: bool
    reason: str
    artifact: str | None = None
    severity: str = "error"  # "error" | "warn"


_ROUND_IN_NAME = re.compile(r"round(\d+)\.md$")


def _latest_gate_artifact(workstream: Path, gate: str) -> tuple[int, Path] | None:
    """Ultima rodada selada de G11/G12 — so leitura historica (T-200)."""
    if gate == "G11":
        subdir, stem = "reviews", "impl-review-findings-round"
    elif gate == "G12":
        subdir, stem = "audits", "ai-ready-audit-round"
    else:
        return None
    base = workstream / subdir
    if not base.is_dir():
        return None
    found: list[tuple[int, Path]] = []
    for path in base.glob(f"**/{stem}*.md"):
        if "_inflight" in path.parts:
            continue
        match = _ROUND_IN_NAME.search(path.name)
        if match:
            found.append((int(match.group(1)), path))
    return max(found, key=lambda item: item[0]) if found else None


def _gate_status(workstream: Path, gate: str, evidence_text: str, *,
                 current_commit: str | None, closed: bool, root: Path | None = None):
    """Estado de um gate cujo artefato vive fora do EVIDENCE.md.

    G13/G14: norma 4.0 (D-064). G11/G12: so registro historico — aviso
    `gate-historical`, nunca erro (T-201).
    """
    if gate == "G5":
        ok = (re.search(r"\*\*Gate:\*\*[^\n]*\bG5\b", evidence_text) is not None
              and "**Resumo (1–3 frases):**" in evidence_text)
        return GateStatus(ok, "bloco de deslop no EVIDENCE.md"
                              if ok else "sem bloco proprio de G5 no EVIDENCE.md")
    if gate in ("G11", "G12"):
        hit = _latest_gate_artifact(workstream, gate)
        if hit:
            round_no, path = hit
            return GateStatus(
                True,
                f"{gate} aposentado (D-064); rodada {round_no} preservada "
                f"como registro historico"
                + (" de workstream fechada" if closed else ""),
                path.name,
                severity="warn",
            )
        return GateStatus(
            True,
            f"{gate} aposentado (D-064); sem artefato — irrelevante sob a 4.0",
            severity="warn",
        )
    if gate == "G13":
        ok = re.search(r"\*\*Gate:\*\*[^\n]*\bG13\b", evidence_text) is not None
        return GateStatus(
            ok,
            "bloco G13 no EVIDENCE.md (saida de tools/verify.py)"
            if ok else "sem bloco G13 no EVIDENCE.md — rode tools/verify.py "
            "e registre a saida, ou devolva G13 a pending_gates",
        )
    if gate == "G14":
        return _g14_status(evidence_text, root)
    return GateStatus(False, f"gate desconhecido: {gate}")


# Quem pode assinar G14 e uma DECLARACAO DO PROJETO, nao um nome fixo no
# validador: gravar a pessoa de um projeto aqui transforma uma escolha local em
# regra do protocolo, e reprova todo projeto que tenha outro responsavel.
# Os signatarios validos vem de `.agents/policy/validator-scope.yaml`, chave
# `g14_signers:`. Sem declaracao, valem os papeis genericos abaixo.
G14_HUMAN_FALLBACK = ("fundador", "responsavel", "responsável", "humano")


def g14_human_pattern(root: Path | None) -> "re.Pattern[str]":
    names = list(G14_HUMAN_FALLBACK)
    if root is not None:
        policy = root / ".agents" / "policy" / "validator-scope.yaml"
        if policy.is_file():
            declared = [value for value in yaml_list(read(policy), "g14_signers") if value]
            if declared:
                names = declared
    alternation = "|".join(re.escape(name) for name in names)
    return re.compile(r"\*\*Assinante:\*\*\s*.*\b(?:" + alternation + r")\b", re.I)
G14_AGENT = re.compile(
    r"\*\*Assinante:\*\*\s*.*\b(?:agente|agent-\d*|cursor|claude|opencode|codex|"
    r"harness|gpt-|grok|gemini)\b",
    re.I,
)
G14_ASSINANTE = re.compile(r"\*\*Assinante:\*\*\s*\S+", re.I)
RC_REF = re.compile(r"\*\*RC:\*\*\s*(AUD-\d+)\b", re.I)
RC_INFRA_ESCAPE = re.compile(
    r"\*\*(?:Escape INFRA|Destravamento INFRA):\*\*\s*(D-\d+)\b", re.I,
)
RC_CRITICAL_STATUS_OK = re.compile(
    r"-\s*Status:\s*(corrigido|enderecado|endereçado|fechado)\b", re.I,
)


def _g14_block(evidence_text: str) -> str | None:
    """Ultimo bloco de evidencia que declara Gate G14."""
    blocks = _evidence_blocks(evidence_text)
    hit = None
    for block in blocks.values():
        if re.search(r"\*\*Gate:\*\*[^\n]*\bG14\b", block):
            hit = block
    if hit:
        return hit
    if re.search(r"\*\*Gate:\*\*[^\n]*\bG14\b", evidence_text):
        return evidence_text
    return None


def _g14_status(evidence_text: str, root: Path | None = None) -> GateStatus:
    block = _g14_block(evidence_text)
    if not block:
        return GateStatus(
            False,
            "sem bloco de aceite G14 assinado no EVIDENCE.md",
        )
    if G14_AGENT.search(block):
        return GateStatus(
            False,
            "G14 assinado por agente — aceite e so humano (cycle-review.md §6)",
        )
    if not G14_ASSINANTE.search(block):
        return GateStatus(
            False,
            "bloco G14 sem **Assinante:** — fundador deve assinar",
        )
    if not g14_human_pattern(root).search(block):
        return GateStatus(
            False,
            "Assinante de G14 nao consta em g14_signers (validator-scope.yaml)",
        )
    # LIMITE DECLARADO: isto verifica que o bloco EXISTE e nomeia um signatario
    # declarado. Nao AUTENTICA ninguem — texto em Markdown e declaracao, nao
    # assinatura. A garantia de G14 vem do processo humano; o validador so impede
    # que ele seja esquecido ou assinado por agente. Ver VALIDATION.md secao 8.
    return GateStatus(True, "bloco de aceite G14 assinado por signatario declarado")


def _rc_requirement(evidence_text: str) -> tuple[bool, str, str | None]:
    """RC citada ou escape INFRA com D-NNN. Devolve (ok, motivo, aud_id|None)."""
    block = _g14_block(evidence_text) or evidence_text
    escape = RC_INFRA_ESCAPE.search(block)
    if escape:
        return True, f"escape INFRA via {escape.group(1)}", None
    ref = RC_REF.search(block)
    if ref:
        return True, f"RC {ref.group(1)} citada", ref.group(1)
    return (
        False,
        "RC ausente em risco >= 3 — cite **RC:** AUD-NNN no G14 "
        "(ou **Escape INFRA:** D-NNN)",
        None,
    )


def _rc_critical_open(root: Path, aud_id: str) -> str | None:
    """Se a auditoria RC ainda tem critico/prova-obrigatoria abertos, devolve motivo."""
    index = root / "project_state" / "AUDITS.md"
    if not index.is_file():
        return f"{aud_id} sem indice AUDITS.md"
    rows = _parse_audit_index(read(index))
    row = next((r for r in rows if r["id"] == aud_id), None)
    if not row:
        return f"{aud_id} nao indexada em AUDITS.md"
    target = (index.parent / row["href"]).resolve()
    if not target.is_file():
        return f"{aud_id} aponta para arquivo inexistente"
    text = read(target)
    verdict = re.search(r"^verdict:\s*(\S+)", text, re.M | re.I)
    if verdict and verdict.group(1).upper() in ("FIX_BEFORE_SHIP", "BLOCKED"):
        # Veredito bloqueante so passa se nao houver critico aberto abaixo.
        pass
    open_ids: list[str] = []
    for match in re.finditer(r"^###\s+(R-\d+)\b(.*?)(?=^###\s+R-\d+\b|\Z)",
                             text, re.M | re.S):
        body = match.group(2)
        classe = re.search(r"-\s*Classe:\s*(critico|prova-obrigatoria)\b", body, re.I)
        if not classe:
            continue
        if RC_CRITICAL_STATUS_OK.search(body):
            continue
        open_ids.append(match.group(1))
    if open_ids:
        return (f"{aud_id} tem achado critico/prova-obrigatoria aberto "
                f"({', '.join(open_ids)}) — corrija e rode G13; nunca aceite por decisao")
    if verdict and verdict.group(1).upper() in ("FIX_BEFORE_SHIP", "BLOCKED"):
        # Sem R-NN critico restante: veredito sozinho nao bloqueia se nao ha classe aberta.
        return None
    return None


def _sha_prefix_match(declared: str | None, expected: str | None) -> bool:
    if not declared or not expected:
        return False
    a, b = declared.lower().strip("`"), expected.lower().strip("`")
    return a == b or a.startswith(b) or b.startswith(a)


def _commit_reachable(root: Path, aud_commit: str, current_commit: str) -> bool:
    """True se o commit da RC e o tip ou ancestral dele (correcoes pos-RC)."""
    if _sha_prefix_match(aud_commit, current_commit):
        return True
    return _git(root, "merge-base", "--is-ancestor", aud_commit, current_commit) is not None


def _rc_identity(
    root: Path, aud_id: str, *, ws_id: str, current_commit: str | None,
) -> str | None:
    """Confere que AUD-NNN e a RC desta workstream — nao auditoria alheia."""
    index = root / "project_state" / "AUDITS.md"
    if not index.is_file():
        return f"{aud_id} sem indice AUDITS.md"
    rows = _parse_audit_index(read(index))
    row = next((r for r in rows if r["id"] == aud_id), None)
    if not row:
        return f"{aud_id} nao indexada em AUDITS.md"
    target = (index.parent / row["href"]).resolve()
    if not target.is_file():
        return f"{aud_id} aponta para arquivo inexistente"
    fm, body = split_frontmatter(read(target))
    if not fm:
        return f"{aud_id} sem frontmatter — identidade RC indemonstravel"
    tipo = (yaml_scalar(fm, "tipo") or "").strip().lower()
    if tipo != "revisao-de-ciclo":
        return (f"{aud_id} tem tipo '{tipo or '(ausente)'}' — G14 exige "
                f"tipo: revisao-de-ciclo")
    aud_ws = (yaml_scalar(fm, "ws") or "").strip()
    if not aud_ws or not (
        aud_ws == ws_id or aud_ws.startswith(ws_id + "-") or ws_id.startswith(aud_ws)
    ):
        return (f"{aud_id} declara ws '{aud_ws or '(ausente)'}' mas a workstream "
                f"e '{ws_id}'")
    aud_commit = (yaml_scalar(fm, "commit") or "").strip()
    if not aud_commit:
        return f"{aud_id} sem commit no frontmatter"
    if not current_commit:
        return f"{aud_id}: current_commit da WS ausente — nao da para amarrar a RC"
    if not _commit_reachable(root, aud_commit, current_commit):
        return (f"{aud_id} declara commit '{aud_commit}' que nao e ancestral de "
                f"current_commit '{current_commit}'")
    if not (yaml_scalar(fm, "engine") or "").strip():
        return f"{aud_id} sem engine no frontmatter"
    independence = (yaml_scalar(fm, "independence") or "").strip()
    if not independence or "cross" not in independence.lower():
        return (f"{aud_id} sem independence cross-LLM valida "
                f"('{independence or '(ausente)'}')")
    patch = (yaml_scalar(fm, "patch_sha256") or "").strip()
    if not re.fullmatch(r"[0-9a-f]{64}", patch, re.I):
        return f"{aud_id} sem patch_sha256 de 64 hex — fotografia da janela ausente"
    declared_findings = yaml_scalar(fm, "findings")
    body_count = len(re.findall(r"^###\s+R-\d+\b", body, re.M))
    if declared_findings is not None:
        try:
            n = int(str(declared_findings).strip())
        except ValueError:
            return f"{aud_id} findings '{declared_findings}' nao e inteiro"
        if n != body_count:
            return (f"{aud_id} findings={n} no frontmatter mas {body_count} "
                    f"heading(s) R-NN no corpo")
    return None


AUDIT_STATUSES = {
    "vigente", "parcialmente-endereçada", "endereçada", "histórica",
}
AUDIT_STATUS_SUPERSEDED = re.compile(r"^superada-por AUD-\d+$")
AUDIT_INDEX_ROW = re.compile(
    r"^\|\s*(AUD-\d+)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*"
    r"\[([^\]]+)\]\(([^)]+)\)\s*\|",
    re.M,
)
AUDIT_ITEM_HEADING = re.compile(
    r"^###\s+((?:[AVR]-\d+)|(?:[PC]\d+))\b[^\n]*$", re.M,
)
AUDIT_ITEM_SEVERITY = re.compile(
    r"(?:\*\*(?:Severidade|Gravidade):\*\*|-\s*(?:Severidade|Gravidade):)\s*\S+",
)
AUDIT_ITEM_TYPE = re.compile(
    r"(?:\*\*Tipo:\*\*|-\s*Tipo:)\s*\S+",
)


def _audit_status_ok(status: str | None) -> bool:
    if not status:
        return False
    return status in AUDIT_STATUSES or bool(AUDIT_STATUS_SUPERSEDED.match(status))


def _parse_audit_index(text: str) -> list[dict[str, str]]:
    rows = []
    for match in AUDIT_INDEX_ROW.finditer(text):
        rows.append({
            "id": match.group(1).strip(),
            "status": match.group(5).strip(),
            "label": match.group(6).strip(),
            "href": match.group(7).strip(),
            "line": text[:match.start()].count("\n") + 1,
        })
    return rows


def _validate_audits(root: Path, r: Report) -> None:
    """Registro AUD-NNN: indice, orfaos, status e campos de item (T-212)."""
    ps = root / "project_state"
    index_path = ps / "AUDITS.md"
    r.checked += 1
    if not index_path.is_file():
        r.error("state::audit-index-missing", "project_state/AUDITS.md",
                "Indice de auditorias ausente.",
                "Crie project_state/AUDITS.md (familia AUD-NNN, D-064).")
        return

    index_text = read(index_path)
    rows = _parse_audit_index(index_text)
    seen: dict[str, int] = {}
    indexed_paths: dict[str, Path] = {}

    for row in rows:
        aud_id = row["id"]
        r.checked += 1
        if aud_id in seen:
            r.error("state::audit-id-reuse", "project_state/AUDITS.md",
                    f"{aud_id} aparece mais de uma vez no indice.",
                    "IDs de auditoria nunca sao reutilizados.", row["line"])
        else:
            seen[aud_id] = row["line"]

        if not _audit_status_ok(row["status"]):
            r.error("state::audit-index-status", "project_state/AUDITS.md",
                    f"{aud_id} tem status de indice invalido '{row['status']}'.",
                    "Use vigente | parcialmente-endereçada | endereçada | "
                    "superada-por AUD-NNN | histórica.", row["line"])

        target = (index_path.parent / row["href"]).resolve()
        try:
            target.relative_to(root.resolve())
        except ValueError:
            r.error("state::audit-orphan", "project_state/AUDITS.md",
                    f"{aud_id} aponta para fora do repositorio: {row['href']}.",
                    "Caminho do indice deve resolver sob a raiz.", row["line"])
            continue
        if not target.is_file():
            r.error("state::audit-orphan", "project_state/AUDITS.md",
                    f"{aud_id} cita documento inexistente '{row['href']}'.",
                    "Crie o documento ou corrija o caminho no indice.", row["line"])
            continue
        indexed_paths[aud_id] = target

        doc = read(target)
        fm, body = split_frontmatter(doc)
        doc_rel = rel(target, root)
        doc_id = yaml_scalar(fm, "id") if fm else None
        doc_status = yaml_scalar(fm, "status") if fm else None
        r.checked += 1
        if doc_id != aud_id:
            r.error("state::audit-index-status", doc_rel,
                    f"Frontmatter id='{doc_id}' diverge do indice '{aud_id}'.",
                    "O ID no documento e o da linha do indice devem coincidir.")
        if doc_status != row["status"]:
            r.error("state::audit-index-status", doc_rel,
                    f"{aud_id} tem status '{doc_status}' no documento e "
                    f"'{row['status']}' no indice.",
                    "Alinhe frontmatter e project_state/AUDITS.md (state-currency §2.7).")
        elif not _audit_status_ok(doc_status):
            r.error("state::audit-index-status", doc_rel,
                    f"{aud_id} tem status de frontmatter invalido '{doc_status}'.",
                    "Use o vocabulario de state-currency.md §2.7.")

        # Itens listados: headings ### ID — exigem severidade e tipo (findings-triage).
        for item in AUDIT_ITEM_HEADING.finditer(body):
            item_id = item.group(1)
            start = item.end()
            nxt = AUDIT_ITEM_HEADING.search(body, start)
            chunk = body[start:nxt.start()] if nxt else body[start:start + 1200]
            # Limita ao bloco curto do item (evita pegar campos do proximo por acaso).
            chunk = chunk.split("\n### ", 1)[0][:1200]
            r.checked += 1
            line = body[:item.start()].count("\n") + 1
            if fm:
                # frontmatter lines shift body line numbers in the full file
                line += fm.count("\n") + 3
            missing = []
            if not AUDIT_ITEM_SEVERITY.search(chunk):
                missing.append("severidade")
            if not AUDIT_ITEM_TYPE.search(chunk):
                missing.append("tipo")
            if missing:
                r.error("state::audit-item-fields", doc_rel,
                        f"{item_id} sem {', '.join(missing)}.",
                        "Todo item de auditoria declara ID local, severidade e tipo "
                        "(findings-triage.md).", line)

    # Documentos em audits/ com frontmatter AUD-NNN devem estar no indice.
    audits_root = root / "audits"
    if audits_root.is_dir():
        for path in sorted(audits_root.rglob("*.md")):
            if any(part.startswith(".") for part in path.parts):
                continue
            text = read(path)
            fm, _ = split_frontmatter(text)
            if not fm:
                continue
            aud_id = yaml_scalar(fm, "id")
            if not aud_id or not re.fullmatch(r"AUD-\d+", aud_id):
                continue
            r.checked += 1
            if aud_id not in indexed_paths:
                r.error("state::audit-orphan", rel(path, root),
                        f"Documento '{aud_id}' sem linha em project_state/AUDITS.md.",
                        "Inclua a auditoria no indice na mesma passagem em que o "
                        "frontmatter recebe o ID.")
            elif indexed_paths[aud_id].resolve() != path.resolve():
                r.error("state::audit-orphan", rel(path, root),
                        f"{aud_id} existe em '{rel(path, root)}', mas o indice aponta "
                        f"para '{rel(indexed_paths[aud_id], root)}'.",
                        "Um ID, um documento. Corrija o caminho ou o frontmatter.")


def run(root: Path) -> Report:
    # O modulo pode validar mais de uma raiz no mesmo processo. Consultas repetidas
    # dentro desta passagem sao imutaveis; entre passagens, o repositorio pode mudar.
    _git_cached.cache_clear()
    r = Report("estado")
    ps = root / "project_state"

    if not ps.is_dir():
        r.error("state::missing", "project_state",
                "Diretorio de estado ausente.",
                "Crie project_state/ com PROJECT.md e WORKSTREAMS.md.")
        return r

    # --- arquivos globais obrigatorios
    for f, why in [("PROJECT.md", "objetivo, comandos e regras criticas"),
                   ("WORKSTREAMS.md", "indice das linhas de trabalho")]:
        r.checked += 1
        if not (ps / f).is_file():
            r.error("state::global-missing", f"project_state/{f}",
                    f"Arquivo global obrigatorio ausente ({why}).",
                    f"Crie project_state/{f}.")

    # --- sem sistemas paralelos de estado (D-003)
    for legacy in ["CONTEXT.md", "TASKS.md", "PROGRESS.md"]:
        r.checked += 1
        if (ps / legacy).is_file():
            r.error("state::parallel-system", f"project_state/{legacy}",
                    f"'{legacy}' global reintroduzido — sistema paralelo de estado.",
                    "Migre: duravel -> PROJECT.md; volatil -> workstreams/<WS>/STATE.md; "
                    "historico -> EVENTS.jsonl. Ver D-003 e o guia de migracao.")

    # --- PROJECT.md declara comandos
    proj = ps / "PROJECT.md"
    if proj.is_file():
        r.checked += 1
        t = read(proj)
        if "## Comandos" not in t:
            r.error("state::project-commands", "project_state/PROJECT.md",
                    "PROJECT.md sem secao '## Comandos'.",
                    "Declare os comandos de build, teste e validacao — capacidade 7 do AI Ready.")
        elif not re.search(r"```(bash|console|sh)", t):
            r.error("state::project-commands-empty", "project_state/PROJECT.md",
                    "Secao Comandos sem comando executavel.",
                    "Inclua os comandos reais num bloco de codigo.")

    # --- workstreams
    ws_dir = ps / "workstreams"
    index = read(ps / "WORKSTREAMS.md") if (ps / "WORKSTREAMS.md").is_file() else ""
    plans = ps / "plans"
    ws_ids: set[str] = set()
    task_locations: dict[str, str] = {}
    index_sections = {
        "active": "Ativas",
        "proposed": "Propostas",
        "paused": "Pausadas",
        "blocked": "Bloqueadas",
        "completed": "Concluídas",
        "cancelled": "Canceladas",
    }
    indexed: dict[str, str] = {}
    for indexed_status, heading in index_sections.items():
        section = re.search(rf"^## {heading}\s*\n(.*?)(?=^## |\Z)", index, re.M | re.S)
        if not section:
            continue
        for indexed_id in re.findall(r"\|\s*\[?(WS-\d+)", section.group(1)):
            if indexed_id in indexed:
                r.error("state::ws-index-duplicate", "project_state/WORKSTREAMS.md",
                        f"{indexed_id} aparece em mais de uma secao do indice.",
                        "Mantenha cada workstream somente na secao do seu status vigente.")
            indexed[indexed_id] = indexed_status

    dirs = sorted([d for d in ws_dir.iterdir() if d.is_dir()]) if ws_dir.is_dir() else []
    for d in dirs:
        r.checked += 1
        state = d / "STATE.md"
        p = rel(state, root)
        if not state.is_file():
            r.error("state::ws-no-state", rel(d, root),
                    "Workstream sem STATE.md.",
                    "Crie STATE.md a partir de .agents/templates/WORKSTREAM-STATE.md.")
            continue

        text = read(state)
        fm, body = split_frontmatter(text)
        if not fm:
            r.error("state::ws-frontmatter", p, "STATE.md sem frontmatter.",
                    "Use .agents/templates/WORKSTREAM-STATE.md.")
            continue

        ws_id = yaml_scalar(fm, "id")
        status = yaml_scalar(fm, "status")
        objective = yaml_scalar(fm, "objective")
        active_plan = yaml_scalar(fm, "active_plan")
        active_tasks = yaml_list(fm, "active_tasks")
        branch = yaml_scalar(fm, "branch")
        worktree = yaml_scalar(fm, "worktree")
        current_commit = yaml_scalar(fm, "current_commit")
        validated_commit = yaml_scalar(fm, "validated_commit") or current_commit
        risk_raw = yaml_scalar(fm, "risk_level")
        try:
            risk_level = int(risk_raw) if risk_raw is not None else -1
        except ValueError:
            risk_level = -1

        if not ws_id:
            r.error("state::ws-id", p, "Campo 'id' ausente.", "Declare id: WS-NNN.")
        else:
            if ws_id in ws_ids:
                r.error("state::ws-id-reuse", p, f"ID '{ws_id}' reutilizado.",
                        "IDs nunca sao reutilizados, nem os de workstreams canceladas.")
            ws_ids.add(ws_id)
            if not d.name.startswith(ws_id):
                r.error("state::ws-dir-name", rel(d, root),
                        f"Diretorio '{d.name}' nao comeca com '{ws_id}'.",
                        f"Renomeie para {ws_id}-<slug>.")
            if ws_id not in indexed:
                r.error("state::ws-orphan", p,
                        f"Workstream '{ws_id}' sem linha em WORKSTREAMS.md.",
                        "Reconcilie o indice antes de qualquer outro trabalho.")
            elif indexed.get(ws_id) != status:
                r.error("state::ws-index-status", p,
                        f"{ws_id} tem status '{status}', mas esta na secao "
                        f"'{indexed.get(ws_id) or 'desconhecida'}' do indice.",
                        f"Mova a linha para '## {index_sections.get(status, status)}'.")

        if status not in WS_STATUS:
            r.error("state::ws-status", p, f"status '{status}' invalido.",
                    f"Use um de {sorted(WS_STATUS)}.")
        if risk_level not in range(6):
            r.error("state::ws-risk", p, f"risk_level '{risk_raw}' invalido.",
                    "Use um inteiro de 0 a 5 conforme risk-levels.md.")
        if (current_commit and current_commit != "none"
                and _git(root, "rev-parse", "--git-dir") is not None
                and _git(root, "rev-parse", "--verify", f"{current_commit}^{{commit}}") is None):
            r.error("state::ws-current-commit", p,
                    f"current_commit '{current_commit}' nao existe neste repositorio.",
                    "Use o commit real que referencia o estado vigente.")
        head = _git(root, "rev-parse", "HEAD")
        current_branch = _git(root, "branch", "--show-current")
        if (status == "active" and worktree == "." and branch == current_branch
                and current_commit not in (None, "none", head)):
            r.warn(
                "state::ws-snapshot-stale", p,
                f"{ws_id} referencia '{current_commit}', mas a worktree atual esta em '{head}'.",
                "Pause a workstream ou revalide e atualize seu snapshot antes de retomar.",
            )

        if status in ("active", "paused", "blocked") and not objective:
            r.error("state::ws-objective", p,
                    "Workstream ativa sem objetivo verificavel.",
                    "Escreva o que estara verdadeiro quando terminar. "
                    "Objetivo vago produz fechamento vago.")

        if status == "active" and not active_tasks:
            r.error("state::ws-active-no-task", p,
                    "Workstream active sem tarefa atual.",
                    "Declare ao menos uma tarefa em active_tasks e marque-a em andamento.")

        if status == "active" and risk_level >= 2:
            if not active_plan:
                r.error("state::ws-active-no-plan", p,
                        "Workstream active de risco >= 2 sem plano ativo.",
                        "Vincule active_plan a PLAN-NNN aprovado e em execução.")
            else:
                plan_path = _plan_path(plans, active_plan)
                if not plan_path:
                    r.error("state::ws-plan-missing", p,
                            f"active_plan '{active_plan}' nao resolve para um plano unico.",
                            "Crie project_state/plans/PLAN-NNN-<slug>.md ou corrija o ID.")
                elif not re.search(r"^\*\*Status:\*\*\s*em execução\s*$",
                                   read(plan_path), re.M):
                    r.error("state::ws-plan-status", rel(plan_path, root),
                            f"Plano ativo {active_plan} nao esta 'em execução'.",
                            "Alinhe o status do plano ao estado active da workstream.")

        pending = yaml_list(fm, "pending_gates")
        gate_section = re.search(r"^## Gates pendentes\s*\n(.*?)(?=^## |\Z)",
                                 body, re.M | re.S)
        body_pending = (re.findall(r"^- (G\d+)\b", gate_section.group(1), re.M)
                        if gate_section else [])
        if set(body_pending) != set(pending):
            r.error("state::pending-gates-diverge", p,
                    f"Frontmatter declara {pending}, mas a secao declara {body_pending}.",
                    "Mantenha a lista e a secao de gates pendentes sincronizadas.")
        if status == "completed" and pending:
            r.error("state::ws-close-with-gates", p,
                    f"Workstream completed com gates pendentes: {pending}.",
                    "Nao feche com gate pendente: o estado correto e paused ou blocked.")

        if status == "blocked":
            if not (yaml_list(fm, "open_questions") or pending):
                r.error("state::ws-blocked-no-cause", p,
                        "Workstream blocked sem causa nomeada.",
                        "Declare a causa em open_questions ou pending_gates. "
                        "Bloqueio sem causa e abandono.")

        if status == "paused" and yaml_scalar(fm, "last_handoff") in (None, "null"):
            if not (d / "HANDOFF.md").is_file():
                r.error("state::ws-paused-no-handoff", p,
                        "Workstream paused sem handoff.",
                        "Pausa sem handoff e perda de contexto disfarcada de organizacao.")

        # tarefas: estado, origem e evidencia sao relacoes, nao substrings
        evidence_path = d / "EVIDENCE.md"
        evidence_text = read(evidence_path) if evidence_path.is_file() else ""
        evidence = _evidence_blocks(evidence_text)

        required_artifacts = []
        if status != "proposed" and risk_level >= 1:
            required_artifacts.append("G5")
        if status != "proposed" and risk_level >= 2:
            required_artifacts.append("G13")
        if status != "proposed" and risk_level >= 3:
            required_artifacts.append("G14")
        closed = status in ("completed", "cancelled")
        legacy_pending = any(g in pending for g in ("G11", "G12"))
        for gate in required_artifacts:
            if gate in pending:
                continue
            r.checked += 1
            # Janela 3.0→4.0: WS aberta ainda lista G11/G12 (conversao = T-202).
            if not closed and legacy_pending and gate in ("G13", "G14"):
                r.warn("state::gate-conversion-pending", p,
                       f"{gate} exigido sob a 4.0, mas pending_gates ainda lista "
                       f"G11/G12 — converta para G13/G14 (T-202 / D-064).",
                       "Troque pending_gates e a secao Gates pendentes; artefatos "
                       "selados de G11/G12 permanecem como historico.")
                continue
            # WS fechada sob a 3.0: G11/G12 historico cobre a verificacao independente.
            if closed and gate in ("G13", "G14"):
                hist = (_latest_gate_artifact(d, "G11")
                        or _latest_gate_artifact(d, "G12"))
                if hist:
                    round_no, path = hist
                    r.warn("state::gate-historical", p,
                           f"{gate}: workstream fechada sob a 3.0; rodada "
                           f"{round_no} ({path.name}) aceita como registro "
                           f"historico no lugar de {gate}.",
                           "Retomada exige G13/G14 sob a 4.0, nao reabrir G11/G12.")
                    continue
            state = _gate_status(d, gate, evidence_text,
                                 current_commit=yaml_scalar(fm, "current_commit"),
                                 closed=closed, root=root)
            if state.ok and state.severity == "warn":
                r.warn("state::gate-historical", p,
                       f"{gate}: {state.reason}.",
                       "Registro preservado; retomada sob a 4.0 usa G13/RC/G14.")
            elif not state.ok:
                check = ("state::g14-agent-signed"
                         if "assinado por agente" in state.reason
                         else "state::gate-artifact-missing")
                r.error(check, p,
                        f"{gate} foi retirado de pending_gates, mas {state.reason}.",
                        f"Rode {gate} contra o tip ou devolva o gate a "
                        f"pending_gates.")
            elif gate == "G14" and not closed and risk_level >= 3:
                rc_ok, rc_reason, aud_id = _rc_requirement(evidence_text)
                r.checked += 1
                if not rc_ok:
                    r.error("state::rc-missing", p, rc_reason,
                            "Antes do G14, rode a RC (AUD-NNN) ou registre "
                            "escape INFRA com D-NNN e prazo.")
                elif aud_id:
                    identity = _rc_identity(
                        root, aud_id, ws_id=ws_id,
                        current_commit=yaml_scalar(fm, "current_commit"),
                    )
                    r.checked += 1
                    if identity:
                        r.error("state::rc-identity", p, identity,
                                "Cite a AUD-NNN da RC desta workstream no tip "
                                "(tipo, ws, commit, engine, independence, patch).")
                    critical = _rc_critical_open(root, aud_id)
                    r.checked += 1
                    if critical:
                        r.error("state::rc-critical-open", p, critical,
                                "Corrija o achado e rode G13; G14 nao aceita "
                                "critico por decisao (D-058).")
        tasks: dict[str, tuple[bool, str, int, str | None]] = {}
        for m in TASK_RE.finditer(body):
            done, tid, rest = m.group(1) == "x", m.group(2), m.group(3)
            line = text[:m.start()].count("\n") + 1
            r.checked += 1
            task_state_match = re.search(
                r"`(aberta|em andamento|bloqueada|parcial|concluída|cancelada)`", rest)
            task_state = task_state_match.group(1) if task_state_match else None
            if tid in tasks:
                r.error("state::task-id-reuse", p, f"{tid} aparece mais de uma vez.",
                        "IDs de tarefa nunca sao reutilizados.", line)
            tasks[tid] = (done, rest, line, task_state)
            if tid in task_locations and task_locations[tid] != p:
                r.error("state::task-id-reuse", p,
                        f"{tid} ja foi alocada em {task_locations[tid]}.",
                        "IDs de tarefa sao globais e nunca sao reutilizados.", line)
            else:
                task_locations[tid] = p

            origin = re.search(r"\((PLAN-\d{3})\)", rest)
            if not origin and not re.search(r"\bad-hoc\b", rest):
                r.error("state::task-no-origin", p,
                        f"{tid} sem origem declarada.",
                        "Toda tarefa referencia PLAN-NNN, ou e marcada 'ad-hoc' (so nos niveis 0 e 1).",
                        line)
            elif origin and not _plan_path(plans, origin.group(1)):
                r.error("state::task-plan-missing", p,
                        f"{tid} referencia plano inexistente '{origin.group(1)}'.",
                        "Crie o plano ou corrija a origem da tarefa.", line)

            if task_state not in TASK_STATES:
                r.error("state::task-state", p, f"{tid} sem estado reconhecido.",
                        f"Use um de {sorted(TASK_STATES)} entre crases.", line)
            if done != (task_state == "concluída"):
                r.error("state::task-checkbox", p,
                        f"{tid} tem checkbox e estado textual divergentes.",
                        "Use [x] somente com `concluída`; os demais estados usam [ ].", line)

            refs = re.findall(r"\bE-\d{3}\b", rest)
            if done and not refs:
                r.error("state::task-no-evidence", p,
                        f"{tid} marcada concluida sem apontar evidencia.",
                        "Aponte EVIDENCE.md#E-NNN. Conclusao sem evidencia nao e conclusao.",
                        line)
            for evidence_id in refs if done else []:
                block = evidence.get(evidence_id)
                if not block:
                    r.error("state::task-evidence-missing", p,
                            f"{tid} referencia {evidence_id}, que nao existe em EVIDENCE.md.",
                            "Crie a evidencia real ou mantenha a tarefa parcial.", line)
                    continue
                missing = _evidence_contract(block)
                if missing:
                    r.error("state::task-evidence-incomplete", rel(evidence_path, root),
                            f"{evidence_id}, usada por {tid}, nao prova: {', '.join(missing)}.",
                            "Registre comando, saida, timestamp ISO 8601 e commit Git exato.")
                    continue
                evidence_commit = _evidence_commit(block)
                if evidence_commit and _git(root, "rev-parse", "--git-dir") is not None:
                    resolved = _git(root, "rev-parse", "--verify",
                                    f"{evidence_commit}^{{commit}}")
                    if not resolved:
                        r.error("state::task-evidence-commit", rel(evidence_path, root),
                                f"{evidence_id} cita commit inexistente '{evidence_commit}'.",
                                "Use um commit real deste repositorio.")
                    elif validated_commit:
                        validated_resolved = _git(root, "rev-parse", "--verify",
                                                  f"{validated_commit}^{{commit}}")
                        if (validated_resolved and _git(
                                root, "merge-base", "--is-ancestor", resolved,
                                validated_resolved) is None):
                            r.error("state::task-evidence-stale", rel(evidence_path, root),
                                    f"{evidence_id} prova {resolved[:12]}, que nao e ancestral de "
                                    f"validated_commit {validated_resolved[:12]}.",
                                    "Reexecute na linhagem validada ou mantenha a tarefa parcial.")

        for active_task in active_tasks:
            row = tasks.get(active_task)
            if not row:
                r.error("state::active-task-missing", p,
                        f"active_tasks cita '{active_task}', ausente de ## Tarefas.",
                        "Crie a tarefa ou corrija active_tasks.")
            elif row[3] != "em andamento":
                r.error("state::active-task-state", p,
                        f"{active_task} esta em active_tasks, mas seu estado e '{row[3]}'.",
                        "Marque a tarefa atual como `em andamento`.", row[2])

        if status == "completed":
            unfinished = [tid for tid, (_, _, _, task_state) in tasks.items()
                          if task_state not in ("concluída", "cancelada")]
            if unfinished:
                r.error("state::ws-completed-with-tasks", p,
                        f"Workstream completed com tarefas abertas: {unfinished}.",
                        "Conclua ou cancele cada tarefa antes de fechar a workstream.")

        # skills obrigatorias puladas exigem registro
        if "skipped_skills" in body:
            for blk in re.finditer(r"- name: (\S+)\s*\n\s+reason: (.*)", body):
                if not blk.group(2).strip().strip('"'):
                    r.error("state::skip-no-reason", p,
                            f"Skill '{blk.group(1)}' pulada sem motivo.",
                            "Gatilho obrigatorio pulado exige justificativa escrita.")

        # evidencia e ledger
        r.checked += 1
        if not (d / "EVENTS.jsonl").is_file():
            r.error("state::ws-no-ledger", rel(d, root), "Workstream sem EVENTS.jsonl.",
                    "Crie o ledger append-only; ele e a memoria pesquisavel.")
        if not (d / "EVIDENCE.md").is_file():
            r.error("state::ws-no-evidence", rel(d, root), "Workstream sem EVIDENCE.md.",
                    "Crie a partir de .agents/templates/EVIDENCE.md.")

        # handoff: exige commit e precisa casar com o estado vigente
        ho = d / "HANDOFF.md"
        if ho.is_file():
            r.checked += 1
            hfm, _ = split_frontmatter(read(ho))
            handoff_branch = yaml_scalar(hfm, "branch")
            handoff_worktree = yaml_scalar(hfm, "worktree")
            commit = yaml_scalar(hfm, "commit")
            if not handoff_branch or not handoff_worktree or not commit:
                r.error("state::handoff-coordinates", rel(ho, root),
                        "Handoff sem branch, worktree ou commit.",
                        "Amarre a branch, worktree e commit; sem eles o handoff nao e verificavel.")
            elif commit != "none":
                if branch and handoff_branch != branch:
                    r.warn("state::handoff-branch-stale", rel(ho, root),
                           f"Handoff usa branch '{handoff_branch}', estado usa '{branch}'.",
                           "Revalide o handoff na branch vigente.")
                if worktree and handoff_worktree != worktree:
                    r.warn("state::handoff-worktree-stale", rel(ho, root),
                           f"Handoff usa worktree '{handoff_worktree}', estado usa '{worktree}'.",
                           "Revalide o handoff na worktree vigente.")
                if current_commit and commit != current_commit:
                    r.warn("state::handoff-stale", rel(ho, root),
                           f"Handoff referencia '{commit}', mas o estado vigente referencia "
                           f"'{current_commit}'.",
                           "Handoff historico: revalide o conteudo e gere outro para o commit "
                           "de referencia do STATE.md.")
                if _git(root, "rev-parse", "--git-dir") is None:
                    r.warn("state::handoff-unverifiable", rel(ho, root),
                           f"Commit '{commit}' declarado, mas o repositorio nao tem Git: "
                           "a obsolescencia do handoff nao e verificavel aqui.",
                           "Trate o handoff como nao verificado — nem valido, nem obsoleto — "
                           "e revalide o conteudo contra o codigo antes de agir.")
                elif _git(root, "rev-parse", "--verify", f"{commit}^{{commit}}") is None:
                    r.warn("state::handoff-stale", rel(ho, root),
                           f"Commit '{commit}' do handoff nao existe neste repositorio.",
                           "Handoff obsoleto: trate o conteudo como historical e revalide.")

    # --- ledger
    for ledger in sorted(ws_dir.rglob("EVENTS.jsonl")) if ws_dir.is_dir() else []:
        p = rel(ledger, root)
        text, _enc = read_ledger(ledger)
        for n, raw in enumerate(text.splitlines(), 1):
            if not raw.strip():
                continue
            r.checked += 1
            try:
                ev = json.loads(raw)
            except json.JSONDecodeError as e:
                r.error("state::ledger-json", p, f"Linha {n} nao e JSON valido: {e.msg}.",
                        "Uma linha JSON por evento. Pule a linha corrompida e registre F-NNN.", n)
                continue
            if not isinstance(ev, dict):
                r.error("state::ledger-object", p, f"Linha {n}: evento deve ser objeto JSON.",
                        "Use um objeto com os campos obrigatorios do ledger.", n)
                continue
            for k in EVENT_REQUIRED:
                if k not in ev:
                    r.error("state::ledger-field", p, f"Linha {n}: campo '{k}' ausente.",
                             f"Campos obrigatorios: {', '.join(EVENT_REQUIRED)}.", n)
                elif not isinstance(ev[k], str) or not ev[k].strip():
                    r.error("state::ledger-field", p, f"Linha {n}: campo '{k}' vazio ou invalido.",
                            "Campos obrigatorios devem ser strings nao vazias.", n)
            if ev.get("type") not in EVENT_TYPES:
                r.error("state::ledger-type", p,
                        f"Linha {n}: tipo '{ev.get('type')}' fora da allowlist.",
                        "Tipo fora da allowlist e descartado com anotacao de perda.", n)
            if ev.get("authority") not in AUTHORITIES:
                r.error("state::ledger-authority", p,
                        f"Linha {n}: autoridade '{ev.get('authority')}' invalida.",
                        f"Use uma de {sorted(AUTHORITIES)}. Memoria sem autoridade nao e avaliavel.", n)
            timestamp = ev.get("ts", "")
            try:
                if not isinstance(timestamp, str) or not re.fullmatch(
                    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", timestamp
                ):
                    raise ValueError
                datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                r.error("state::ledger-timestamp", p, f"Linha {n}: timestamp invalido.",
                        "Use ISO-8601 UTC, por exemplo 2026-07-30T12:00:00Z.", n)
            directory_ws = ledger.parent.name.split("-", 2)[:2]
            directory_ws_id = "-".join(directory_ws)
            if ev.get("ws") and ev["ws"] != directory_ws_id:
                r.error("state::ledger-workstream", p,
                        f"Linha {n}: evento {ev.get('ws')} esta no diretorio {ledger.parent.name}.",
                        "Grave o evento no ledger da workstream declarada.", n)
            commit = ev.get("commit")
            if (commit and commit != "none" and _git(root, "rev-parse", "--git-dir") is not None
                    and _git(root, "rev-parse", "--verify", f"{commit}^{{commit}}") is None):
                r.error("state::ledger-commit", p, f"Linha {n}: commit '{commit}' nao existe.",
                        "Use o commit real ou 'none' em repositorio sem Git.", n)

    # --- planos
    plans = ps / "plans"
    if plans.is_dir():
        for pl in sorted(plans.glob("PLAN-*.md")):
            r.checked += 1
            t = read(pl)
            p = rel(pl, root)
            if "## Critérios de validação" not in t and "## Criterios de validacao" not in t:
                r.error("state::plan-no-criteria", p, "Plano sem criterios de validacao.",
                        "Plano sem criterio de validacao e intencao, nao plano.")
            elif not re.search(r"comando:\s*`", t):
                r.error("state::plan-criteria-no-command", p,
                        "Criterios de validacao sem comando associado.",
                        "Cada criterio declara o comando que o prova.")
            if not re.search(r"^\*\*Status:\*\*", t, re.M):
                r.error("state::plan-no-status", p, "Plano sem status.",
                        "Declare: proposto | aprovado | em execucao | concluido | cancelado.")

    # --- auditorias (AUD-NNN)
    _validate_audits(root, r)

    # --- decisoes
    dec = ps / "DECISIONS.md"
    if dec.is_file():
        t = read(dec)
        ids = re.findall(r"^## (D-\d+)", t, re.M)
        for i, did in enumerate(ids):
            r.checked += 1
            block = t.split(f"## {did}", 1)[1]
            block = block.split("\n## ", 1)[0]
            if "**Status:**" not in block:
                r.error("state::decision-no-status", "project_state/DECISIONS.md",
                        f"{did} sem status.", "Declare: ativa | substituida por D-NNN | revogada.")
            if "**Autoridade:**" not in block and "Autoridade:" not in block:
                r.error("state::decision-no-authority", "project_state/DECISIONS.md",
                        f"{did} sem autoridade.",
                        "Decisao sem autoridade declarada nao vincula.")
        if len(ids) != len(set(ids)):
            r.error("state::decision-id-reuse", "project_state/DECISIONS.md",
                    "IDs de decisao repetidos.", "IDs nunca sao reutilizados.")

    # --- findings
    fnd = ps / "FINDINGS.md"
    if fnd.is_file():
        t = read(fnd)
        ids = re.findall(r"^## (F-\d+)", t, re.M)
        if len(ids) != len(set(ids)):
            r.error("state::finding-id-reuse", "project_state/FINDINGS.md",
                    "IDs de finding repetidos.", "IDs nunca sao reutilizados.")
        for fid in ids:
            r.checked += 1
            block = t.split(f"## {fid}", 1)[1].split("\n## ", 1)[0]
            if "Autoridade:" not in block:
                r.error("state::finding-no-authority", "project_state/FINDINGS.md",
                        f"{fid} sem autoridade.",
                        "Declare evidence ou hypothesis. Sem comando e saida, e hypothesis.")

    return r
