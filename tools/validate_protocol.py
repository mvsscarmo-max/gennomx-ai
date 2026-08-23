"""Paridade local do bundle federado 1.1.0 e do protocol-overlay.yaml.

Usa só a cópia instalada em federation/protocol/. Não importa tools da raiz.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

from _common import Report

PROTOCOL_DIR = Path("federation") / "protocol"
LOCK_NAME = ".protocol-lock.json"
OVERLAY_NAME = "protocol-overlay.yaml"
EXPECTED_VERSION = "1.1.0"
SOURCE_COMMIT = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _import_parity(root: Path):
    core_dir = str(root / PROTOCOL_DIR / "core")
    sys.path.insert(0, core_dir)
    try:
        import parity  # type: ignore
    finally:
        if core_dir in sys.path:
            sys.path.remove(core_dir)
    return parity


def run(root: Path) -> Report:
    rep = Report("protocol")
    protocol_root = root / PROTOCOL_DIR
    lock_path = protocol_root / LOCK_NAME
    overlay_path = root / OVERLAY_NAME
    version_path = protocol_root / "VERSION"

    rep.checked += 1
    if not protocol_root.is_dir() or not version_path.is_file():
        rep.error(
            "protocol::bundle-missing",
            str(PROTOCOL_DIR),
            "Cópia instalada do bundle federado ausente.",
            "Instale federation/protocol 1.1.0 com core/protocol.py install.",
        )
        return rep

    version = version_path.read_text(encoding="utf-8").strip()
    rep.checked += 1
    if version != EXPECTED_VERSION:
        rep.error(
            "protocol::version-mismatch",
            str(PROTOCOL_DIR / "VERSION"),
            f"Bundle {version} instalado; esperado {EXPECTED_VERSION}.",
            "Atualize o bundle com install e sourceCommit da raiz.",
        )

    if not lock_path.is_file():
        rep.error(
            "protocol::lock-missing",
            str(PROTOCOL_DIR / LOCK_NAME),
            "Lock do consumidor ausente.",
            "Rode install do bundle para gerar .protocol-lock.json.",
        )
        return rep

    lock = _load_json(lock_path)
    rep.checked += 1
    if lock.get("protocolVersion") != EXPECTED_VERSION:
        rep.error(
            "protocol::lock-version",
            str(PROTOCOL_DIR / LOCK_NAME),
            f"Lock em {lock.get('protocolVersion')}; esperado {EXPECTED_VERSION}.",
            "Reinstale o bundle 1.1.0.",
        )

    source_commit = lock.get("sourceCommit")
    rep.checked += 1
    if not isinstance(source_commit, str) or not SOURCE_COMMIT.fullmatch(source_commit):
        rep.error(
            "protocol::source-commit",
            str(PROTOCOL_DIR / LOCK_NAME),
            "sourceCommit deve ser SHA Git de 40 hex da raiz.",
            "Passe --source-commit com o SHA da raiz no install.",
        )

    rep.checked += 1
    if lock.get("source") != "federation/protocol":
        rep.error(
            "protocol::source-path",
            str(PROTOCOL_DIR / LOCK_NAME),
            "source do lock deve ser o caminho relativo federation/protocol.",
            "Não grave caminho absoluto de máquina no lock.",
        )

    managed = lock.get("managedFiles")
    digests = lock.get("fileDigests")
    if not isinstance(managed, list) or not isinstance(digests, dict):
        rep.error(
            "protocol::lock-files",
            str(PROTOCOL_DIR / LOCK_NAME),
            "managedFiles/fileDigests ausentes ou inválidos.",
            "Regenere o lock com install do bundle.",
        )
        return rep

    managed_set = set(managed)
    for relative in managed:
        path = protocol_root / relative
        rep.checked += 1
        if not path.is_file():
            rep.error(
                "protocol::managed-missing",
                str(PROTOCOL_DIR / relative),
                "Arquivo gerenciado do bundle ausente.",
                "Reinstale o bundle sem editar arquivos gerenciados.",
            )
            continue
        actual = _file_digest(path)
        expected = digests.get(relative)
        if expected != actual:
            rep.error(
                "protocol::managed-drift",
                str(PROTOCOL_DIR / relative),
                "Digest diverge do lock.",
                "Não edite a cópia instalada; reinstale o bundle.",
            )
        if expected and not DIGEST.fullmatch(str(expected)):
            rep.error(
                "protocol::digest-format",
                str(PROTOCOL_DIR / LOCK_NAME),
                f"Digest inválido para {relative}.",
                "Regenere o lock.",
            )

    extra = sorted(
        path.relative_to(protocol_root).as_posix()
        for path in protocol_root.rglob("*")
        if path.is_file()
        and path.name != LOCK_NAME
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
        and path.relative_to(protocol_root).as_posix() not in managed_set
    )
    rep.checked += 1
    if extra:
        rep.error(
            "protocol::extra-files",
            str(PROTOCOL_DIR),
            "Arquivos extras na cópia instalada: " + ", ".join(extra[:8]),
            "Remova arquivos que não pertencem ao bundle.",
        )

    if not overlay_path.is_file():
        rep.error(
            "protocol::overlay-missing",
            OVERLAY_NAME,
            "Overlay semântico local ausente.",
            "Crie protocol-overlay.yaml com campos permitidos e motivo.",
        )
        return rep

    try:
        overlay = _load_json(overlay_path)
    except json.JSONDecodeError as exc:
        rep.error(
            "protocol::overlay-json",
            OVERLAY_NAME,
            f"Overlay não é JSON válido: {exc}",
            "O arquivo usa extensão yaml mas o conteúdo é JSON (como na raiz).",
        )
        return rep

    parity = _import_parity(root)
    forbidden = parity.forbidden_overlay_fields(overlay)
    unknown = parity.unknown_overlay_fields(overlay)
    rep.checked += 2
    if forbidden:
        rep.error(
            "protocol::overlay-forbidden",
            OVERLAY_NAME,
            "Overlay altera autoridade humana ou privacidade: " + ", ".join(forbidden),
            "Remova campos proibidos; overlay não baixa o piso de gates.",
        )
    if unknown:
        rep.error(
            "protocol::overlay-unknown",
            OVERLAY_NAME,
            "Campos de overlay desconhecidos: " + ", ".join(unknown),
            "Use só os campos permitidos do schema semântico 1.1.0.",
        )
    elif not parity.overlay_is_portable(overlay):
        rep.error(
            "protocol::overlay-not-portable",
            OVERLAY_NAME,
            "Overlay rejeitado por parity.overlay_is_portable.",
            "Alinhe o documento ao schema semântico 1.1.0.",
        )

    rep.checked += 1
    if overlay.get("core_version") != EXPECTED_VERSION:
        rep.error(
            "protocol::overlay-core-version",
            OVERLAY_NAME,
            f"core_version {overlay.get('core_version')} ≠ bundle {EXPECTED_VERSION}.",
            "Alinhe core_version ao VERSION instalado.",
        )

    rep.checked += 1
    if overlay.get("vlaeg_edition") != "4.0":
        rep.error(
            "protocol::overlay-edition",
            OVERLAY_NAME,
            "vlaeg_edition deve ser 4.0.",
            "Não declare edição antiga no overlay.",
        )

    fields = overlay.get("fields")
    if not isinstance(fields, list):
        rep.error(
            "protocol::overlay-fields",
            OVERLAY_NAME,
            "fields deve ser uma lista.",
            "Siga o schema semântico 1.1.0.",
        )
        return rep

    for index, item in enumerate(fields):
        rep.checked += 1
        reason = item.get("reason") if isinstance(item, dict) else None
        if not isinstance(reason, str) or len(reason.strip()) < 8:
            rep.error(
                "protocol::overlay-reason",
                f"{OVERLAY_NAME}:fields/{index}",
                "Cada campo do overlay precisa de reason com pelo menos 8 caracteres.",
                "Declare o motivo local da diferença.",
            )

    return rep
