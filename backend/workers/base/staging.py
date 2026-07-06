"""DuckDB-backed batch staging and deterministic quality gates."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass(frozen=True)
class QualityGateResult:
    accepted: bool
    errors: tuple[str, ...] = field(default_factory=tuple)


def canonical_value_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode()).hexdigest()


def validate_trial_record(record: dict) -> QualityGateResult:
    errors: list[str] = []
    nct_id = record.get("nct_id")
    if not isinstance(nct_id, str) or not nct_id.startswith("NCT") or len(nct_id) != 11:
        errors.append("invalid_nct_id")
    if record.get("enrollment") is not None and record["enrollment"] < 0:
        errors.append("negative_enrollment")
    start, completion = record.get("start_date"), record.get("completion_date")
    if isinstance(start, date) and isinstance(completion, date) and completion < start:
        errors.append("completion_before_start")
    return QualityGateResult(not errors, tuple(errors))


def validate_publication_record(record: dict) -> QualityGateResult:
    errors: list[str] = []
    pmid = record.get("pmid")
    if not isinstance(pmid, str) or not pmid.strip().isdigit():
        errors.append("invalid_pmid")
    if not isinstance(record.get("title"), str) or not record["title"].strip():
        errors.append("missing_title")
    return QualityGateResult(not errors, tuple(errors))


def validate_regulatory_record(record: dict) -> QualityGateResult:
    errors: list[str] = []
    if not isinstance(record.get("asset_name"), str) or not record["asset_name"].strip():
        errors.append("missing_asset_name")
    if not isinstance(record.get("agency"), str) or not record["agency"].strip():
        errors.append("missing_agency")
    approval_date = record.get("approval_date")
    submission_date = record.get("submission_date")
    if (
        isinstance(approval_date, date)
        and isinstance(submission_date, date)
        and approval_date < submission_date
    ):
        errors.append("approval_before_submission")
    return QualityGateResult(not errors, tuple(errors))


def validate_target_record(record: dict) -> QualityGateResult:
    errors: list[str] = []
    if not isinstance(record.get("symbol"), str) or not record["symbol"].strip():
        errors.append("missing_symbol")
    score = record.get("open_targets_score")
    if score is not None and not (0 <= score <= 1):
        errors.append("score_out_of_range")
    return QualityGateResult(not errors, tuple(errors))


def stage_and_deduplicate(rows: list[dict], natural_key: str, updated_key: str) -> list[dict]:
    """Keep the newest candidate per natural key before canonical writes."""
    if not rows:
        return []
    import duckdb

    connection = duckdb.connect(":memory:")
    try:
        connection.execute(
            "CREATE TABLE staging (natural_key VARCHAR, updated_at TIMESTAMP, payload JSON)"
        )
        connection.executemany(
            "INSERT INTO staging VALUES (?, ?, ?)",
            [(str(r[natural_key]), r.get(updated_key), json.dumps(r, default=str)) for r in rows],
        )
        selected = connection.execute(
            """SELECT payload FROM staging QUALIFY row_number() OVER
            (PARTITION BY natural_key ORDER BY updated_at DESC NULLS LAST) = 1"""
        ).fetchall()
        return [json.loads(row[0]) for row in selected]
    finally:
        connection.close()
