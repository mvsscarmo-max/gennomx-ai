#!/usr/bin/env python3
"""VLAEG phase L (Link) — connectivity handshake for registered data sources.

Runs ``BaseConnector.healthcheck()`` for each registered connector and prints a Link
matrix (source, status, latency, detail). Deterministic, read-only, no side effects.

Usage:
    python tools/handshake.py
    make handshake

Exit code is non-zero if any connector handshake fails, so it can gate CI/pre-flight.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Make the backend package importable when run from the repo root.
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from workers.base.connector import BaseConnector, HealthcheckResult  # noqa: E402


def get_registered_connectors() -> list[BaseConnector]:
    """Return one instance per registered connector.

    Add new connectors here as they are implemented so the Link matrix stays complete.
    """
    from workers.connectors.clinicaltrials.connector import ClinicalTrialsConnector
    from workers.connectors.dailymed.connector import DailyMedConnector
    from workers.connectors.ema.connector import EMAConnector
    from workers.connectors.openfda.connector import OpenFDAConnector
    from workers.connectors.opentargets.connector import OpenTargetsConnector
    from workers.connectors.pubmed.connector import PubMedConnector

    return [
        ClinicalTrialsConnector(),
        PubMedConnector(),
        OpenFDAConnector(),
        DailyMedConnector(),
        OpenTargetsConnector(),
        EMAConnector(),
    ]


async def run_all() -> list[HealthcheckResult]:
    connectors = get_registered_connectors()
    return [await c.healthcheck() for c in connectors]


def print_matrix(results: list[HealthcheckResult]) -> None:
    header = f"{'SOURCE':<22} {'STATUS':<12} {'LATENCY':>10}  DETAIL"
    print(header)
    print("-" * len(header))
    for r in results:
        latency = f"{r.latency_ms:.0f} ms" if r.latency_ms is not None else "-"
        mark = "OK " if r.ok else "!! "
        print(f"{mark}{r.source_slug:<19} {r.status:<12} {latency:>10}  {r.detail or ''}")


def main() -> int:
    results = asyncio.run(run_all())
    print_matrix(results)
    failed = [r for r in results if not r.ok]
    if failed:
        print(
            f"\n{len(failed)} connector(s) failed handshake: "
            f"{', '.join(r.source_slug for r in failed)}"
        )
        return 1
    print("\nAll connectors reachable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
