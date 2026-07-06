from pathlib import Path

import pytest


@pytest.mark.unit
def test_temporal_migration_contains_required_governance_structures():
    migration = Path("migrations/versions/0003_temporal_governance.py").read_text(encoding="utf-8")
    for token in (
        "field_assertions",
        "data_conflicts",
        "manual_corrections",
        "source_updated_at",
        "uq_assertion_one_current",
        "max_historical_stage",
    ):
        assert token in migration


@pytest.mark.unit
def test_rls_policies_do_not_allow_privileged_runtime_roles():
    migrations = "\n".join(
        Path(path).read_text(encoding="utf-8")
        for path in (
            "migrations/versions/0002_integrity_rls.py",
            "migrations/versions/0003_temporal_governance.py",
        )
    )

    assert "service_role" not in migrations
    assert "'postgres'" not in migrations
