#!/usr/bin/env python3
"""VLAEG phase L (Link) — connectivity handshake for the OPENCODE LLM provider.

Validates that the OPENCODE configuration is correct and the API is reachable
with a minimal, safe request. Never prints the API key.

Usage:
    python tools/handshake_llm.py              # live test (needs OPENCODE_API_KEY)
    python tools/handshake_llm.py --dry-run    # config-only check (no network)
    python tools/handshake_llm.py --mock       # mock response for CI
    make handshake-llm

Exit code is non-zero if the handshake fails, so it can gate CI/pre-flight.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv(BACKEND_DIR / ".env")


def _check_config() -> dict[str, str | None]:
    api_key = os.getenv("OPENCODE_API_KEY")
    base_url = os.getenv("OPENCODE_BASE_URL")
    model = os.getenv("OPENCODE_MODEL_DEEPSEEK_V4_PRO") or os.getenv("LLM_MODEL_PREMIUM")
    return {
        "api_key_set": "yes" if api_key else None,
        "base_url": base_url,
        "model": model,
        "enabled": os.getenv("LLM_ENABLE_NETWORK_CALLS"),
    }


def _print_config(config: dict[str, str | None]) -> None:
    print("OPENCODE LLM — Configuration check")
    print("-" * 40)
    print(f"  API Key      : {'configured' if config['api_key_set'] else 'MISSING'}")
    print(f"  Base URL     : {config['base_url'] or 'MISSING'}")
    print(f"  Model        : {config['model'] or 'MISSING'}")
    print(f"  Net calls    : {config['enabled'] or 'false'}")
    print()


def _do_live_handshake() -> int:
    import time
    import httpx

    api_key = os.getenv("OPENCODE_API_KEY", "")
    base_url = (os.getenv("OPENCODE_BASE_URL") or "").rstrip("/")
    model = os.getenv("OPENCODE_MODEL_DEEPSEEK_V4_PRO") or os.getenv("LLM_MODEL_PREMIUM", "")

    if not api_key:
        print("SKIPPED: OPENCODE_API_KEY is not set")
        return 2
    if not base_url:
        print("FAILED: OPENCODE_BASE_URL is not set")
        return 1
    if not model:
        print("FAILED: model identifier is not set")
        return 1

    print(f"Testing connectivity to {base_url} with model '{model}'...")

    client = httpx.Client(
        base_url=base_url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        timeout=httpx.Timeout(30, connect=10.0),
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Respond with the JSON: {\"status\":\"ok\"}"}
        ],
        "temperature": 0,
        "max_tokens": 10,
        "response_format": {"type": "json_object"},
    }

    start = time.monotonic()
    try:
        resp = client.post("/v1/chat/completions", json=payload)
        elapsed = (time.monotonic() - start) * 1000
    except httpx.TimeoutException:
        print("FAILED: connection timed out after 30s")
        return 1
    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1
    finally:
        client.close()

    if resp.status_code >= 400:
        print(f"FAILED: HTTP {resp.status_code} — {resp.text[:200]}")
        return 1

    body = resp.json()
    content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    usage = body.get("usage", {})
    model_used = body.get("model", model)

    print(f"  Status       : {resp.status_code}")
    print(f"  Model used   : {model_used}")
    print(f"  Latency      : {elapsed:.0f} ms")
    print(f"  Tokens       : {usage.get('total_tokens', 'N/A')}")
    print(f"  Response     : {content.strip()}")

    if content.strip():
        print("\nOPENCODE LLM handshake OK.")
        return 0
    else:
        print("\nFAILED: empty response from provider")
        return 1


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="OPENCODE LLM handshake")
    parser.add_argument("--dry-run", action="store_true", help="Config check only")
    parser.add_argument("--mock", action="store_true", help="Simulate success for CI")
    args = parser.parse_args()

    config = _check_config()
    _print_config(config)

    if args.mock:
        print("MOCK: Skipping real handshake (--mock)")
        return 0

    if args.dry_run:
        if not config["api_key_set"]:
            print("DRY-RUN: OPENCODE_API_KEY missing — would skip in live mode")
            return 2
        if not config["base_url"]:
            print("DRY-RUN: OPENCODE_BASE_URL missing — would fail in live mode")
            return 1
        print("DRY-RUN: Configuration looks valid")
        return 0

    if not os.getenv("OPENCODE_API_KEY"):
        print("SKIPPED: OPENCODE_API_KEY is not set")
        return 2

    return _do_live_handshake()


if __name__ == "__main__":
    raise SystemExit(main())
