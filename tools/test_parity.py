"""Cobre federation/protocol/core/parity.py via o overlay local."""
from __future__ import annotations

import importlib.util
import json

from _common import repo_root


def test_parity_accepts_local_overlay() -> None:
    root = repo_root()
    path = root / "federation" / "protocol" / "core" / "parity.py"
    spec = importlib.util.spec_from_file_location("parity_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    overlay = json.loads((root / "protocol-overlay.yaml").read_text(encoding="utf-8"))
    assert module.forbidden_overlay_fields(overlay) == []
    assert module.unknown_overlay_fields(overlay) == []
    assert module.overlay_is_portable(overlay) is True


if __name__ == "__main__":
    test_parity_accepts_local_overlay()
    print("ok")
