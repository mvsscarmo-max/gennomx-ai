"""Persistence logic shared by regulatory-approval connectors (openFDA, DailyMed, EMA)."""

import json
import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy import text

from app.services.persistence_decision import (
    AssertionCandidate,
    CurrentAssertion,
    PersistenceAction,
)
from workers.base.connector import ConnectorResult
from workers.base.staging import stage_and_deduplicate, validate_regulatory_record
from workers.persistence.common import (
    DECISION_ENGINE,
    _get_data_source_id,
    _record_data_conflict,
)
from workers.persistence.evidence import _insert_regulatory_evidence_snippet
from workers.storage.raw_payload import store_raw_payload

logger = structlog.get_logger(__name__)

REGULATORY_JSONB_FIELDS = {"special_designations", "raw_data", "ingestion_metadata"}


async def _resolve_drug_asset_id(
    db, asset_name: str, aliases: list[str] | None = None
) -> str | None:
    """Match a regulatory record to an existing canonical drug asset by name/alias."""
    candidates = [asset_name, *(aliases or [])]
    for candidate in candidates:
        if not candidate:
            continue
        row = (
            await db.execute(
                text("""
                    SELECT id::text FROM drug_assets
                    WHERE lower(primary_name) = lower(:name)
                       OR lower(:name) = ANY(SELECT lower(a) FROM unnest(aliases) AS a)
                    LIMIT 1
                """),
                {"name": candidate},
            )
        ).fetchone()
        if row:
            return str(row[0])
    return None


async def _persist_regulatory_approvals(
    db, result: ConnectorResult, normalizer, source_slug: str
) -> None:
    source_id = await _get_data_source_id(db, source_slug)
    systemic_failures = 0

    payloads = _stage_regulatory_payloads(result.raw_payloads)
    result.records_skipped += len(result.raw_payloads) - len(payloads)

    for payload in payloads:
        parsed = payload.get("parsed")
        raw_hash = payload.get("hash")
        raw = payload.get("raw")

        if not parsed or not raw_hash:
            result.records_rejected += 1
            continue

        try:
            async with db.begin_nested():
                normalized = normalizer.normalize(parsed)
                quality = validate_regulatory_record(normalized)
                if not quality.accepted:
                    raise ValueError(f"quality_gate_failed:{','.join(quality.errors)}")

                drug_asset_id = await _resolve_drug_asset_id(
                    db, normalized["asset_name"], normalized.get("asset_aliases")
                )
                if not drug_asset_id:
                    result.records_skipped += 1
                    continue

                source_document_id = await _upsert_regulatory_source_document(
                    db=db,
                    source_id=source_id,
                    source_slug=source_slug,
                    parsed=parsed,
                    normalized=normalized,
                    raw_hash=raw_hash,
                    raw=raw,
                )
                normalized["drug_asset_id"] = drug_asset_id
                normalized["regulatory_document_id"] = source_document_id
                normalized["ingestion_metadata"] = {
                    "source": source_slug,
                    "ingested_at": datetime.now(UTC).isoformat(),
                    "source_document_id": source_document_id,
                    "raw_payload_hash": raw_hash,
                }
                normalized["lifecycle_status"] = "active"
                normalized["is_current"] = True
                normalized["valid_from"] = normalized.get("source_updated_at") or datetime.now(UTC)
                normalized["system_from"] = datetime.now(UTC)

                existing = (
                    await db.execute(
                        text("""
                            SELECT id::text,
                                   ingestion_metadata->>'raw_payload_hash',
                                   ingestion_metadata->>'source_updated_at'
                            FROM regulatory_approvals
                            WHERE drug_asset_id = :drug_asset_id
                              AND COALESCE(agency, '') = COALESCE(:agency, '')
                              AND COALESCE(region, '') = COALESCE(:region, '')
                              AND COALESCE(application_number, '')
                                  = COALESCE(:application_number, '')
                              AND is_current = true
                        """),
                        {
                            "drug_asset_id": drug_asset_id,
                            "agency": normalized.get("agency"),
                            "region": normalized.get("region"),
                            "application_number": normalized.get("application_number"),
                        },
                    )
                ).fetchone()

                if existing:
                    approval_id = str(existing[0])
                    current_source_updated_at = (
                        datetime.fromisoformat(str(existing[2])) if existing[2] else None
                    )
                    decision = DECISION_ENGINE.decide(
                        AssertionCandidate(
                            value=normalized,
                            value_hash=raw_hash,
                            source_updated_at=normalized.get("source_updated_at"),
                            authority_score=1.0,
                            confidence_score=0.95,
                            evidence_present=bool(raw),
                        ),
                        CurrentAssertion(
                            value=None,
                            value_hash=existing[1] or "",
                            source_updated_at=current_source_updated_at,
                            authority_score=1.0,
                        ),
                    )
                    if decision.action in {PersistenceAction.NOOP, PersistenceAction.ARCHIVE}:
                        operation = "skipped"
                    elif decision.action in {
                        PersistenceAction.CONFLICT,
                        PersistenceAction.QUARANTINE,
                    }:
                        await _record_data_conflict(
                            db, approval_id, "record", decision.reason_code, "regulatory_approval"
                        )
                        operation = "skipped"
                    else:
                        operation = "updated"
                else:
                    approval_id = ""
                    operation = "inserted"

                if operation == "updated":
                    await _update_regulatory_approval(db, approval_id, normalized)
                elif operation == "inserted":
                    approval_id = await _insert_regulatory_approval(db, normalized)

                if operation != "skipped":
                    await _insert_regulatory_evidence_snippet(
                        db=db,
                        source_document_id=source_document_id,
                        approval_id=approval_id,
                        fragment=raw or normalized,
                    )

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
                errors.append(
                    {
                        "asset_name": getattr(parsed, "asset_name", None),
                        "error_type": type(e).__name__,
                    }
                )
            logger.error(
                "regulatory_persist_error",
                source=source_slug,
                error=str(e),
            )

    if payloads and systemic_failures == len(payloads):
        raise RuntimeError("All parsed regulatory records failed during persistence")
    await db.commit()


def _stage_regulatory_payloads(payloads: list[dict]) -> list[dict]:
    indexed: list[dict] = []
    invalid: list[dict] = []
    keys: list[str] = []
    for index, payload in enumerate(payloads):
        parsed = payload.get("parsed")
        external_id = getattr(parsed, "external_id", None) if parsed else None
        if not external_id:
            invalid.append(payload)
            continue
        keys.append(str(external_id))
        indexed.append(
            {
                "external_id": str(external_id),
                "updated_at": getattr(parsed, "source_updated_at", None),
                "payload_index": index,
            }
        )
    if len(set(keys)) == len(keys):
        return payloads
    selected = stage_and_deduplicate(indexed, "external_id", "updated_at")
    return [payloads[int(item["payload_index"])] for item in selected] + invalid


async def _upsert_regulatory_source_document(
    *,
    db,
    source_id: str | None,
    source_slug: str,
    parsed,
    normalized: dict,
    raw_hash: str,
    raw: dict | None,
) -> str:
    external_id = str(getattr(parsed, "external_id", "") or "")
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
                "external_record_id": external_id,
            },
        )
    ).fetchone()
    if existing and existing[1]:
        return str(existing[0])

    if not raw:
        raise ValueError("Raw payload is required for source-document traceability")
    stored = await store_raw_payload(
        source_slug=source_slug,
        external_id=external_id,
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
            "source_type": "regulatory_filing",
            "title": normalized.get("asset_name") or external_id,
            "url": normalized.get("label_url"),
            "content_hash": raw_hash,
            "external_record_id": external_id,
            "source_updated_at": normalized.get("source_updated_at"),
            "license_status": "open",
            "raw_storage_path": stored.path,
            "metadata": json.dumps(
                {
                    "source": source_slug,
                    "external_id": external_id,
                    "raw_format": "json+gzip",
                    "connector_version": f"{source_slug}_v1",
                    "raw_byte_count_gzip": stored.byte_count,
                }
            ),
        },
    )
    return source_document_id


async def _insert_regulatory_approval(db, data: dict) -> str:
    fields = [
        "drug_asset_id",
        "indication_id",
        "indication_name",
        "region",
        "agency",
        "approval_status",
        "approval_date",
        "submission_date",
        "pathway",
        "special_designations",
        "label_url",
        "regulatory_document_id",
        "application_number",
        "raw_data",
        "ingestion_metadata",
        "valid_from",
        "system_from",
        "is_current",
        "lifecycle_status",
    ]
    filtered = {k: v for k, v in data.items() if k in fields}
    placeholders = []
    values: dict = {}
    for k, v in filtered.items():
        if k in REGULATORY_JSONB_FIELDS:
            placeholders.append(f"CAST(:{k} AS jsonb)")
            values[k] = json.dumps(v)
        else:
            placeholders.append(f":{k}")
            values[k] = v
    approval_id = str(uuid.uuid4())
    await db.execute(
        text(
            f"INSERT INTO regulatory_approvals (id, {', '.join(filtered.keys())}, "
            f"created_at, updated_at) "
            f"VALUES (:__id, {', '.join(placeholders)}, now(), now())"
        ),
        {"__id": approval_id, **values},
    )
    return approval_id


async def _update_regulatory_approval(db, approval_id: str, data: dict) -> None:
    fields = [
        "approval_status",
        "approval_date",
        "submission_date",
        "pathway",
        "special_designations",
        "label_url",
        "regulatory_document_id",
        "raw_data",
        "ingestion_metadata",
        "lifecycle_status",
    ]
    filtered = {k: v for k, v in data.items() if k in fields}
    set_clauses = []
    values: dict = {}
    for k, v in filtered.items():
        if k in REGULATORY_JSONB_FIELDS:
            set_clauses.append(f"{k} = CAST(:{k} AS jsonb)")
            values[k] = json.dumps(v)
        else:
            set_clauses.append(f"{k} = :{k}")
            values[k] = v
    await db.execute(
        text(
            f"UPDATE regulatory_approvals SET {', '.join(set_clauses)}, updated_at = now() "
            f"WHERE id = :__id"
        ),
        {"__id": approval_id, **values},
    )
