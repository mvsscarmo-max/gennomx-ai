"""Valida a propriedade AI Ready: as dez capacidades, orcamentos, politica e segredos."""
from __future__ import annotations

import re
from pathlib import Path

from _common import (Report, core_paths, excluded_parts, iter_markdown, read, rel,
                     sandbox_violation, walk_files, yaml_list)
from capture_policy import load_redaction_allowlist, load_redaction_patterns
# A verificacao de sandbox e semantica, nao lexical: ver _common.sandbox_violation.
# Estes arquivos definem ou implementam a propria regra, entao a citam fora de
# contexto de exclusao por necessidade.
SANDBOX_ALLOWLIST = {
    ".agents/policy/capture-policy.yaml",
    "tools/validate_skills.py",
    "tools/validate_ai_ready.py",
    "tools/_common.py",
    ".agents/skills/priority/writing-skills/scripts/validate_metadata.py",
}


def _budget(root: Path, key: str, default: int) -> int:
    f = root / ".agents" / "policy" / "context-budget.yaml"
    if not f.is_file():
        return default
    m = re.search(rf"^\s*{key}:\s*(\d+)", read(f), re.M)
    return int(m.group(1)) if m else default


def _is_text(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            sample = handle.read(8192)
    except OSError:
        return False
    if b"\0" in sample:
        return False
    try:
        sample.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def run(root: Path) -> Report:
    r = Report("ai-ready")
    secret_patterns = load_redaction_patterns(root)
    secret_allowlist = load_redaction_allowlist(root)
    scope = excluded_parts(root)

    protected = core_paths(root)

    scope_policy = root / ".agents" / "policy" / "validator-scope.yaml"
    if scope_policy.is_file():
        scope_text = read(scope_policy)
        for key in ("excluded_paths", "excluded_harness", "excluded_vendor"):
            for value in yaml_list(scope_text, key):
                r.checked += 1
                if not value or value in {".", ".."} or "/" in value or "\\" in value:
                    r.error("ai-ready::scope-entry", rel(scope_policy, root),
                            f"Entrada '{value}' em {key} nao e um basename valido.",
                            "Declare fronteiras top-level por basename; vendors recursivos tambem usam basename.")
                if value in protected:
                    r.error("ai-ready::scope-core", rel(scope_policy, root),
                            f"Caminho central '{value}' foi excluido dos validadores.",
                            "Caminhos centrais nunca podem ser excluidos; corrija a causa do sinal.")

        tracked = _git_tracked(root)
        for value in yaml_list(scope_text, "excluded_harness"):
            hidden = [path for path in tracked if path.parts and path.parts[0] == value]
            r.checked += 1
            if hidden:
                r.error("ai-ready::scope-tracked-harness", rel(scope_policy, root),
                        f"Harness excluido '{value}' contem {len(hidden)} arquivo(s) versionado(s).",
                        "Remova o caminho da exclusao ou retire os artefatos locais do versionamento.")

    # --- Capacidade 1: descobrir como trabalhar
    r.checked += 1
    agents = root / "AGENTS.md"
    if not agents.is_file():
        r.error("ai-ready::core-missing", "AGENTS.md",
                "Nucleo residente ausente — capacidade 1 do AI Ready falha.",
                "Crie AGENTS.md com precedencia, ordem de descoberta, ciclo, roteamento, "
                "limites de autonomia, evidencia, registro e comandos.")
    else:
        text = read(agents)
        max_chars = _budget(root, "agents_md_max_chars", 6000)
        max_lines = _budget(root, "agents_md_max_lines", 120)
        r.checked += 2
        if len(text) > max_chars:
            r.error("ai-ready::resident-budget", "AGENTS.md",
                    f"Nucleo residente com {len(text)} caracteres (teto {max_chars}).",
                    "Rode o ramo Cortar de writing-agents-md: de veredito a cada linha e "
                    "realoque as que falham no teste do aluguel.")
        if len(text.splitlines()) > max_lines:
            r.error("ai-ready::resident-lines", "AGENTS.md",
                    f"Nucleo residente com {len(text.splitlines())} linhas (teto {max_lines}).",
                    "Mova conteudo especializado para skill ou documento sob demanda.")
        for section, why in [("Precedência", "resolver conflito de regra"),
                             ("Ordem de descoberta", "um agente novo comecar"),
                             ("Limites de autonomia", "saber o que exige aprovacao"),
                             ("Evidência", "provar conclusao"),
                             ("Comandos", "validar o trabalho")]:
            r.checked += 1
            if section not in text:
                r.error("ai-ready::core-section", "AGENTS.md",
                        f"Secao '{section}' ausente ({why}).",
                        f"Acrescente a secao '{section}' ao nucleo residente.")

    # --- Capacidade 2 e 7: objetivo, arquitetura e comandos
    r.checked += 1
    proj = root / "project_state" / "PROJECT.md"
    if not proj.is_file():
        r.error("ai-ready::project-missing", "project_state/PROJECT.md",
                "PROJECT.md ausente — capacidades 2 e 7 falham.",
                "Declare objetivo, escopo, arquitetura, regras criticas e comandos.")
    else:
        t = read(proj)
        for section in ["## Objetivo", "## Comandos", "## Regras críticas"]:
            r.checked += 1
            if section not in t:
                r.error("ai-ready::project-section", "project_state/PROJECT.md",
                        f"Secao '{section}' ausente.",
                        f"Acrescente '{section}' — e o que um agente novo le primeiro.")

    # --- Capacidade 3: workstream ativa localizavel
    r.checked += 1
    idx = root / "project_state" / "WORKSTREAMS.md"
    if not idx.is_file():
        r.error("ai-ready::workstreams-missing", "project_state/WORKSTREAMS.md",
                "Indice de workstreams ausente — capacidade 3 falha.",
                "Crie o indice com as linhas ativas, pausadas, bloqueadas e concluidas.")
    elif not re.search(r"WS-\d+", read(idx)):
        r.warn("ai-ready::no-workstream", "project_state/WORKSTREAMS.md",
               "Nenhuma workstream registrada.",
               "Um agente novo nao tem onde comecar: crie a primeira workstream.")

    # --- Capacidade 5: roteamento com gatilhos e anti-gatilhos
    r.checked += 1
    routing = root / ".agents" / "registry" / "routing-rules.yaml"
    if not routing.is_file():
        r.error("ai-ready::routing-missing", ".agents/registry/routing-rules.yaml",
                "Regras de roteamento ausentes — capacidade 5 falha.",
                "Declare gatilhos obrigatorios, anti-gatilhos e ordem de execucao.")
    else:
        t = read(routing)
        for key in ["mandatory:", "negative:", "execution_order:"]:
            r.checked += 1
            if key not in t:
                r.error("ai-ready::routing-section", ".agents/registry/routing-rules.yaml",
                        f"Bloco '{key}' ausente.",
                        "Sem anti-gatilho, a selecao volta a ser por semelhanca de nome.")

    # --- Capacidade 10: gates verificaveis
    r.checked += 1
    gates = root / "docs" / "ai-ready" / "quality-gates.md"
    if not gates.is_file():
        r.error("ai-ready::gates-missing", "docs/ai-ready/quality-gates.md",
                "Gates de qualidade ausentes — capacidade 10 falha.",
                "Declare os gates minimos e a prova exigida por cada um.")

    # --- Catalogo externo: nada instalado sem auditoria
    ext = root / ".agents" / "registry" / "external-skills.yaml"
    if ext.is_file():
        t = read(ext)
        r.checked += 1
        if "auto_update: false" not in t:
            r.error("ai-ready::auto-update", ".agents/registry/external-skills.yaml",
                    "Atualizacao automatica de skill externa nao esta desativada.",
                    "Declare auto_update: false. Mudar source_commit exige D-NNN e nova auditoria.")
        for m in re.finditer(r"^\s+- name: (\S+)", t, re.M):
            block = t[m.end():t.find("\n  - name:", m.end()) if "\n  - name:" in t[m.end():] else len(t)]
            r.checked += 1
            if "approval_status:" not in block[:600]:
                r.error("ai-ready::external-no-status", ".agents/registry/external-skills.yaml",
                        f"Skill externa '{m.group(1)}' sem approval_status.",
                        "Estado inicial e not-evaluated; usar exige intake.")

    # --- Busca entre projetos desativada por padrao
    r.checked += 1
    budget = root / ".agents" / "policy" / "context-budget.yaml"
    if not budget.is_file():
        r.error("ai-ready::budget-missing", ".agents/policy/context-budget.yaml",
                "Orcamento de contexto ausente.",
                "Declare os tetos de residente, briefing e delta, e cross_project_search.")
    else:
        t = read(budget)
        if not re.search(r"^\s*cross_project_search:\s*false", t, re.M):
            if not all(k in t for k in ["registered_decision", "written_justification",
                                        "explicit_project_list", "review_date"]):
                r.error("ai-ready::cross-project", ".agents/policy/context-budget.yaml",
                        "Busca entre projetos ativada sem os quatro requisitos.",
                        "Exige decisao registrada, justificativa, lista explicita de projetos "
                        "e data de revisao — os quatro.")

    # --- Politica de captura
    r.checked += 1
    cap = root / ".agents" / "policy" / "capture-policy.yaml"
    if not cap.is_file():
        r.error("ai-ready::capture-missing", ".agents/policy/capture-policy.yaml",
                "Politica de captura ausente.",
                "Declare ignore_paths, allowed_event_types e redaction_patterns.")
    else:
        t = read(cap)
        for key in ["ignore_paths:", "allowed_event_types:", "redaction_patterns:"]:
            r.checked += 1
            if key not in t:
                r.error("ai-ready::capture-section", ".agents/policy/capture-policy.yaml",
                        f"Bloco '{key}' ausente.", "A defesa em camadas exige os tres.")

    # --- Sandbox excluida (D-044)
    for f in [*iter_markdown(root, scope), *sorted((root / ".agents").rglob("*.yaml"))]:
        p = rel(f, root)
        if p in SANDBOX_ALLOWLIST or "legacy" in f.parts:
            continue
        r.checked += 1
        hit = sandbox_violation(read(f))
        if hit:
            term, line = hit
            r.error("ai-ready::sandbox", p,
                    f"Termo '{term}' citado fora de contexto de exclusao — leitura possivel "
                    "de adocao.",
                    "Sandbox, ai-jail e YOLO estao excluidos por D-044. Reescreva a frase "
                    "declarando a exclusao, ou remova a mencao.", line)

    # --- Segredos
    # Mesma fronteira do resto dos validadores: projeto vizinho tem o proprio gate.
    scan = walk_files(root, set(), scope)
    for f in scan:
        p = rel(f, root)
        if p in secret_allowlist or not _is_text(f):
            continue
        content = read(f)
        r.checked += 1
        for name, pattern in secret_patterns:
            hit = pattern.search(content)
            if hit:
                line = content[:hit.start()].count("\n") + 1
                r.error("ai-ready::secret", p,
                        f"Possivel segredo do tipo '{name}' detectado.",
                        "Trate o segredo como comprometido e rotacione na origem; remover o "
                        "arquivo nao desfaz a exposicao. Ver skill memory-privacy.", line)
                break

    return r


def _git_tracked(root: Path) -> list[Path]:
    import subprocess

    try:
        result = subprocess.run(["git", "-C", str(root), "ls-files", "-z"],
                                capture_output=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return []
    if result.returncode:
        return []
    return [Path(item.decode("utf-8", errors="surrogateescape"))
            for item in result.stdout.split(b"\0") if item]
