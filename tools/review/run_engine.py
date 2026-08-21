#!/usr/bin/env python3
"""Executa UMA invocacao de motor ja aprovada, com dois relogios.

    python -B tools/review/run_engine.py --stdout out.log --stderr err.log -- \\
        opencode run --model ... --pure --format json "..."

Fronteira (D-044 / PLAN-023 F4): este wrapper nao escolhe motor, nao desce a
escada D-060, nao re-invoca e nao adiciona `--auto`. Recebe o comando que o
humano ja autorizou (tipicamente o que `build_prompt.py --model` imprimiu) e
o executa uma vez.

Dois relogios distintos — misturar foi o erro da primeira calibracao:

  * **stall** (default 600 s): processo vivo com stdout+stderr em 0 bytes, ou
    sem crescimento. Dispara **hang duro** → classe INFRA, 1 tentativa, autoriza
    descida imediata da escada D-060.
  * **teto duro** (default 1800 s): encerra rodada produtiva (com output
    crescendo) que estourou o orcamento de relogio. Continua INVALIDA/INFRA
    com as 2 tentativas de D-061 — nao e hang duro.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_STALL_S = 600
DEFAULT_CEILING_S = 1800
POLL_S = 0.5

OK = "OK"
HANG_DURO = "HANG_DURO"
TETO = "TETO"
ERROR = "ERROR"


@dataclass
class RunResult:
    classification: str
    exit_code: int | None
    elapsed_s: float
    stdout_bytes: int
    stderr_bytes: int
    stalled: bool
    killed: bool
    evidence: str
    command: list[str]
    finished_at: str


def _byte_size(path: Path) -> int:
    try:
        return path.stat().st_size if path.is_file() else 0
    except OSError:
        return 0


def _kill(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    try:
        if os.name == "nt":
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        else:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, OSError):
        pass


def run_command(command: list[str], *, stdout_path: Path, stderr_path: Path,
                stall_s: float = DEFAULT_STALL_S,
                ceiling_s: float = DEFAULT_CEILING_S,
                poll_s: float = POLL_S,
                cwd: Path | None = None) -> RunResult:
    """Roda o comando uma vez sob os dois relogios."""
    if stall_s <= 0 or ceiling_s <= 0:
        raise ValueError("stall e teto devem ser > 0")
    if stall_s > ceiling_s:
        raise ValueError("stall nao pode exceder o teto duro")

    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_f = stdout_path.open("wb")
    stderr_f = stderr_path.open("wb")
    started = time.monotonic()
    last_growth = started
    last_total = 0
    killed = False
    stalled = False
    classification = OK
    evidence = ""

    # Windows: `opencode` no PATH e um shim .cmd/.ps1; Popen sem shell nao resolve.
    resolved = list(command)
    found = shutil.which(resolved[0])
    if found:
        resolved[0] = found

    popen_kwargs: dict = {
        "stdout": stdout_f,
        "stderr": stderr_f,
        "cwd": str(cwd) if cwd else None,
    }
    if os.name != "nt":
        popen_kwargs["start_new_session"] = True

    try:
        proc = subprocess.Popen(resolved, **popen_kwargs)
    except OSError as exc:
        stdout_f.close()
        stderr_f.close()
        return RunResult(
            classification=ERROR, exit_code=None, elapsed_s=0.0,
            stdout_bytes=0, stderr_bytes=0, stalled=False, killed=False,
            evidence=f"falha ao iniciar: {exc}", command=command,
            finished_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

    try:
        while True:
            code = proc.poll()
            now = time.monotonic()
            elapsed = now - started
            out_n = _byte_size(stdout_path)
            err_n = _byte_size(stderr_path)
            total = out_n + err_n
            if total > last_total:
                last_total = total
                last_growth = now

            if code is not None:
                classification = OK if code == 0 else ERROR
                evidence = (f"processo encerrou com codigo {code}; "
                            f"stdout={out_n}B stderr={err_n}B")
                break

            idle = now - last_growth
            if idle >= stall_s:
                # Hang duro: vivo sem crescimento por stall_s (inclui 0 bytes).
                stalled = True
                killed = True
                classification = HANG_DURO
                _kill(proc)
                evidence = (
                    f"hang duro: sem crescimento de stdout+stderr por "
                    f"{stall_s:.0f}s (total={total}B). Classe INFRA — 1 tentativa; "
                    f"autoriza descida imediata da escada D-060. "
                    f"stderr tail nao aplicavel se vazio ou congelado."
                )
                proc.wait(timeout=10)
                break

            if elapsed >= ceiling_s:
                killed = True
                classification = TETO
                _kill(proc)
                evidence = (
                    f"teto duro {ceiling_s:.0f}s atingido com output "
                    f"stdout={out_n}B stderr={err_n}B. INVALIDA/INFRA — mantem "
                    f"as 2 tentativas de D-061 no mesmo motor (nao e hang duro)."
                )
                proc.wait(timeout=10)
                break

            time.sleep(poll_s)
    finally:
        stdout_f.close()
        stderr_f.close()

    out_n = _byte_size(stdout_path)
    err_n = _byte_size(stderr_path)
    # Trecho de stderr para EVIDENCE — so o final, e so se houver bytes.
    if err_n and classification in {HANG_DURO, TETO, ERROR}:
        try:
            tail = stderr_path.read_bytes()[-2000:].decode("utf-8", errors="replace")
            evidence = evidence + "\n--- stderr (tail) ---\n" + tail
        except OSError:
            pass

    return RunResult(
        classification=classification,
        exit_code=proc.poll(),
        elapsed_s=round(time.monotonic() - started, 3),
        stdout_bytes=out_n,
        stderr_bytes=err_n,
        stalled=stalled,
        killed=killed,
        evidence=evidence.strip(),
        command=command,
        finished_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stdout", type=Path, required=True)
    ap.add_argument("--stderr", type=Path, required=True)
    ap.add_argument("--stall-s", type=float, default=DEFAULT_STALL_S,
                    help=f"hang duro sem crescimento (default {DEFAULT_STALL_S})")
    ap.add_argument("--ceiling-s", type=float, default=DEFAULT_CEILING_S,
                    help=f"teto duro da rodada (default {DEFAULT_CEILING_S})")
    ap.add_argument("--poll-s", type=float, default=POLL_S)
    ap.add_argument("--meta", type=Path, help="grava RunResult JSON ao lado dos logs")
    ap.add_argument("--cwd", type=Path)
    ap.add_argument("command", nargs=argparse.REMAINDER,
                    help="comando apos -- ; ex.: -- opencode run ...")
    args = ap.parse_args()

    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        ap.error("passe o comando apos --")

    result = run_command(
        command, stdout_path=args.stdout, stderr_path=args.stderr,
        stall_s=args.stall_s, ceiling_s=args.ceiling_s, poll_s=args.poll_s,
        cwd=args.cwd,
    )
    if args.meta:
        args.meta.parent.mkdir(parents=True, exist_ok=True)
        args.meta.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2),
                             encoding="utf-8")

    print(f"classificacao: {result.classification}")
    print(f"elapsed:       {result.elapsed_s}s")
    print(f"stdout/stderr: {result.stdout_bytes}B / {result.stderr_bytes}B")
    print(f"exit:          {result.exit_code}")
    print(f"evidence:\n{result.evidence}")

    if result.classification == OK:
        return 0
    if result.classification == HANG_DURO:
        return 4
    if result.classification == TETO:
        return 5
    return 2


if __name__ == "__main__":
    sys.exit(main())
