"""Persistence logic for PubMed publication records."""

import json
import uuid
from datetime import UTC, datetime, time

import structlog
from sqlalchemy import text

from app.services.persistence_decision import (
    AssertionCandidate,
    CurrentAssertion,
    PersistenceAction,
)
from workers.base.connector import ConnectorResult
from workers.base.staging import stage_and_deduplicate, validate_publication_record
from workers.persistence.common import (
    DECISION_ENGINE,
    _get_data_source_id,
    _record_data_conflict,
)
from workers.persistence.evidence import _insert_publication_evidence_snippet
from workers.storage.raw_payload import store_raw_payload

logger = structlog.get_logger(__name__)

PUBLICATION_JSONB_FIELDS = {"ingestion_metadata"}


async def _persist_publications(db, result: ConnectorResult, normalizer) -> None:
    source_id = await _get_data_source_id(db, "pubmed")
    systemic_failures = 0

    payloads = _stage_publication_payloads(result.raw_payloads)
    result.records_skipped += len(result.raw_payloads) - len(payloads)

    for payload in payloads:
        parsed = payload.get("parsed")
        raw_hash = payload["hash"]
        raw = payload["raw"]

        if not parsed or not parsed.pmid:
            result.records_rejected += 1
            continue

        try:
            async with db.begin_nested():
                normalized = normalizer.normalize(parsed)
                normalized["raw_payload_hash"] = raw_hash
                source_document_id = await _upsert_publication_source_document(
                    db=db, source_id=source_id, parsed=parsed, raw_hash=raw_hash, raw=raw
                )
                normalized["source_document_id"] = source_document_id
                normalized["ingestion_metadata"] = {
                    "source": "pubmed",
                    "ingested_at": datetime.now(UTC).isoformat(),
                    "source_document_id": source_document_id,
                    "source_updated_at": (
                        normalized["source_updated_at"].isoformat()
                        if normalized.get("source_updated_at")
                        else None
                    ),
                    "raw_payload_hash": raw_hash,
                }
                normalized["lifecycle_status"] = "active"
                normalized["is_current"] = True
                normalized["valid_from"] = normalized.get("source_updated_at") or datetime.now(UTC)
                normalized["system_from"] = datetime.now(UTC)
                quality = validate_publication_record(normalized)
                if not quality.accepted:
                    raise ValueError(f"quality_gate_failed:{','.join(quality.errors)}")

                existing = await db.execute(
                    text("""
                        SELECT id::text,
                               ingestion_metadata->>'source_updated_at',
                               ingestion_metadata->>'raw_payload_hash'
                        FROM publications WHERE pmid = :pmid
                    """),
                    {"pmid": parsed.pmid},
                )
                row = existing.fetchone()
                if row:
                    pub_id = str(row[0])
                    current_source_updated_at = (
                        datetime.fromisoformat(str(row[1])) if row[1] else None
                    )
                    candidate_source_updated_at = normalized.get("source_updated_at")
                    decision = DECISION_ENGINE.decide(
                        AssertionCandidate(
                            value=normalized,
                            value_hash=raw_hash,
                            source_updated_at=candidate_source_updated_at,
                            authority_score=1.0,
                            confidence_score=0.98,
                            evidence_present=bool(raw),
                        ),
                        CurrentAssertion(
                            value=None,
                            value_hash=row[2] or "",
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
                        await _record_data_conflict(db, pub_id, "record", decision.reason_code)
                        operation = "skipped"
                    else:
                        operation = "updated"
                else:
                    pub_id = ""
                    operation = "inserted"

                if operation != "skipped":
                    linked_trial_ids, unresolved_ncts = await _resolve_nct_links(
                        db, normalized.get("nct_ids", []) or []
                    )
                    normalized["linked_trial_ids"] = linked_trial_ids
                    if unresolved_ncts:
                        meta = dict(normalized.get("ingestion_metadata") or {})
                        meta["unresolved_nct_ids"] = unresolved_ncts
                        normalized["ingestion_metadata"] = meta
                    if operation == "updated":
                        await _update_publication(db, pub_id, normalized)
                    else:
                        pub_id = await _insert_publication(db, normalized)
                    await _insert_publication_evidence_snippet(
                        db=db,
                        source_document_id=source_document_id,
                        pub_id=pub_id,
                        parsed=parsed,
                        raw=raw,
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
                        "pmid": getattr(parsed, "pmid", None),
                        "error_type": type(e).__name__,
                    }
                )
            logger.error(
                "publication_persist_error",
                pmid=getattr(parsed, "pmid", None),
                error=str(e),
            )

    if payloads and systemic_failures == len(payloads):
        raise RuntimeError("All parsed publication records failed during persistence")
    await db.commit()


def _stage_publication_payloads(payloads: list[dict]) -> list[dict]:
    indexed: list[dict] = []
    invalid: list[dict] = []
    keys: list[str] = []
    for index, payload in enumerate(payloads):
        parsed = payload.get("parsed")
        if not parsed or not getattr(parsed, "pmid", None):
            invalid.append(payload)
            continue
        pmid = str(parsed.pmid)
        keys.append(pmid)
        indexed.append(
            {
                "pmid": pmid,
                "updated_at": getattr(parsed, "date_revised", None),
                "payload_index": index,
            }
        )
    if len(set(keys)) == len(keys):
        return payloads
    selected = stage_and_deduplicate(indexed, "pmid", "updated_at")
    return [payloads[int(item["payload_index"])] for item in selected] + invalid


async def _upsert_publication_source_document(
    *,
    db,
    source_id: str | None,
    parsed,
    raw_hash: str,
    raw: dict | None,
) -> str:
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
                "external_record_id": parsed.pmid,
            },
        )
    ).fetchone()
    if existing and existing[1]:
        return str(existing[0])

    if not raw:
        raise ValueError("Raw payload is required for source-document traceability")
    stored = await store_raw_payload(
        source_slug="pubmed",
        external_id=parsed.pmid,
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
    pub_url = f"https://pubmed.ncbi.nlm.nih.gov/{parsed.pmid}/"
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
            "source_type": "scientific_publication",
            "title": parsed.title or parsed.pmid,
            "url": pub_url,
            "content_hash": raw_hash,
            "external_record_id": parsed.pmid,
            "source_updated_at": (
                datetime.combine(parsed.date_revised, time.min, tzinfo=UTC)
                if getattr(parsed, "date_revised", None)
                else None
            ),
            "license_status": "open",
            "raw_storage_path": stored.path,
            "metadata": json.dumps(
                {
                    "source": "pubmed",
                    "pmid": parsed.pmid,
                    "raw_format": "xml+gzip",
                    "connector_version": "pubmed_eutils_v1",
                    "raw_byte_count_gzip": stored.byte_count,
                }
            ),
        },
    )
    return source_document_id


async def _resolve_nct_links(db, nct_ids: list[str]) -> tuple[list[str], list[str]]:
    if not nct_ids:
        return [], []
    unique = list(dict.fromkeys(nct_ids))
    placeholders = ", ".join(f":nct_{i}" for i in range(len(unique)))
    params = {f"nct_{i}": nct for i, nct in enumerate(unique)}
    rows = (
        await db.execute(
            text(f"""
                SELECT nct_id FROM clinical_trials
                WHERE nct_id IN ({placeholders})
            """),
            params,
        )
    ).fetchall()
    resolved = {str(r[0]) for r in rows}
    linked = [n for n in unique if n in resolved]
    unresolved = [n for n in unique if n not in resolved]
    return linked, unresolved


async def _insert_publication(db, data: dict) -> str:
    pub_fields = [
        "title",
        "journal",
        "publication_date",
        "publication_type",
        "doi",
        "pmid",
        "pmcid",
        "abstract",
        "authors",
        "keywords",
        "linked_trial_ids",
        "linked_asset_ids",
        "linked_indication_ids",
        "source_url",
        "open_access",
        "ingestion_metadata",
        "valid_from",
        "system_from",
        "is_current",
        "lifecycle_status",
    ]
    filtered = {k: v for k, v in data.items() if k in pub_fields}
    placeholders = []
    values: dict = {}
    for k, v in filtered.items():
        if k in PUBLICATION_JSONB_FIELDS:
            placeholders.append(f"CAST(:{k} AS jsonb)")
            values[k] = json.dumps(v)
        else:
            placeholders.append(f":{k}")
            values[k] = v
    pub_id = str(uuid.uuid4())
    await db.execute(
        text(
            f"INSERT INTO publications (id, {', '.join(filtered.keys())}, created_at, updated_at) "
            f"VALUES (:__id, {', '.join(placeholders)}, now(), now())"
        ),
        {"__id": pub_id, **values},
    )
    return pub_id


async def _update_publication(db, pub_id: str, data: dict) -> None:
    pub_fields = [
        "title",
        "journal",
        "publication_date",
        "publication_type",
        "doi",
        "pmid",
        "pmcid",
        "abstract",
        "authors",
        "keywords",
        "linked_trial_ids",
        "linked_asset_ids",
        "linked_indication_ids",
        "source_url",
        "open_access",
        "ingestion_metadata",
        "source_document_id",
        "lifecycle_status",
    ]
    filtered = {k: v for k, v in data.items() if k in pub_fields}
    set_clauses = []
    values: dict = {}
    for k, v in filtered.items():
        if k in PUBLICATION_JSONB_FIELDS:
            set_clauses.append(f"{k} = CAST(:{k} AS jsonb)")
            values[k] = json.dumps(v)
        else:
            set_clauses.append(f"{k} = :{k}")
            values[k] = v
    await db.execute(
        text(
            f"UPDATE publications SET {', '.join(set_clauses)}, updated_at = now() WHERE id = :__id"
        ),
        {"__id": pub_id, **values},
    )
