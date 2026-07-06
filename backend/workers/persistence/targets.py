"""Persistence logic for Open Targets biological-target records."""

import json
import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy import text

from workers.base.connector import ConnectorResult
from workers.base.staging import validate_target_record
from workers.persistence.common import _get_data_source_id
from workers.persistence.evidence import _insert_target_evidence_snippet
from workers.storage.raw_payload import store_raw_payload

logger = structlog.get_logger(__name__)

TARGET_JSONB_FIELDS = {"external_ids", "ingestion_metadata"}


async def _resolve_indication_ids(db, names: list[str]) -> list[str]:
    if not names:
        return []
    unique = list(dict.fromkeys(n for n in names if n))
    if not unique:
        return []
    placeholders = ", ".join(f":name_{i}" for i in range(len(unique)))
    lowered_placeholders = ", ".join(f"lower(:name_{i})" for i in range(len(unique)))
    params = {f"name_{i}": name for i, name in enumerate(unique)}
    rows = (
        await db.execute(
            text(f"""
                SELECT id::text FROM indications
                WHERE lower(preferred_name) IN ({lowered_placeholders})
                   OR EXISTS (
                       SELECT 1 FROM unnest(aliases) a
                       WHERE lower(a) IN ({placeholders})
                   )
            """),
            params,
        )
    ).fetchall()
    return [str(r[0]) for r in rows]


async def _persist_targets(db, result: ConnectorResult, normalizer, source_slug: str) -> None:
    source_id = await _get_data_source_id(db, source_slug)
    systemic_failures = 0

    payloads = result.raw_payloads

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
                quality = validate_target_record(normalized)
                if not quality.accepted:
                    raise ValueError(f"quality_gate_failed:{','.join(quality.errors)}")

                indication_names = normalized.pop("associated_indication_names", [])
                normalized["associated_indication_ids"] = await _resolve_indication_ids(
                    db, indication_names
                )

                source_document_id = await _upsert_target_source_document(
                    db=db,
                    source_id=source_id,
                    source_slug=source_slug,
                    parsed=parsed,
                    normalized=normalized,
                    raw_hash=raw_hash,
                    raw=raw,
                )
                normalized["ingestion_metadata"] = {
                    "source": source_slug,
                    "ingested_at": datetime.now(UTC).isoformat(),
                    "source_document_id": source_document_id,
                    "raw_payload_hash": raw_hash,
                }

                existing = (
                    await db.execute(
                        text("""
                            SELECT id::text, aliases, associated_indication_ids,
                                   ingestion_metadata->>'raw_payload_hash'
                            FROM targets
                            WHERE lower(symbol) = lower(:symbol)
                            LIMIT 1
                        """),
                        {"symbol": normalized["symbol"]},
                    )
                ).fetchone()

                if existing:
                    target_id = str(existing[0])
                    if existing[3] == raw_hash:
                        operation = "skipped"
                    else:
                        merged_aliases = sorted(
                            {*(existing[1] or []), *(normalized.get("aliases") or [])}
                        )
                        merged_indications = sorted(
                            {
                                *(existing[2] or []),
                                *(normalized.get("associated_indication_ids") or []),
                            }
                        )
                        normalized["aliases"] = merged_aliases
                        normalized["associated_indication_ids"] = merged_indications
                        await _update_target(db, target_id, normalized)
                        operation = "updated"
                else:
                    target_id = await _insert_target(db, normalized)
                    operation = "inserted"

                if operation != "skipped":
                    await _insert_target_evidence_snippet(
                        db=db,
                        source_document_id=source_document_id,
                        target_id=target_id,
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
                    {"symbol": getattr(parsed, "symbol", None), "error_type": type(e).__name__}
                )
            logger.error("target_persist_error", source=source_slug, error=str(e))

    if payloads and systemic_failures == len(payloads):
        raise RuntimeError("All parsed target records failed during persistence")
    await db.commit()


async def _upsert_target_source_document(
    *,
    db,
    source_id: str | None,
    source_slug: str,
    parsed,
    normalized: dict,
    raw_hash: str,
    raw: dict | None,
) -> str:
    external_id = str(getattr(parsed, "external_id", "") or normalized.get("symbol", ""))
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
                external_record_id, retrieved_at,
                raw_storage_path, license_status, metadata,
                created_at, updated_at
            )
            VALUES (
                :id, :data_source_id, :source_type, :title, :url, :content_hash,
                :external_record_id, now(),
                :raw_storage_path, :license_status,
                CAST(:metadata AS jsonb), now(), now()
            )
        """),
        {
            "id": source_document_id,
            "data_source_id": source_id,
            "source_type": "genomics_reference",
            "title": normalized.get("name") or normalized.get("symbol"),
            "url": f"https://platform.opentargets.org/target/{external_id}",
            "content_hash": raw_hash,
            "external_record_id": external_id,
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


async def _insert_target(db, data: dict) -> str:
    fields = [
        "symbol",
        "name",
        "aliases",
        "organism",
        "target_type",
        "external_ids",
        "open_targets_score",
        "associated_indication_ids",
        "ingestion_metadata",
    ]
    filtered = {k: v for k, v in data.items() if k in fields}
    placeholders = []
    values: dict = {}
    for k, v in filtered.items():
        if k in TARGET_JSONB_FIELDS:
            placeholders.append(f"CAST(:{k} AS jsonb)")
            values[k] = json.dumps(v)
        else:
            placeholders.append(f":{k}")
            values[k] = v
    target_id = str(uuid.uuid4())
    await db.execute(
        text(
            f"INSERT INTO targets (id, {', '.join(filtered.keys())}, created_at, updated_at) "
            f"VALUES (:__id, {', '.join(placeholders)}, now(), now())"
        ),
        {"__id": target_id, **values},
    )
    return target_id


async def _update_target(db, target_id: str, data: dict) -> None:
    fields = [
        "name",
        "aliases",
        "organism",
        "target_type",
        "external_ids",
        "open_targets_score",
        "associated_indication_ids",
        "ingestion_metadata",
    ]
    filtered = {k: v for k, v in data.items() if k in fields}
    set_clauses = []
    values: dict = {}
    for k, v in filtered.items():
        if k in TARGET_JSONB_FIELDS:
            set_clauses.append(f"{k} = CAST(:{k} AS jsonb)")
            values[k] = json.dumps(v)
        else:
            set_clauses.append(f"{k} = :{k}")
            values[k] = v
    await db.execute(
        text(f"UPDATE targets SET {', '.join(set_clauses)}, updated_at = now() WHERE id = :__id"),
        {"__id": target_id, **values},
    )
