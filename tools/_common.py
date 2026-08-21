"""Utilitarios compartilhados pelos validadores do Protocolo VLAEG AI Ready First.

Sem dependencias externas: o protocolo precisa provar conformidade em qualquer
ambiente com Python 3.10+.
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Issue:
    """Um achado acionavel: o que falhou, onde, e o que fazer."""
    severity: str          # "error" | "warn"
    check: str             # identificador estavel, ex.: "skills::name-matches-dir"
    path: str
    message: str
    fix: str
    line: int | None = None

    def render(self) -> str:
        loc = f"{self.path}:{self.line}" if self.line else self.path
        tag = "ERRO " if self.severity == "error" else "AVISO"
        return f"  [{tag}] {self.check}\n         {loc}\n         {self.message}\n         -> {self.fix}"

    def as_dict(self) -> dict:
        return {"severity": self.severity, "check": self.check, "path": self.path,
                "line": self.line, "message": self.message, "fix": self.fix}


@dataclass
class Report:
    name: str
    issues: list[Issue] = field(default_factory=list)
    checked: int = 0

    def error(self, check: str, path: str, message: str, fix: str, line: int | None = None) -> None:
        self.issues.append(Issue("error", check, path, message, fix, line))

    def warn(self, check: str, path: str, message: str, fix: str, line: int | None = None) -> None:
        self.issues.append(Issue("warn", check, path, message, fix, line))

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warns(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "warn"]

    @property
    def ok(self) -> bool:
        return not self.errors


def repo_root() -> Path:
    """Raiz do repositorio: o diretorio que contem AGENTS.md, subindo a partir daqui."""
    here = Path(__file__).resolve().parent
    for candidate in [here.parent, *here.parents]:
        if (candidate / "AGENTS.md").is_file():
            return candidate
    return here.parent


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def decode_bytes(raw: bytes) -> tuple[str, str]:
    """Decodifica bytes de arquivo de texto. Devolve (texto, rótulo do encoding).

    Ordem: UTF-16 via BOM → UTF-8 com BOM → UTF-8 estrito → linha a linha
    UTF-8 com fallback CP1252 (legados Windows mistos).
    """
    if not raw:
        return "", "utf-8"
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16"), "utf-16"
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw[3:].decode("utf-8"), "utf-8-sig"
    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        pass
    parts: list[str] = []
    for line in raw.splitlines(keepends=True):
        try:
            parts.append(line.decode("utf-8"))
        except UnicodeDecodeError:
            parts.append(line.decode("cp1252"))
    return "".join(parts), "mixed-cp1252"


def read_ledger(path: Path) -> tuple[str, str]:
    """Lê EVENTS.jsonl (ou similar) com decode_bytes — sem errors=replace silencioso."""
    return decode_bytes(path.read_bytes())


def split_frontmatter(text: str) -> tuple[str, str]:
    """Devolve (frontmatter, corpo). Frontmatter vazio quando ausente."""
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 3)
    if end == -1:
        return "", text
    return text[3:end], text[end + 4:]


def strip_yaml_comment(value: str) -> str | None:
    """Remove comentario fora de aspas; devolve None para aspas desbalanceadas."""
    quote: str | None = None
    escaped = False
    for index, char in enumerate(value):
        if quote == '"' and escaped:
            escaped = False
            continue
        if quote == '"' and char == "\\":
            escaped = True
            continue
        if char in "'\"":
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
            continue
        if char == "#" and quote is None and (index == 0 or value[index - 1].isspace()):
            return value[:index].rstrip()
    return None if quote else value.rstrip()


def yaml_scalar_value(value: str) -> str | None:
    value = strip_yaml_comment(value)
    if value is None or not (value := value.strip()):
        return None
    if value[0] not in "'\"":
        return value
    if len(value) < 2 or value[-1] != value[0]:
        return None
    if value[0] == "'":
        return value[1:-1].replace("''", "'")
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, str) else None


def yaml_inline_list(value: str) -> list[str] | None:
    value = strip_yaml_comment(value)
    if value is None:
        return None
    value = value.strip()
    if not value.startswith("[") or not value.endswith("]"):
        return None
    inner = value[1:-1]
    if not inner.strip():
        return []
    tokens: list[str] = []
    start = 0
    quote: str | None = None
    escaped = False
    for index, char in enumerate(inner):
        if quote == '"' and escaped:
            escaped = False
            continue
        if quote == '"' and char == "\\":
            escaped = True
            continue
        if char in "'\"":
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
            continue
        if quote is None and char in "[]{}":
            return None
        if quote is None and char == ",":
            tokens.append(inner[start:index])
            start = index + 1
    if quote:
        return None
    tokens.append(inner[start:])
    parsed = [yaml_scalar_value(token) for token in tokens]
    if any(item is None for item in parsed):
        return None
    return [item for item in parsed if item is not None]


def yaml_scalar(block: str, key: str) -> str | None:
    """Le um escalar de um bloco YAML simples, suportando blocos > e |.

    Deliberadamente minimo: os arquivos deste protocolo usam YAML plano por
    desenho, para que a validacao nao dependa de biblioteca externa.
    """
    m = re.search(rf"^(\s*){re.escape(key)}:[ \t]*(>-|>|\||\|-)?[ \t]*(.*)$", block, re.M)
    if not m:
        return None
    if m.group(2):
        indent = len(m.group(1))
        out = []
        for line in block[m.end():].splitlines():
            if line.strip() and (len(line) - len(line.lstrip())) <= indent:
                break
            out.append(line.strip())
        return " ".join(x for x in out if x).strip()
    return yaml_scalar_value(m.group(3))


def yaml_list(block: str, key: str) -> list[str]:
    """Le uma lista YAML inline ([a, b]) ou por hifens."""
    m = re.search(rf"^(\s*){re.escape(key)}:[ \t]*(.*)$", block, re.M)
    if not m:
        return []
    tail = strip_yaml_comment(m.group(2))
    if tail is None:
        return []
    if tail.strip():
        return yaml_inline_list(tail) or []
    indent = len(m.group(1))
    out = []
    for line in block[m.end():].splitlines():
        if not line.strip():
            continue
        cur = len(line) - len(line.lstrip())
        if cur <= indent and not line.lstrip().startswith("-"):
            break
        if line.lstrip().startswith("- "):
            value = yaml_scalar_value(line.lstrip()[2:])
            if value is None:
                return []
            out.append(value)
    return out


# Caminhos que o protocolo define. Nenhum deles pode ser excluido do escopo do
# validador: excluir um e silenciar a propria verificacao, nao declarar fronteira.
PROTOCOL_CORE_PATHS = {".agents", "tools", "docs", "project_state"}


def core_paths(root: Path) -> set[str]:
    """Caminhos centrais do protocolo, mais os que ESTE projeto declarar.

    O projeto acrescenta os seus em validator-scope.yaml sob `core_paths:` — o
    diretorio de codigo-fonte, os dados publicados, o que mais nao possa sumir
    do escopo por engano. Fixar essa lista no codigo do validador amarraria o
    protocolo ao layout de um projeto so.
    """
    policy = root / ".agents" / "policy" / "validator-scope.yaml"
    extra = yaml_list(read(policy), "core_paths") if policy.is_file() else []
    return PROTOCOL_CORE_PATHS | {value for value in extra if value}


# Compatibilidade: modulos que so precisam do nucleo do protocolo.
CORE_PATHS = PROTOCOL_CORE_PATHS


@dataclass(frozen=True)
class ValidatorScope:
    top_level: tuple[str, ...]
    recursive: tuple[str, ...]


DEFAULT_SCOPE = ValidatorScope((), (".git", "node_modules", ".tmp"))


def excluded_parts(root: Path) -> ValidatorScope:
    """Fronteiras top-level e diretorios recursivos que nao sao percorridos.

    Um repositorio que hospeda projetos independentes como subpastas precisa
    declarar a fronteira: validar o vizinho produz ruido, nao verificacao. A
    lista fica em .agents/policy/validator-scope.yaml, visivel e revisavel,
    em vez de escondida no codigo do validador. Ausente o arquivo, vale o
    comportamento historico.
    """
    policy = root / ".agents" / "policy" / "validator-scope.yaml"
    if not policy.is_file():
        return DEFAULT_SCOPE
    text = read(policy)
    top_level = [*yaml_list(text, "excluded_paths"), *yaml_list(text, "excluded_harness")]
    recursive = [*yaml_list(text, "excluded_vendor"),
                 *yaml_list(text, "excluded_transient")]
    return ValidatorScope(tuple(top_level), tuple(recursive)) if top_level or recursive else DEFAULT_SCOPE


def walk_files(root: Path, suffixes: set[str], scope: ValidatorScope) -> list[Path]:
    """Percorre a arvore podando os diretorios excluidos.

    Filtrar depois de rglob("*") ainda desce em node_modules e .venv: num
    repositorio com dependencias instaladas isso e a diferenca entre segundos
    e minutos. Podar na descida mantem o gate barato o bastante para rodar
    sempre — validador caro vira validador que ninguem roda.
    """
    out: list[Path] = []
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            entries = list(current.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.name in scope.recursive or (current == root and entry.name in scope.top_level):
                continue
            if entry.is_dir():
                if not entry.is_symlink():
                    stack.append(entry)
            elif not suffixes or entry.suffix.lower() in suffixes:
                out.append(entry)
    return sorted(out)


def iter_markdown(root: Path, scope: ValidatorScope | None = None) -> list[Path]:
    return walk_files(root, {".md"}, excluded_parts(root) if scope is None else scope)


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


SANDBOX_TERM = re.compile(r"\b(sandbox|ai-jail|yolo)\b", re.I)
# A regra normativa e "sandbox nao e adotada", nao "a palavra nao aparece": declarar a
# exclusao exige nomea-la. Uma ocorrencia so viola D-044 quando NAO esta num contexto
# de exclusao, proibicao ou ausencia.
_EXCLUSION_CONTEXT = re.compile(
    r"sem\s|exclu|não|nao\s|nunca|proibi|forbidden|never|D-044|descartad|remov|"
    r"ausen|dispensa|independe|fora d|no-|nenhum",
    re.I)


def sandbox_violation(text: str) -> tuple[str, int] | None:
    """Devolve (termo, linha) da primeira mencao a sandbox FORA de contexto de exclusao.

    Verificar a palavra e nao o sentido reprovaria justamente os documentos que
    tornam a exclusao normativa. O que interessa e a adocao.
    """
    for m in SANDBOX_TERM.finditer(text):
        # A unidade semantica e o paragrafo, nao a linha: em Markdown uma frase quebra
        # em varias linhas, e a palavra que declara a exclusao costuma cair na linha
        # seguinte a da mencao.
        start = text.rfind("\n\n", 0, m.start())
        start = 0 if start == -1 else start + 2
        end = text.find("\n\n", m.end())
        paragraph = text[start:end if end != -1 else len(text)]
        if _EXCLUSION_CONTEXT.search(paragraph):
            continue
        if (m.group(0).lower() == "sandbox"
                and re.search(r"(?m)^\s+enabled:\s*false\s*$", paragraph)
                and re.search(r"(?m)^\s+required:\s*false\s*$", paragraph)):
            continue
        return m.group(0), text[:m.start()].count("\n") + 1
    return None


def print_report(report: Report, verbose: bool = True) -> None:
    status = "OK" if report.ok else "FALHOU"
    counts = f"{len(report.errors)} erro(s), {len(report.warns)} aviso(s)"
    print(f"[{status:6}] {report.name:22} {report.checked} verificacoes, {counts}")
    if verbose:
        for issue in report.issues:
            print(issue.render(), file=sys.stderr if issue.severity == "error" else sys.stdout)
