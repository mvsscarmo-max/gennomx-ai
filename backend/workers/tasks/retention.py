"""Auditable archive and retention jobs with legal-hold protection."""

import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import text

from workers.base.async_runner import run_coroutine
from workers.celery_app import celery_app
from workers.storage.raw_payload import store_raw_payload

RESOURCE_TABLES = {
    "field_assertions": "field_assertions",
    "source_documents": "source_documents",
    "ingestion_jobs": "ingestion_jobs",
    "mcp_query_logs": "mcp_query_logs",
    "security_events": "security_events",
}


async def _archive_resource(db, policy: dict, *, dry_run: bool, batch_size: int) -> dict:
    resource_type = policy["resource_type"]
    table = RESOURCE_TABLES[resource_type]
    now = datetime.now(UTC)
    archive_before = now - timedelta(days=policy["archive_after_days"])
    rows = (
        (
            await db.execute(
                text(f"""
                SELECT t.id::text AS id, row_to_json(t)::text AS payload
                FROM {table} t
                WHERE t.created_at < :archive_before
                  AND NOT EXISTS (
                    SELECT 1 FROM archive_items ai
                    WHERE ai.resource_type = :resource_type
                      AND ai.resource_id = t.id::text
                  )
                  AND NOT EXISTS (
                    SELECT 1 FROM legal_holds h
                    WHERE h.resource_type = :resource_type
                      AND (h.resource_id IS NULL OR h.resource_id = t.id::text)
                      AND h.released_at IS NULL
                      AND (h.expires_at IS NULL OR h.expires_at > now())
                  )
                ORDER BY t.created_at
                LIMIT :batch_size
            """),
                {
                    "archive_before": archive_before,
                    "resource_type": resource_type,
                    "batch_size": batch_size,
                },
            )
        )
        .mappings()
        .all()
    )
    manifest_id = str(uuid.uuid4())
    payload = {"resource_type": resource_type, "records": [json.loads(r["payload"]) for r in rows]}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    checksum = hashlib.sha256(canonical.encode()).hexdigest()
    storage_uri = None
    status = "dry_run" if dry_run else "running"
    await db.execute(
        text("""
            INSERT INTO archive_manifests (
                id, resource_type, window_end, record_count, content_checksum,
                status, dry_run, policy_version, created_at, updated_at
            ) VALUES (
                :id, :resource_type, :window_end, :record_count, :checksum,
                :status, :dry_run, :policy_version, now(), now()
            )
        """),
        {
            "id": manifest_id,
            "resource_type": resource_type,
            "window_end": archive_before,
            "record_count": len(rows),
            "checksum": checksum,
            "status": status,
            "dry_run": dry_run,
            "policy_version": policy["policy_version"],
        },
    )
    if not dry_run and rows:
        try:
            stored = await store_raw_payload(
                source_slug=f"archive_{resource_type}",
                external_id=manifest_id,
                payload=payload,
                content_hash=checksum,
            )
            storage_uri = stored.path
            for row in rows:
                await db.execute(
                    text("""
                        INSERT INTO archive_items (
                            id, manifest_id, resource_type, resource_id, archived_at
                        ) VALUES (:id, :manifest_id, :resource_type, :resource_id, now())
                        ON CONFLICT (resource_type, resource_id) DO NOTHING
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "manifest_id": manifest_id,
                        "resource_type": resource_type,
                        "resource_id": row["id"],
                    },
                )
            status = "completed"
        except Exception as exc:
            await db.execute(
                text("""
                    UPDATE archive_manifests
                    SET status = 'failed', error_detail = CAST(:detail AS JSONB),
                        completed_at = now(), updated_at = now()
                    WHERE id = :id
                """),
                {"id": manifest_id, "detail": json.dumps({"type": type(exc).__name__})},
            )
            raise
    elif not dry_run:
        status = "completed"
    await db.execute(
        text("""
            UPDATE archive_manifests
            SET status = :status, storage_uri = :storage_uri,
                completed_at = now(), updated_at = now()
            WHERE id = :id
        """),
        {"id": manifest_id, "status": status, "storage_uri": storage_uri},
    )
    return {"resource_type": resource_type, "manifest_id": manifest_id, "records": len(rows)}


async def _delete_expired_archived(db, policy: dict, *, batch_size: int) -> int:
    if policy["delete_after_days"] is None:
        return 0
    resource_type = policy["resource_type"]
    table = RESOURCE_TABLES[resource_type]
    cutoff = datetime.now(UTC) - timedelta(days=policy["delete_after_days"])
    deleted = (
        await db.execute(
            text(f"""
                DELETE FROM {table} t
                USING archive_items ai
                WHERE ai.resource_type = :resource_type
                  AND ai.resource_id = t.id::text
                  AND ai.deleted_at IS NULL
                  AND t.created_at < :cutoff
                  AND NOT EXISTS (
                    SELECT 1 FROM legal_holds h
                    WHERE h.resource_type = :resource_type
                      AND (h.resource_id IS NULL OR h.resource_id = t.id::text)
                      AND h.released_at IS NULL
                      AND (h.expires_at IS NULL OR h.expires_at > now())
                  )
                  AND ai.id IN (
                    SELECT id FROM archive_items
                    WHERE resource_type = :resource_type AND deleted_at IS NULL
                    ORDER BY archived_at LIMIT :batch_size
                  )
                RETURNING ai.id
            """),
            {
                "resource_type": resource_type,
                "cutoff": cutoff,
                "batch_size": batch_size,
            },
        )
    ).fetchall()
    for row in deleted:
        await db.execute(
            text("UPDATE archive_items SET deleted_at = now() WHERE id = :id"),
            {"id": row[0]},
        )
    return len(deleted)


@celery_app.task(name="workers.tasks.retention.run_retention_cycle", queue="process")
def run_retention_cycle(*, dry_run: bool = True, batch_size: int = 1000) -> dict:
    if not 1 <= batch_size <= 10_000:
        raise ValueError("batch_size must be between 1 and 10000")
    from workers.tasks.ingest import _get_async_session

    async def _run() -> dict:
        async_session = _get_async_session()
        async with async_session() as db:
            policies = (
                (
                    await db.execute(
                        text("""
                        SELECT resource_type, archive_after_days, delete_after_days,
                               policy_version
                        FROM retention_policies
                        WHERE active = true AND archive_after_days IS NOT NULL
                    """)
                    )
                )
                .mappings()
                .all()
            )
            manifests = []
            deleted = 0
            for policy in policies:
                if policy["resource_type"] not in RESOURCE_TABLES:
                    continue
                manifests.append(
                    await _archive_resource(db, policy, dry_run=dry_run, batch_size=batch_size)
                )
                if not dry_run:
                    deleted += await _delete_expired_archived(db, policy, batch_size=batch_size)
            await db.commit()
            return {
                "status": "success",
                "dry_run": dry_run,
                "manifests": manifests,
                "deleted": deleted,
            }

    return run_coroutine(_run())
