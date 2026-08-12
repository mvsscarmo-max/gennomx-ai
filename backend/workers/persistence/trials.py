"""Persistence logic for ClinicalTrials.gov clinical trial records."""

import json
import uuid
from datetime import UTC, date, datetime, time, timedelta
from types import SimpleNamespace

import structlog
from sqlalchemy import text

from app.services.persistence_decision import (
    AssertionCandidate,
    CurrentAssertion,
    PersistenceAction,
)
from workers.base.connector import ConnectorResult
from workers.base.staging import (
    canonical_value_hash,
    stage_and_deduplicate,
    validate_trial_record,
)
from workers.persistence.assets import _upsert_drug_assets_from_trial
from workers.persistence.clinical_outcomes import persist_clinical_outcomes
from workers.persistence.common import (
    DECISION_ENGINE,
    _get_data_source_id,
    _record_data_conflict,
)
from workers.persistence.evidence import _insert_evidence_snippet
from workers.storage.raw_payload import store_raw_payload

logger = structlog.get_logger(__name__)

TRIAL_JSONB_FIELDS = {
    "other_ids",
    "collaborators",
    "interventions",
    "arms",
    "locations",
    "ingestion_metadata",
}


async def _persist_trials(db, result: ConnectorResult, normalizer) -> None:
    """Upsert parsed trials into the clinical_trials table."""
    source_id = await _get_data_source_id(db, "clinicaltrials_gov")
    systemic_failures = 0

    payloads = _stage_trial_payloads(result.raw_payloads)
    result.records_skipped += len(result.raw_payloads) - len(payloads)

    for payload in payloads:
        parsed = payload.get("parsed")
        raw_hash = payload["hash"]
        raw = payload["raw"]

        if not parsed or not parsed.nct_id:
            result.records_rejected += 1
            continue

        try:
            async with db.begin_nested():
                normalized = normalizer.normalize(parsed)
                parsed.phase_normalized = normalized.get("phase_normalized")
                parsed.status_normalized = normalized.get("status_normalized")
                normalized["raw_payload_hash"] = raw_hash
                source_document_id = await _upsert_source_document(
                    db=db, source_id=source_id, parsed=parsed, raw_hash=raw_hash, raw=raw
                )
                normalized["source_document_id"] = source_document_id
                normalized["ingestion_metadata"] = {
                    "source": "clinicaltrials_gov",
                    "ingested_at": datetime.now(UTC).isoformat(),
                    "source_document_id": source_document_id,
                }
                normalized["lifecycle_status"] = "active"
                normalized["is_current"] = True
                quality = validate_trial_record(normalized)
                if not quality.accepted:
                    raise ValueError(f"quality_gate_failed:{','.join(quality.errors)}")
                existing = await db.execute(
                    text("""
                        SELECT id, source_updated_at, raw_payload_hash
                        FROM clinical_trials WHERE nct_id = :nct_id
                    """),
                    {"nct_id": parsed.nct_id},
                )
                row = existing.fetchone()
                if row:
                    trial_id = str(row[0])
                    decision = DECISION_ENGINE.decide(
                        AssertionCandidate(
                            value=normalized,
                            value_hash=raw_hash,
                            source_updated_at=normalized.get("source_updated_at"),
                            authority_score=1.0,
                            confidence_score=0.98,
                            evidence_present=bool(raw),
                        ),
                        CurrentAssertion(
                            value=None,
                            value_hash=row[2] or "",
                            source_updated_at=row[1],
                            authority_score=1.0,
                        ),
                    )
                    if decision.action in {PersistenceAction.NOOP, PersistenceAction.ARCHIVE}:
                        operation = "skipped"
                    elif decision.action in {
                        PersistenceAction.CONFLICT,
                        PersistenceAction.QUARANTINE,
                    }:
                        await _record_data_conflict(db, trial_id, "record", decision.reason_code)
                        operation = "skipped"
                    else:
                        operation = "updated"
                else:
                    trial_id = ""
                    operation = "inserted"
                    decision = None
                if operation != "skipped":
                    normalized["drug_asset_ids"] = await _upsert_drug_assets_from_trial(
                        db=db,
                        parsed=parsed,
                        source_document_id=source_document_id,
                        raw=raw,
                    )
                    if operation == "updated":
                        await _update_trial(db, trial_id, normalized)
                    else:
                        trial_id = await _insert_trial(db, normalized)
                    await _sync_trial_asset_links(
                        db, trial_id, normalized["drug_asset_ids"], source_document_id
                    )
                    await _insert_evidence_snippet(
                        db=db, source_document_id=source_document_id, trial_id=trial_id, raw=raw
                    )
                    await _insert_trial_assertions(
                        db, trial_id, source_document_id, parsed.nct_id, normalized
                    )
                if operation != "skipped" or (
                    row and decision and decision.action == PersistenceAction.NOOP
                ):
                    granular_counts = await persist_clinical_outcomes(
                        db,
                        trial_id=trial_id,
                        source_document_id=source_document_id,
                        parsed=parsed,
                        raw=raw,
                    )
                    aggregate = result.metadata.setdefault(
                        "clinical_outcomes",
                        {"endpoints": 0, "results": 0, "adverse_events": 0},
                    )
                    for key, value in granular_counts.items():
                        aggregate[key] += value
            if operation == "updated":
                result.records_updated += 1
            elif operation == "inserted":
                result.records_inserted += 1
            else:
                result.records_skipped += 1

        except Exception as e:
            result.records_rejected += 1
            systemic_failures += 1
            errors = result.metadata.setdefault("persistence_errors", [])
            if len(errors) < 20:
                errors.append({"nct_id": parsed.nct_id, "error_type": type(e).__name__})
            logger.error("trial_persist_error", nct_id=parsed.nct_id, error=str(e))

    if payloads and systemic_failures == len(payloads):
        raise RuntimeError("All parsed records failed during persistence")
    await db.commit()


def _stage_trial_payloads(payloads: list[dict]) -> list[dict]:
    """Use DuckDB only when a page contains duplicate natural keys."""
    indexed: list[dict] = []
    invalid: list[dict] = []
    keys: list[str] = []
    for index, payload in enumerate(payloads):
        parsed = payload.get("parsed")
        if not parsed or not getattr(parsed, "nct_id", None):
            invalid.append(payload)
            continue
        nct_id = str(parsed.nct_id)
        keys.append(nct_id)
        indexed.append(
            {
                "nct_id": nct_id,
                "updated_at": getattr(parsed, "last_update_date", None),
                "payload_index": index,
            }
        )
    if len(set(keys)) == len(keys):
        return payloads
    selected = stage_and_deduplicate(indexed, "nct_id", "updated_at")
    return [payloads[int(item["payload_index"])] for item in selected] + invalid


async def _sync_trial_asset_links(
    db, trial_id: str, asset_ids: list[str], source_document_id: str | None
) -> None:
    """Maintain the canonical trial↔asset relation; the array remains a read cache."""
    await db.execute(
        text("""
            INSERT INTO clinical_trial_asset_history (
                id, trial_id, asset_id, source_document_id, valid_from, valid_to,
                system_from, system_to, lifecycle_status, created_at
            )
            SELECT gen_random_uuid(), trial_id, asset_id, source_document_id,
                   valid_from, now(), system_from, now(), 'superseded', now()
            FROM clinical_trial_assets
            WHERE trial_id = :trial_id AND is_current = true
        """),
        {"trial_id": trial_id},
    )
    await db.execute(
        text("DELETE FROM clinical_trial_assets WHERE trial_id = :trial_id"),
        {"trial_id": trial_id},
    )
    for asset_id in asset_ids:
        await db.execute(
            text("""
                INSERT INTO clinical_trial_assets (
                    trial_id, asset_id, source_document_id, valid_from,
                    system_from, is_current, lifecycle_status
                ) VALUES (
                    :trial_id, :asset_id, :source_document_id, now(), now(), true, 'active'
                )
                ON CONFLICT (trial_id, asset_id) DO UPDATE
                SET source_document_id = EXCLUDED.source_document_id,
                    valid_to = NULL, system_to = NULL, is_current = true,
                    lifecycle_status = 'active'
            """),
            {
                "trial_id": trial_id,
                "asset_id": asset_id,
                "source_document_id": source_document_id,
            },
        )


async def link_existing_trials_to_assets(db, limit: int = 500) -> dict:
    """Backfill trial->asset links for already ingested ClinicalTrials.gov records."""
    rows = (
        await db.execute(
            text("""
                SELECT id::text, nct_id, phase_normalized, sponsor_name, conditions,
                       interventions, source_document_id
                FROM clinical_trials
                WHERE interventions IS NOT NULL
                  AND (drug_asset_ids IS NULL OR cardinality(drug_asset_ids) = 0)
                ORDER BY updated_at DESC
                LIMIT :limit
            """),
            {"limit": limit},
        )
    ).fetchall()

    linked_trials = 0
    linked_assets = 0
    for row in rows:
        parsed = SimpleNamespace(
            nct_id=row[1],
            phase_normalized=row[2],
            sponsor_name=row[3],
            conditions=row[4] or [],
            interventions=row[5] or [],
        )
        asset_ids = await _upsert_drug_assets_from_trial(
            db=db,
            parsed=parsed,
            source_document_id=row[6],
        )
        if not asset_ids:
            continue
        await db.execute(
            text("""
                UPDATE clinical_trials
                SET drug_asset_ids = :drug_asset_ids,
                    updated_at = now()
                WHERE id = :trial_id
            """),
            {"trial_id": row[0], "drug_asset_ids": asset_ids},
        )
        linked_trials += 1
        linked_assets += len(asset_ids)

    await db.commit()
    return {"status": "success", "linked_trials": linked_trials, "linked_assets": linked_assets}


async def _upsert_source_document(
    *,
    db,
    source_id: str | None,
    parsed,
    raw_hash: str,
    raw: dict | None,
) -> str:
    source_updated_at = getattr(parsed, "last_update_date", None)
    if isinstance(source_updated_at, date) and not isinstance(source_updated_at, datetime):
        source_updated_at = datetime.combine(source_updated_at, time.min, tzinfo=UTC)
    existing = (
        await db.execute(
            text("""
                SELECT id::text, raw_storage_path
                FROM source_documents
                WHERE content_hash = :content_hash
                  AND data_source_id IS NOT DISTINCT FROM :data_source_id
                  AND external_record_id = :external_record_id
            """),
            {
                "content_hash": raw_hash,
                "data_source_id": source_id,
                "external_record_id": parsed.nct_id,
            },
        )
    ).fetchone()
    if existing and existing[1]:
        return str(existing[0])

    if not raw:
        raise ValueError("Raw payload is required for source-document traceability")
    stored = await store_raw_payload(
        source_slug="clinicaltrials_gov",
        external_id=parsed.nct_id,
        payload=raw,
        content_hash=raw_hash,
    )
    if existing:
        await db.execute(
            text("""
                UPDATE source_documents
                SET raw_storage_path = :path, updated_at = now()
                WHERE id = :id
            """),
            {"id": str(existing[0]), "path": stored.path},
        )
        return str(existing[0])

    source_document_id = str(uuid.uuid4())
    nct_url = f"https://clinicaltrials.gov/study/{parsed.nct_id}"
    await db.execute(
        text("""
            INSERT INTO source_documents (
                id, data_source_id, source_type, title, url, content_hash,
                external_record_id, source_updated_at, retrieved_at,
                raw_storage_path, license_status, metadata,
                created_at, updated_at
            )
            VALUES (
                :id, :data_source_id, :source_type, :title, :url, :content_hash,
                :external_record_id, :source_updated_at, now(),
                :raw_storage_path, :license_status,
                CAST(:metadata AS jsonb), now(), now()
            )
        """),
        {
            "id": source_document_id,
            "data_source_id": source_id,
            "source_type": "clinical_trial_registry",
            "title": parsed.title or parsed.nct_id,
            "url": nct_url,
            "content_hash": raw_hash,
            "external_record_id": parsed.nct_id,
            "source_updated_at": source_updated_at,
            "license_status": "open",
            "raw_storage_path": stored.path,
            "metadata": json.dumps(
                {
                    "source": "clinicaltrials_gov",
                    "nct_id": parsed.nct_id,
                    "payload_keys": sorted((raw or {}).keys()),
                    "raw_byte_count_gzip": stored.byte_count,
                    "raw_format": "json+gzip",
                    "connector_version": "clinicaltrials_api_v2",
                }
            ),
        },
    )
    return source_document_id


async def _insert_trial_assertions(
    db, trial_id: str, source_document_id: str, source_record_id: str, normalized: dict
) -> None:
    """Version critical fields without overwriting prior assertions."""
    for field_path in ("status_normalized", "phase_normalized", "enrollment", "sponsor_name"):
        value = normalized.get(field_path)
        if value is None:
            continue
        value_hash = canonical_value_hash(value)
        current = (
            await db.execute(
                text("""
                    SELECT id::text, value_hash FROM field_assertions
                    WHERE entity_type = 'clinical_trial' AND entity_id = :entity_id
                      AND field_path = :field_path
                      AND granularity_key = 'registry=clinicaltrials.gov'
                      AND is_current = true
                    FOR UPDATE
                """),
                {"entity_id": trial_id, "field_path": field_path},
            )
        ).fetchone()
        if current and current[1] == value_hash:
            continue
        if current:
            await db.execute(
                text("""
                    UPDATE field_assertions
                    SET is_current = false, lifecycle_status = 'superseded',
                        valid_to = now(), system_to = now(), updated_at = now()
                    WHERE id = :id
                """),
                {"id": current[0]},
            )
        await db.execute(
            text("""
                INSERT INTO field_assertions (
                    id, entity_type, entity_id, field_path, granularity_key,
                    value_json, value_hash, source_document_id, evidence_snippet_id,
                    source_record_id,
                    source_updated_at, observed_at, valid_from, system_from, is_current,
                    lifecycle_status, update_type, supersedes_assertion_id,
                    extraction_method, normalizer_version, rule_set_version,
                    authority_score, confidence_score, relevance_score,
                    freshness_score, completeness_score, conflict_status, review_status,
                    data_class, source_type, priority, evidence_maturity,
                    novelty_score, clinical_impact_score, validation_status, expires_at,
                    created_at, updated_at
                ) VALUES (
                    :id, 'clinical_trial', :entity_id, :field_path,
                    'registry=clinicaltrials.gov',
                    CAST(:value_json AS jsonb), :value_hash, :source_document_id,
                    (SELECT id FROM evidence_snippets
                     WHERE source_document_id = :source_document_id
                       AND entity_type = 'clinical_trial' AND entity_id = :entity_id
                       AND entity_field = :field_path LIMIT 1),
                    :source_record_id,
                    :source_updated_at, now(), :source_updated_at, now(), true,
                    'active', :update_type, :supersedes_assertion_id,
                    'api_structured', 'clinicaltrials_normalizer_v1', '2026-06-20.1',
                    1.0, 0.99, 1.0, 1.0, 1.0, 'none', 'unreviewed',
                    'operational', 'official_registry', 90, 'registry_record',
                    0.0, NULL, 'confirmed',
                    :expires_at,
                    now(), now()
                )
            """),
            {
                "id": str(uuid.uuid4()),
                "entity_id": trial_id,
                "field_path": field_path,
                "value_json": json.dumps(value),
                "value_hash": value_hash,
                "source_document_id": source_document_id,
                "source_record_id": source_record_id,
                "source_updated_at": normalized.get("source_updated_at"),
                "update_type": "replace" if current else "insert",
                "supersedes_assertion_id": current[0] if current else None,
                "expires_at": _trial_assertion_expiry(field_path, value),
            },
        )


def _trial_assertion_expiry(field_path: str, value) -> datetime:
    if field_path == "status_normalized":
        terminal = {"COMPLETED", "TERMINATED", "WITHDRAWN", "SUSPENDED", "UNKNOWN"}
        days = 180 if str(value).upper() in terminal else 14
    elif field_path == "phase_normalized":
        days = 90
    else:
        days = 30
    return datetime.now(UTC) + timedelta(days=days)


async def _insert_trial(db, data: dict) -> str:
    fields = list(data.keys())
    placeholders = [f"CAST(:{f} AS jsonb)" if f in TRIAL_JSONB_FIELDS else f":{f}" for f in fields]
    values = {}
    for k, v in data.items():
        if k in TRIAL_JSONB_FIELDS:
            values[k] = json.dumps(v)
        else:
            values[k] = v

    trial_id = str(uuid.uuid4())
    await db.execute(
        text(
            f"INSERT INTO clinical_trials (id, {', '.join(fields)}, created_at, updated_at) "
            f"VALUES (:__id, {', '.join(placeholders)}, now(), now())"
        ),
        {"__id": trial_id, **values},
    )
    return trial_id


async def _update_trial(db, trial_id: str, data: dict) -> None:
    set_clauses = [
        f"{k} = CAST(:{k} AS jsonb)" if k in TRIAL_JSONB_FIELDS else f"{k} = :{k}" for k in data
    ]
    values = {}
    for k, v in data.items():
        if k in TRIAL_JSONB_FIELDS:
            values[k] = json.dumps(v)
        else:
            values[k] = v

    await db.execute(
        text(
            f"UPDATE clinical_trials SET {', '.join(set_clauses)}, updated_at = now() "
            f"WHERE id = :__id"
        ),
        {"__id": trial_id, **values},
    )
