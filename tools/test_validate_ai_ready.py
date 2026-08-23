"""Garante que a varredura de segredo nao lê .env ignorado."""
from validate_ai_ready import _git_tracked, run
from _common import repo_root


def test_git_tracked_omits_dotenv() -> None:
    tracked = {str(path).replace("\\", "/") for path in _git_tracked(repo_root())}
    assert ".env" not in tracked
    assert "backend/.env" not in tracked
    assert "frontend/.env.local" not in tracked


def test_ai_ready_gate_ok() -> None:
    assert run(repo_root()).ok


if __name__ == "__main__":
    test_git_tracked_omits_dotenv()
    test_ai_ready_gate_ok()
    print("ok")
