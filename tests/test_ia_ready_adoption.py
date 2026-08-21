"""Smoke da adocao AI Ready First 4.0.0 e do bundle federado 1.0.0."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestIaReadyAdoption(unittest.TestCase):
    def test_protocol_lock_matches_federation_bundle(self) -> None:
        lock = json.loads(
            (ROOT / "federation" / "protocol" / ".protocol-lock.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(lock["protocolVersion"], "1.0.0")
        self.assertEqual(
            lock["bundleDigest"],
            "sha256:5703c899a6dac0f44dedf69b29558f58a63eceacf0e2ac0b45c1fa02cff95898",
        )
        manifest = json.loads(
            (ROOT / "federation" / "protocol" / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertIn("distribution", manifest)

    def test_agents_points_to_protocol(self) -> None:
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("docs/ai-ready/protocol.md", text)
        self.assertIn("docs/ai-ready/cycle-review.md", text)

    def test_protocol_tools_import(self) -> None:
        sys.path.insert(0, str(ROOT / "tools"))
        import _common  # noqa: E402
        import capture_policy  # noqa: E402
        import currency  # noqa: E402
        import validate  # noqa: E402
        import validate_ai_ready  # noqa: E402
        import validate_coordination  # noqa: E402
        import validate_links  # noqa: E402
        import validate_skills  # noqa: E402
        import validate_state  # noqa: E402
        import verify  # noqa: E402
        from coordination import errors, filesystem, provider, schema_validation  # noqa: E402
        from review import contract  # noqa: E402
        from review import build_prompt, run_engine  # noqa: E402

        self.assertEqual(_common.repo_root().resolve(), ROOT.resolve())
        self.assertTrue(callable(capture_policy.load_redaction_patterns))
        self.assertTrue(callable(currency.check_frozen_banners))
        self.assertTrue(callable(validate.main))
        self.assertTrue(callable(verify.main))
        self.assertTrue(callable(verify.run))
        self.assertTrue(callable(schema_validation.SchemaValidator))
        self.assertIsNotNone(filesystem)
        self.assertIsNotNone(provider)
        self.assertIsNotNone(errors)
        self.assertIsNotNone(contract)
        self.assertTrue(callable(build_prompt.main))
        self.assertTrue(callable(run_engine.main))
        self.assertTrue(callable(validate_ai_ready.run))
        self.assertTrue(callable(validate_state.run))
        self.assertTrue(callable(validate_coordination.run))
        self.assertTrue(callable(validate_links.run))
        self.assertTrue(callable(validate_skills.run))

    def test_protocol_core_module(self) -> None:
        sys.path.insert(0, str(ROOT / "federation" / "protocol"))
        from core import protocol  # noqa: E402

        self.assertTrue(callable(protocol.verify_bundle))
        self.assertTrue(callable(protocol.install_bundle))


if __name__ == "__main__":
    unittest.main()
