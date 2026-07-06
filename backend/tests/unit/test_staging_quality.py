from datetime import date

import pytest

from workers.base.staging import canonical_value_hash, stage_and_deduplicate, validate_trial_record


@pytest.mark.unit
def test_canonical_hash_is_key_order_independent():
    assert canonical_value_hash({"a": 1, "b": 2}) == canonical_value_hash({"b": 2, "a": 1})


@pytest.mark.unit
def test_quality_gate_rejects_invalid_dates_and_enrollment():
    result = validate_trial_record(
        {
            "nct_id": "NCT00000001",
            "enrollment": -1,
            "start_date": date(2025, 1, 2),
            "completion_date": date(2025, 1, 1),
        }
    )
    assert not result.accepted
    assert set(result.errors) == {"negative_enrollment", "completion_before_start"}


@pytest.mark.unit
def test_duckdb_staging_keeps_newest_candidate():
    pytest.importorskip("duckdb")
    rows = [
        {"nct_id": "NCT00000001", "updated": "2026-01-01T00:00:00", "value": "old"},
        {"nct_id": "NCT00000001", "updated": "2026-02-01T00:00:00", "value": "new"},
    ]
    assert stage_and_deduplicate(rows, "nct_id", "updated")[0]["value"] == "new"
