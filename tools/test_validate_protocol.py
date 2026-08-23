"""Exercita validate_protocol.run contra o overlay instalado."""
from _common import repo_root
from validate_protocol import run


def test_protocol_overlay_is_portable() -> None:
    report = run(repo_root())
    assert report.ok


if __name__ == "__main__":
    test_protocol_overlay_is_portable()
    print("ok")
