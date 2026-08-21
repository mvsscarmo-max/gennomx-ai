"""Valida as skills locais: metadados, estrutura, orfaos, registro e copias divergentes."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from _common import (Report, read, rel, sandbox_violation, split_frontmatter,
                     yaml_list, yaml_scalar)

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FIRST_PERSON = {"eu", "meu", "minha", "nos", "nosso", "nossa", "voce", "seu", "sua",
                "i", "me", "my", "we", "our", "you", "your"}
REQUIRED_META = ["protocol", "layer", "version", "risk", "vlaeg_phases",
                 "triggers", "negative_triggers", "produces", "gates"]
LAYERS = {"priority", "memory", "protocol", "coordination", "project"}
RISKS = {"low", "medium", "high", "critical"}
PHASES = {"V", "L", "A", "E", "G", "cross-cutting", "not-applicable"}
STD_DIRS = {"scripts", "references", "assets"}
HUMAN_DOCS = {"readme.md", "changelog.md", "install.md", "contributing.md"}
# Cinco prioritarias + cycle-review (protocolo) apos D-064 / T-201.
PRIORITY_CORE = {"writing-agents-md", "writing-skills", "no-workarounds",
                 "deslop", "qa-execution"}
PROTOCOL_REQUIRED = {"cycle-review"}
MAX_LINES = 500


def _meta_block(fm: str) -> str:
    m = re.search(r"^metadata:[ \t]*$", fm, re.M)
    if not m:
        return ""
    out = []
    for line in fm[m.end():].splitlines():
        if line.strip() and not line.startswith((" ", "\t")):
            break
        out.append(line)
    return "\n".join(out)


def _hash_dir(d: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(d.rglob("*")):
        if p.is_file():
            content = p.read_bytes()
            h.update(content.replace(b"\r\n", b"\n") if b"\0" not in content else content)
    return h.hexdigest()[:16]


def run(root: Path) -> Report:
    r = Report("skills")
    skills_root = root / ".agents" / "skills"

    if not skills_root.is_dir():
        r.error("skills::root-missing", ".agents/skills",
                "Diretorio canonico de skills ausente.",
                "Crie .agents/skills/{priority,memory,protocol}/ (fonte canonica unica, D-008).")
        return r

    found: dict[str, Path] = {}
    hashes: dict[str, list[str]] = {}
    skill_info: dict[str, dict[str, str]] = {}

    for skill_md in sorted(skills_root.rglob("SKILL.md")):
        d = skill_md.parent
        p = rel(skill_md, root)
        r.checked += 1
        text = read(skill_md)
        fm, body = split_frontmatter(text)

        if not fm:
            r.error("skills::frontmatter", p, "SKILL.md sem frontmatter YAML.",
                    "Acrescente o bloco --- com name, description e metadata.")
            continue

        name = yaml_scalar(fm, "name")
        desc = yaml_scalar(fm, "description")
        meta = _meta_block(fm)

        # --- nome
        if not name:
            r.error("skills::name-missing", p, "Campo 'name' ausente.", "Acrescente name ao frontmatter.")
        else:
            if not NAME_RE.match(name):
                r.error("skills::name-charset", p,
                        f"Nome '{name}' invalido.",
                        "Use minusculas, numeros e hifens simples; sem hifen no inicio ou fim.")
            if not 1 <= len(name) <= 64:
                r.error("skills::name-length", p, f"Nome com {len(name)} caracteres.",
                        "Use entre 1 e 64 caracteres.")
            if name != d.name:
                r.error("skills::name-matches-dir", p,
                        f"name='{name}' difere do diretorio '{d.name}'.",
                        f"Renomeie o diretorio para '{name}' ou o campo name para '{d.name}'.")
            if name in found:
                r.error("skills::duplicate-name", p,
                        f"Skill '{name}' ja existe em {rel(found[name], root)}.",
                        "Nomes de skill sao unicos no repositorio.")
            else:
                found[name] = d

        # --- descricao
        if not desc:
            r.error("skills::description-missing", p, "Campo 'description' ausente.",
                    "Acrescente uma descricao com gatilhos positivos e negativos.")
        else:
            if len(desc) > 1024:
                r.error("skills::description-length", p,
                        f"Descricao com {len(desc)} caracteres (limite 1024).",
                        "Corte identidade que ja vive no corpo; mantenha apenas gatilhos.")
            words = set(re.findall(r"\b\w+\b", desc.lower()))
            bad = FIRST_PERSON & words
            if bad:
                r.error("skills::description-person", p,
                        f"Descricao usa primeira/segunda pessoa: {sorted(bad)}.",
                        "Reescreva em terceira pessoa ('Remove...', 'Autora...').")
            norm = desc.lower().replace("ã", "a").replace("á", "a").replace("é", "e")
            if "use " not in norm:
                r.error("skills::trigger-positive", p, "Descricao sem gatilho positivo.",
                        "Acrescente 'Use ao ...' nomeando um ramo por gatilho.")
            if "nao use" not in norm and "don't use" not in norm:
                r.error("skills::trigger-negative", p, "Descricao sem gatilho negativo.",
                        "Acrescente 'Nao use para ...' — impede selecao por semelhanca de nome.")

        # --- metadata do protocolo
        if not meta:
            r.error("skills::metadata-missing", p, "Bloco 'metadata:' ausente.",
                    f"Acrescente metadata com: {', '.join(REQUIRED_META)}.")
        else:
            for key in REQUIRED_META:
                if not re.search(rf"^\s+{key}:", meta, re.M):
                    r.error("skills::metadata-field", p, f"Campo 'metadata.{key}' ausente.",
                            f"Acrescente metadata.{key} conforme o contrato do protocolo.")
            layer = yaml_scalar(meta, "layer")
            if layer and layer not in LAYERS:
                r.error("skills::layer", p, f"layer '{layer}' invalida.",
                        f"Use uma de {sorted(LAYERS)}.")
            if layer and d.parent.name != layer:
                r.error("skills::layer-matches-dir", p,
                        f"layer='{layer}' mas a skill esta em '{d.parent.name}/'.",
                        "Mova a skill para o diretorio da camada declarada.")
            risk = yaml_scalar(meta, "risk")
            if risk and risk not in RISKS:
                r.error("skills::risk", p, f"risk '{risk}' invalido.", f"Use uma de {sorted(RISKS)}.")
            ver = yaml_scalar(meta, "version")
            if ver and not re.match(r"^\d+\.\d+\.\d+$", ver):
                r.error("skills::version", p, f"version '{ver}' nao e semver.", "Use x.y.z.")
            for ph in yaml_list(meta, "vlaeg_phases"):
                if ph not in PHASES:
                    r.error("skills::vlaeg-phase", p, f"Fase VLAEG '{ph}' invalida.",
                            f"Use uma de {sorted(PHASES)}.")

        # --- politica: sandbox excluida (D-044). Verificacao semantica: o que viola
        # e a adocao, nao a mencao — declarar a exclusao exige nomea-la.
        hit = sandbox_violation(text)
        if hit:
            term, line = hit
            r.error("skills::forbidden-mechanism", p,
                    f"Termo '{term}' citado fora de contexto de exclusao.",
                    "Sandbox, ai-jail e YOLO estao excluidos por D-044. Reescreva declarando "
                    "a exclusao, ou remova a mencao.", line)

        # --- corpo
        n_lines = len(text.splitlines())
        if n_lines > MAX_LINES:
            r.error("skills::body-length", p, f"SKILL.md com {n_lines} linhas (teto {MAX_LINES}).",
                    "Extraia para references/ o maior bloco que so alguns ramos precisam.")

        # --- estrutura de diretorio
        for child in sorted(d.iterdir()):
            if child.is_dir():
                if child.name not in STD_DIRS:
                    r.error("skills::nonstandard-dir", rel(child, root),
                            f"Diretorio '{child.name}' fora do padrao.",
                            f"Use apenas {sorted(STD_DIRS)}.")
                else:
                    for sub in child.iterdir():
                        if sub.is_dir():
                            r.error("skills::nested-dir", rel(sub, root),
                                    "Subdiretorio aninhado alem de um nivel.",
                                    "Mantenha scripts/, references/ e assets/ planos.")
            elif child.name.lower() in HUMAN_DOCS:
                r.error("skills::human-doc", rel(child, root),
                        f"Documento humano '{child.name}' dentro da skill.",
                        "A skill embarca so arquivos voltados ao agente; mova para fora.")

        # --- orfaos: todo arquivo empacotado precisa de ponteiro no SKILL.md
        for sub in STD_DIRS:
            sd = d / sub
            if not sd.is_dir():
                continue
            for f in sorted(sd.iterdir()):
                if not f.is_file():
                    continue
                if f.name not in body and f"{sub}/{f.name}" not in body:
                    r.error("skills::orphan-file", rel(f, root),
                            f"Arquivo empacotado sem ponteiro em SKILL.md.",
                            f"Cite '{sub}/{f.name}' no SKILL.md com a condicao de carregamento, "
                            "ou remova o arquivo.")

        content_hash = _hash_dir(d)
        hashes.setdefault(content_hash, []).append(p)
        if name:
            skill_info[name] = {
                "path": rel(d, root),
                "version": yaml_scalar(meta, "version") or "",
                "files": str(sum(1 for child in d.rglob("*") if child.is_file())),
                "content_hash": content_hash,
            }

    # --- prioritarias + cycle-review (D-064)
    for name in sorted(PRIORITY_CORE):
        r.checked += 1
        if name not in found:
            r.error("skills::priority-missing", f".agents/skills/priority/{name}",
                    f"Skill prioritaria '{name}' ausente.",
                    "As skills prioritarias do protocolo sao obrigatorias.")
        elif found[name].parent.name != "priority":
            r.error("skills::priority-layer", rel(found[name], root),
                    f"Skill prioritaria '{name}' fora de priority/.",
                    "Mova para .agents/skills/priority/.")
    for name in sorted(PROTOCOL_REQUIRED):
        r.checked += 1
        if name not in found:
            r.error("skills::protocol-missing", f".agents/skills/protocol/{name}",
                    f"Skill de protocolo '{name}' ausente.",
                    "cycle-review e obrigatoria sob D-064 (skills de G11/G12 aposentadas).")
        elif found[name].parent.name != "protocol":
            r.error("skills::protocol-layer", rel(found[name], root),
                    f"Skill de protocolo '{name}' fora de protocol/.",
                    "Mova para .agents/skills/protocol/.")

    # --- copias divergentes
    for h, paths in hashes.items():
        if len(paths) > 1:
            r.error("skills::duplicate-content", paths[0],
                    f"Conteudo identico em: {', '.join(paths)}.",
                    "Mantenha uma fonte canonica: remova a copia e aponte pelo registro.")

    # --- registro sincronizado
    reg = root / ".agents" / "registry" / "local-skills.yaml"
    r.checked += 1
    if not reg.is_file():
        r.error("skills::registry-missing", ".agents/registry/local-skills.yaml",
                "Registro de skills locais ausente.",
                "Gere o registro indexando .agents/skills/.")
    else:
        reg_text = read(reg)
        for name in sorted(found):
            if f"name: {name}" not in reg_text:
                r.error("skills::registry-sync", ".agents/registry/local-skills.yaml",
                        f"Skill '{name}' existe mas nao esta registrada.",
                        f"Acrescente a entrada de '{name}' ao registro.")
        for m in re.finditer(r"^\s+- name: (\S+)", reg_text, re.M):
            if m.group(1) not in found:
                r.error("skills::registry-ghost", ".agents/registry/local-skills.yaml",
                        f"Registro cita '{m.group(1)}', que nao existe em .agents/skills/.",
                        "Remova a entrada ou crie a skill.")
        entries = re.finditer(r"^\s+- name: (\S+)\s*\n(.*?)(?=^\s+- name: |\Z)",
                              reg_text, re.M | re.S)
        for entry in entries:
            name, block = entry.group(1), entry.group(2)
            actual = skill_info.get(name)
            if not actual:
                continue
            for key in ("path", "version", "files", "content_hash"):
                declared = yaml_scalar(block, key)
                if declared != actual[key]:
                    r.error("skills::registry-value", ".agents/registry/local-skills.yaml",
                            f"{name}.{key} declara '{declared}', mas o valor real e "
                            f"'{actual[key]}'.",
                            "Atualize o registro a partir da fonte canonica da skill.")

    return r
