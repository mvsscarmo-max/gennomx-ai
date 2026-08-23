#!/usr/bin/env python3
"""Verify and install the provider-neutral protocol without network access."""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any, Iterable


PROTOCOL_ROOT = Path(__file__).resolve().parents[1]
LOCK_NAME = ".protocol-lock.json"
MANIFEST_NAME = "manifest.json"
SOURCE_NAME = "federation/protocol"
LOCK_ID = "https://vlaeg.local/federation/protocol/lock"
SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
SOURCE_COMMIT = re.compile(r"^[0-9a-f]{40}$")
SENSITIVE_PATHS = [".env", ".env.*", "*.key", "*.pem"]
IGNORED_SUFFIXES = {".pyc"}
IGNORED_DIRECTORIES = {"__pycache__"}
OPERATIONS = ["diff", "install", "update", "verify"]


class ProtocolError(Exception):
    """An expected, fail-closed protocol operation error."""

    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProtocolError("missing-file", f"Missing JSON file: {path}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("invalid-json", f"Cannot read JSON file: {path}") from exc
    if not isinstance(value, dict):
        raise ProtocolError("invalid-json", f"JSON root must be an object: {path}")
    return value


def _write_json_if_changed(path: Path, value: dict[str, Any]) -> bool:
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + "\n"
    if path.is_file() and path.read_text(encoding="utf-8") == encoded:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(encoded)
    os.replace(temporary, path)
    return True


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ProtocolError("read-error", f"Cannot hash file: {path}") from exc
    return f"sha256:{digest.hexdigest()}"


def _relative(path: Path, root: Path) -> str:
    relative = path.relative_to(root).as_posix()
    parts = relative.split("/")
    if not relative or any(part in {"", ".", ".."} for part in parts):
        raise ProtocolError("unsafe-path", f"Unsafe relative path: {relative!r}")
    if "\\" in relative:
        raise ProtocolError("unsafe-path", f"Backslash is not allowed in path: {relative!r}")
    return relative


def _is_runtime_artifact(path: Path) -> bool:
    return any(part in IGNORED_DIRECTORIES for part in path.parts) or path.suffix in IGNORED_SUFFIXES


def _iter_files(root: Path) -> Iterable[tuple[str, Path]]:
    if not root.is_dir():
        raise ProtocolError("missing-directory", f"Protocol directory does not exist: {root}")
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = _relative(path, root)
        if path.is_symlink():
            raise ProtocolError("symlink", f"Symlinks are not allowed in the bundle: {relative}")
        if path.is_file() and not _is_runtime_artifact(path):
            yield relative, path


def _source_records(root: Path) -> list[dict[str, str]]:
    records = [
        {"path": relative, "sha256": _sha256(path)}
        for relative, path in _iter_files(root)
        if relative != MANIFEST_NAME
    ]
    return sorted(records, key=lambda item: item["path"])


def _digest(records: list[dict[str, str]], manifest: dict[str, Any]) -> str:
    digest_manifest = dict(manifest)
    digest_manifest["bundleDigest"] = ""
    payload = (
        "".join(f"{item['path']}\0{item['sha256']}\n" for item in records)
        + "manifest\0"
        + json.dumps(digest_manifest, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _manifest_records(manifest: dict[str, Any]) -> list[dict[str, str]]:
    raw = manifest.get("files")
    if not isinstance(raw, list):
        raise ProtocolError("invalid-manifest", "Manifest files must be a list")
    records: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            raise ProtocolError("invalid-manifest", "Manifest file entries must contain path and sha256")
        path = item["path"]
        checksum = item["sha256"]
        if not isinstance(path, str) or not isinstance(checksum, str):
            raise ProtocolError("invalid-manifest", "Manifest file entries must be strings")
        if path in seen or path == MANIFEST_NAME or path.startswith("/") or "\\" in path:
            raise ProtocolError("unsafe-path", f"Invalid or duplicate manifest path: {path!r}")
        if any(part in {"", ".", ".."} for part in path.split("/")):
            raise ProtocolError("unsafe-path", f"Invalid manifest path: {path!r}")
        if not SHA256.fullmatch(checksum):
            raise ProtocolError("invalid-manifest", f"Invalid SHA-256 value for {path}")
        seen.add(path)
        records.append({"path": path, "sha256": checksum})
    if records != sorted(records, key=lambda item: item["path"]):
        raise ProtocolError("invalid-manifest", "Manifest files must be sorted by path")
    return records


def _validate_manifest_shape(manifest: dict[str, Any], version: str) -> list[dict[str, str]]:
    required = {
        "$schema", "$id", "manifestVersion", "protocolVersion", "source", "operations",
        "distribution", "tests", "files", "bundleDigest", "security",
    }
    if set(manifest) != required:
        missing = sorted(required - set(manifest))
        extra = sorted(set(manifest) - required)
        raise ProtocolError("invalid-manifest", f"Manifest fields differ; missing={missing}, extra={extra}")
    if manifest["manifestVersion"] != 1 or manifest["protocolVersion"] != version:
        raise ProtocolError("invalid-manifest", "Manifest version does not match VERSION")
    if manifest["source"] != SOURCE_NAME:
        raise ProtocolError("invalid-manifest", "Manifest source must be the canonical relative path")
    if manifest["operations"] != OPERATIONS:
        raise ProtocolError("invalid-manifest", "Manifest operations are not the approved set")
    for field in ("distribution", "tests"):
        values = manifest[field]
        if not isinstance(values, list) or values != sorted(values) or not all(isinstance(item, str) for item in values):
            raise ProtocolError("invalid-manifest", f"Manifest {field} must be a sorted string list")
        if any(
            path == LOCK_NAME or path.startswith("/") or "\\" in path
            or any(part in {"", ".", ".."} for part in path.split("/"))
            for path in values
        ):
            raise ProtocolError("unsafe-path", f"Manifest {field} contains an unsafe path")
    security = manifest["security"]
    if not isinstance(security, dict) or set(security) != {"commands", "network", "secrets", "sensitivePaths"}:
        raise ProtocolError("invalid-manifest", "Manifest security must be an object")
    if security["commands"] != "not-distributed" or security["network"] != "disabled-by-default" \
            or security["secrets"] != "forbidden" or security["sensitivePaths"] != SENSITIVE_PATHS:
        raise ProtocolError("invalid-manifest", "Manifest security values are not the approved set")
    if not all(isinstance(path, str) and path for path in security["sensitivePaths"]):
        raise ProtocolError("invalid-manifest", "Manifest sensitive paths must be non-empty strings")
    if not SHA256.fullmatch(manifest["bundleDigest"]):
        raise ProtocolError("invalid-manifest", "Manifest bundleDigest must be a sha256 value")
    return _manifest_records(manifest)


def _reject_sensitive_paths(records: Iterable[dict[str, str]], patterns: list[str]) -> None:
    for record in records:
        path = record["path"]
        name = Path(path).name
        if any(fnmatch.fnmatchcase(path, pattern) or fnmatch.fnmatchcase(name, pattern) for pattern in patterns):
            raise ProtocolError("sensitive-path", f"Sensitive path is not allowed in the bundle: {path}")


def _read_version(root: Path) -> str:
    path = root / "VERSION"
    try:
        version = path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as exc:
        raise ProtocolError("missing-file", "Cannot read VERSION") from exc
    if not SEMVER.fullmatch(version):
        raise ProtocolError("invalid-version", "VERSION must contain a three-part semver")
    return version


def verify_bundle(root: Path = PROTOCOL_ROOT) -> dict[str, Any]:
    root = root.resolve()
    version = _read_version(root)
    actual = _source_records(root)
    manifest = _read_json(root / MANIFEST_NAME)
    expected = _validate_manifest_shape(manifest, version)
    _reject_sensitive_paths(expected, manifest["security"]["sensitivePaths"])
    expected_by_path = {item["path"]: item["sha256"] for item in expected}
    actual_by_path = {item["path"]: item["sha256"] for item in actual}
    missing = sorted(set(expected_by_path) - set(actual_by_path))
    extra = sorted(set(actual_by_path) - set(expected_by_path))
    changed = sorted(
        path for path in set(expected_by_path) & set(actual_by_path)
        if expected_by_path[path] != actual_by_path[path]
    )
    if missing or extra or changed:
        raise ProtocolError(
            "bundle-drift",
            "Bundle files differ from manifest",
            {"missing": missing, "extra": extra, "changed": changed},
        )
    digest = _digest(actual, manifest)
    if digest != manifest["bundleDigest"]:
        raise ProtocolError("bundle-drift", "Bundle digest differs from manifest", {"expected": manifest["bundleDigest"], "actual": digest})
    distribution = set(manifest["distribution"])
    tests = set(manifest["tests"])
    listed = set(expected_by_path) | {MANIFEST_NAME}
    if not distribution or not distribution.issubset(listed) or not tests.issubset(listed) or distribution & tests:
        raise ProtocolError("invalid-manifest", "Distribution and test file lists are inconsistent")
    return {
        "status": "verified",
        "protocolVersion": version,
        "bundleDigest": digest,
        "fileCount": len(actual),
        "distribution": sorted(distribution),
    }


def _validate_lock(lock: dict[str, Any]) -> None:
    required = {
        "$schema", "$id", "protocolVersion", "sourceCommit", "bundleDigest", "source", "overlay", "patches",
        "managedFiles", "fileDigests", "semanticOverlaySchema", "semanticCore",
    }
    if set(lock) != required:
        raise ProtocolError("invalid-lock", "Lock fields differ from the protocol lock schema")
    if lock["$id"] != LOCK_ID:
        raise ProtocolError("invalid-lock", "Lock $id must be the canonical absolute URI")
    if not isinstance(lock["protocolVersion"], str) or not SEMVER.fullmatch(lock["protocolVersion"]):
        raise ProtocolError("invalid-lock", "Lock protocolVersion must be semver")
    if not isinstance(lock["sourceCommit"], str) or not SOURCE_COMMIT.fullmatch(lock["sourceCommit"]):
        raise ProtocolError("invalid-lock", "Lock sourceCommit must be a 40-character Git SHA")
    if not isinstance(lock["bundleDigest"], str) or not SHA256.fullmatch(lock["bundleDigest"]):
        raise ProtocolError("invalid-lock", "Lock bundleDigest must be a sha256 value")
    if lock["source"] != SOURCE_NAME or lock["overlay"] != "base":
        raise ProtocolError("invalid-lock", "Lock source or overlay is not canonical")
    if lock["patches"] != []:
        raise ProtocolError("invalid-lock", "Only the empty patch list is supported by the base bundle")
    if lock["semanticOverlaySchema"] != "schemas/semantic-overlay.schema.json":
        raise ProtocolError("invalid-lock", "Lock semanticOverlaySchema must be the bundled schema")
    if lock["semanticCore"] != "core/parity.py":
        raise ProtocolError("invalid-lock", "Lock semanticCore must be the bundled parity module")
    files = lock["managedFiles"]
    if not isinstance(files, list) or files != sorted(files) or not all(isinstance(item, str) for item in files):
        raise ProtocolError("invalid-lock", "Lock managedFiles must be a sorted string list")
    if any(
        path == LOCK_NAME or path.startswith("/") or "\\" in path
        or any(part in {"", ".", ".."} for part in path.split("/"))
        for path in files
    ):
        raise ProtocolError("unsafe-path", "Lock managedFiles contain an unsafe path")
    digests = lock["fileDigests"]
    if not isinstance(digests, dict) or list(digests) != sorted(digests) or set(digests) != set(files):
        raise ProtocolError("invalid-lock", "Lock fileDigests must match managedFiles")
    if not all(isinstance(path, str) and isinstance(checksum, str) and SHA256.fullmatch(checksum)
               for path, checksum in digests.items()):
        raise ProtocolError("invalid-lock", "Lock fileDigests contain an invalid checksum")


def _lock_path(target: Path, explicit: Path | None) -> Path:
    lock = explicit.resolve() if explicit else target.resolve() / LOCK_NAME
    if lock.name != LOCK_NAME or lock.parent != target.resolve():
        raise ProtocolError("unsafe-lock", "Lock path must be the standard file inside the target")
    return lock


def _target_records(target: Path) -> list[dict[str, str]]:
    if not target.exists():
        return []
    return [
        {"path": relative, "sha256": _sha256(path)}
        for relative, path in _iter_files(target)
        if relative != LOCK_NAME
    ]


def _target_drift_against_lock(target: Path, lock: dict[str, Any]) -> dict[str, list[str]]:
    expected = lock["fileDigests"]
    actual = {item["path"]: item["sha256"] for item in _target_records(target)}
    missing = sorted(set(expected) - set(actual))
    changed = sorted(path for path in set(expected) & set(actual) if expected[path] != actual[path])
    extra = sorted(set(actual) - set(expected))
    return {"missing": missing, "changed": changed, "extra": extra}


def _lock_for_source(
    source: Path, source_result: dict[str, Any], manifest: dict[str, Any], source_commit: str,
) -> dict[str, Any]:
    if not SOURCE_COMMIT.fullmatch(source_commit):
        raise ProtocolError("invalid-lock", "Source commit must be a 40-character Git SHA")
    managed = sorted(manifest["distribution"])
    digests = {path: _sha256(source / path) for path in managed}
    return {
        "$schema": "https://vlaeg.local/federation/protocol/schemas/protocol-lock.schema.json",
        "$id": LOCK_ID,
        "protocolVersion": source_result["protocolVersion"],
        "sourceCommit": source_commit,
        "bundleDigest": source_result["bundleDigest"],
        "source": SOURCE_NAME,
        "overlay": "base",
        "patches": [],
        "managedFiles": managed,
        "fileDigests": digests,
        "semanticOverlaySchema": "schemas/semantic-overlay.schema.json",
        "semanticCore": "core/parity.py",
    }


def diff_bundle(
    source: Path, target: Path, source_commit: str, lock_path: Path | None = None,
) -> dict[str, Any]:
    _ensure_target(source, target)
    source = source.resolve()
    target = target.resolve()
    source_result = verify_bundle(source)
    source_manifest = _read_json(source / MANIFEST_NAME)
    source_records = _manifest_records(source_manifest)
    source_by_path = {item["path"]: item["sha256"] for item in source_records}
    managed = set(source_manifest["distribution"])
    if MANIFEST_NAME in managed:
        source_by_path[MANIFEST_NAME] = _sha256(source / MANIFEST_NAME)
    lock_file = _lock_path(target, lock_path)
    lock_issues: list[str] = []
    if not lock_file.is_file():
        lock_issues.append("missing")
    else:
        lock = _read_json(lock_file)
        try:
            _validate_lock(lock)
        except ProtocolError:
            lock_issues.append("invalid")
        else:
            if lock["protocolVersion"] != source_result["protocolVersion"]:
                lock_issues.append("protocolVersion")
            if lock["sourceCommit"] != source_commit:
                lock_issues.append("sourceCommit")
            if lock["bundleDigest"] != source_result["bundleDigest"]:
                lock_issues.append("bundleDigest")
            if set(lock["managedFiles"]) != managed:
                lock_issues.append("managedFiles")
    actual = _target_records(target)
    actual_by_path = {item["path"]: item["sha256"] for item in actual}
    missing = sorted(managed - set(actual_by_path))
    changed = sorted(
        path for path in managed & set(actual_by_path)
        if source_by_path[path] != actual_by_path[path]
    )
    extra = sorted(set(actual_by_path) - managed)
    differences = bool(lock_issues or missing or changed or extra)
    return {
        "status": "drift" if differences else "clean",
        "protocolVersion": source_result["protocolVersion"],
        "bundleDigest": source_result["bundleDigest"],
        "lock": lock_issues,
        "missing": missing,
        "changed": changed,
        "extra": extra,
    }


def _ensure_target(source: Path, target: Path) -> None:
    if source.is_symlink() or target.is_symlink():
        raise ProtocolError("symlink", "Source and target must not be symlinks")
    source = source.resolve()
    target = target.resolve()
    if target == source or source in target.parents or target in source.parents:
        raise ProtocolError("unsafe-target", "Install target cannot be the source or inside the source")
    if target.exists() and not target.is_dir():
        raise ProtocolError("invalid-target", "Install target must be a directory")


def _copy_distribution(source: Path, target: Path, distribution: list[str]) -> bool:
    changed = False
    for relative in distribution:
        source_file = source / relative
        target_file = target / relative
        if not source_file.is_file() or source_file.is_symlink():
            raise ProtocolError("invalid-manifest", f"Distribution file is not a regular file: {relative}")
        target_file.parent.mkdir(parents=True, exist_ok=True)
        source_bytes = source_file.read_bytes()
        if target_file.is_file() and target_file.read_bytes() == source_bytes:
            continue
        with tempfile.NamedTemporaryFile("wb", dir=target_file.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(source_bytes)
        os.replace(temporary, target_file)
        changed = True
    return changed


def _staging_directory(target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=f".{target.name}.stage-", dir=target.parent))


def _replace_directory(staged: Path, target: Path) -> None:
    backup = target.parent / f".{target.name}.backup-{uuid.uuid4().hex}"
    moved_target = False
    try:
        if target.exists():
            os.replace(target, backup)
            moved_target = True
        os.replace(staged, target)
    except OSError as exc:
        if moved_target and backup.exists() and not target.exists():
            try:
                os.replace(backup, target)
            except OSError as restore_exc:
                raise ProtocolError("write-error", f"Cannot restore target after failed replacement: {target}") from restore_exc
        raise ProtocolError("write-error", f"Cannot replace target directory: {target}") from exc
    if backup.exists():
        try:
            shutil.rmtree(backup)
        except OSError as exc:
            raise ProtocolError("write-error", f"Cannot remove replacement backup: {backup}") from exc


def install_bundle(
    source: Path, target: Path, source_commit: str, lock_path: Path | None = None,
) -> dict[str, Any]:
    _ensure_target(source, target)
    source = source.resolve()
    target = target.resolve()
    source_result = verify_bundle(source)
    lock_file = _lock_path(target, lock_path)
    if target.exists() and any(target.iterdir()):
        if lock_file.is_file():
            current = diff_bundle(source, target, source_commit, lock_file)
            if current["status"] == "clean":
                return {**source_result, "status": "already-current", "changed": False}
            raise ProtocolError("target-drift", "Existing install has drift; use update after reviewing diff", current)
        raise ProtocolError("target-not-empty", "Install refuses to overwrite an occupied target")
    manifest = _read_json(source / MANIFEST_NAME)
    staged = _staging_directory(target)
    try:
        changed = _copy_distribution(source, staged, manifest["distribution"])
        lock = _lock_for_source(source, source_result, manifest, source_commit)
        changed = _write_json_if_changed(staged / LOCK_NAME, lock) or changed
        _replace_directory(staged, target)
        return {**source_result, "status": "installed", "changed": changed}
    except ProtocolError:
        raise
    except OSError as exc:
        raise ProtocolError("write-error", f"Cannot install bundle into target: {target}") from exc
    finally:
        if staged.exists():
            shutil.rmtree(staged)


def update_bundle(
    source: Path, target: Path, source_commit: str, lock_path: Path | None = None,
) -> dict[str, Any]:
    _ensure_target(source, target)
    source = source.resolve()
    target = target.resolve()
    if not target.is_dir():
        raise ProtocolError("missing-target", "Update target does not exist")
    lock_file = _lock_path(target, lock_path)
    if not lock_file.is_file():
        raise ProtocolError("missing-lock", "Update requires a consumer lock")
    old_lock = _read_json(lock_file)
    _validate_lock(old_lock)
    local_drift = _target_drift_against_lock(target, old_lock)
    if any(local_drift.values()):
        raise ProtocolError("target-drift", "Update refuses undeclared local drift", local_drift)
    source_result = verify_bundle(source)
    if old_lock["bundleDigest"] == source_result["bundleDigest"] and old_lock["sourceCommit"] == source_commit:
        return {**source_result, "status": "already-current", "changed": False}
    manifest = _read_json(source / MANIFEST_NAME)
    old_managed = set(old_lock["managedFiles"])
    new_managed = set(manifest["distribution"])
    staged = _staging_directory(target)
    try:
        shutil.copytree(target, staged, dirs_exist_ok=True)
        for relative in sorted(old_managed - new_managed):
            path = staged / relative
            if path.is_file():
                path.unlink()
        changed = _copy_distribution(source, staged, manifest["distribution"])
        new_lock = _lock_for_source(source, source_result, manifest, source_commit)
        changed = _write_json_if_changed(staged / LOCK_NAME, new_lock) or changed
        _replace_directory(staged, target)
        return {**source_result, "status": "updated", "changed": changed}
    except ProtocolError:
        raise
    except OSError as exc:
        raise ProtocolError("write-error", f"Cannot update bundle in target: {target}") from exc
    finally:
        if staged.exists():
            shutil.rmtree(staged)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    verify = commands.add_parser("verify", help="verify the source bundle")
    verify.add_argument("--root", type=Path, default=PROTOCOL_ROOT)
    diff = commands.add_parser("diff", help="compare an installed copy with the source bundle")
    diff.add_argument("--root", type=Path, default=PROTOCOL_ROOT)
    diff.add_argument("--target", type=Path, required=True)
    diff.add_argument("--source-commit", required=True)
    diff.add_argument("--lock", type=Path)
    install = commands.add_parser("install", help="install the source bundle into an empty target")
    install.add_argument("--root", type=Path, default=PROTOCOL_ROOT)
    install.add_argument("--target", type=Path, required=True)
    install.add_argument("--source-commit", required=True)
    install.add_argument("--lock", type=Path)
    update = commands.add_parser("update", help="update an existing, drift-free install")
    update.add_argument("--root", type=Path, default=PROTOCOL_ROOT)
    update.add_argument("--target", type=Path, required=True)
    update.add_argument("--source-commit", required=True)
    update.add_argument("--lock", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.operation == "verify":
            result = verify_bundle(args.root)
        elif args.operation == "diff":
            result = diff_bundle(args.root, args.target, args.source_commit, args.lock)
        elif args.operation == "install":
            result = install_bundle(args.root, args.target, args.source_commit, args.lock)
        else:
            result = update_bundle(args.root, args.target, args.source_commit, args.lock)
    except ProtocolError as exc:
        payload = {"status": "error", "code": exc.code, "message": exc.message, **exc.details}
        print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2))
    return 1 if args.operation == "diff" and result["status"] != "clean" else 0


if __name__ == "__main__":
    raise SystemExit(main())
