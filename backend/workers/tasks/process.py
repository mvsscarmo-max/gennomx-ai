"""Post-ingestion processing tasks: deduplication, normalization, linking."""

import logging
import uuid

from sqlalchemy import text

from workers.base.async_runner import run_coroutine
from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="workers.tasks.process.mark_stale_assertions",
    queue="process",
)
def mark_stale_assertions() -> dict:
    """Mark expired current assertions and their trial projection for revalidation."""
    from workers.tasks.ingest import _get_async_session

    async def _run():
        async_session = _get_async_session()
        async with async_session() as db:
            assertions = await db.execute(
                text("""
                    UPDATE field_assertions
                    SET lifecycle_status = 'stale',
                        validation_status = 'revalidation_required', updated_at = now()
                    WHERE is_current = true AND lifecycle_status = 'active'
                      AND expires_at IS NOT NULL AND expires_at <= now()
                    RETURNING entity_type, entity_id, field_path
                """)
            )
            stale_assertions = assertions.fetchall()
            trials = await db.execute(
                text("""
                    UPDATE clinical_trials ct
                    SET lifecycle_status = 'stale', updated_at = now()
                    WHERE ct.is_current = true AND ct.lifecycle_status = 'active'
                      AND EXISTS (
                        SELECT 1 FROM field_assertions fa
                        WHERE fa.entity_type = 'clinical_trial'
                          AND fa.entity_id = ct.id
                          AND fa.field_path = 'status_normalized'
                          AND fa.is_current = true AND fa.lifecycle_status = 'stale'
                      )
                    RETURNING ct.id
                """)
            )
            stale_trials = len(trials.fetchall())
            await db.commit()
            return {
                "status": "success",
                "stale_assertions": len(stale_assertions),
                "stale_trials": stale_trials,
            }

    return run_coroutine(_run())


@celery_app.task(
    name="workers.tasks.process.deduplicate_assets",
    queue="process",
    bind=True,
    max_retries=2,
)
def deduplicate_assets(self) -> dict:
    """Register exact-identity duplicate candidates without an unsafe automatic merge."""
    logger.info("deduplicate_assets: starting")
    from workers.tasks.ingest import _get_async_session

    async def _run():
        async_session = _get_async_session()
        async with async_session() as db:
            rows = (
                await db.execute(
                    text("""
                        SELECT a.id::text, b.id::text
                        FROM drug_assets a
                        JOIN drug_assets b ON a.id < b.id
                        WHERE (
                            a.inn IS NOT NULL AND b.inn IS NOT NULL
                            AND lower(a.inn) = lower(b.inn)
                        ) OR (
                            a.external_ids IS NOT NULL AND b.external_ids IS NOT NULL
                            AND a.external_ids <> '{}'::jsonb
                            AND a.external_ids @> b.external_ids
                            AND b.external_ids @> a.external_ids
                        )
                    """)
                )
            ).fetchall()
            created = 0
            for canonical_id, duplicate_id in rows:
                await db.execute(
                    text("""
                        INSERT INTO data_conflicts (
                            id, entity_type, entity_id, field_path, conflict_type,
                            severity, status, resolution_reason, created_at, updated_at
                        ) SELECT
                            :id, 'drug_asset', :entity_id, 'identity', 'duplicate_identity',
                            'high', 'open', :reason, now(), now()
                        WHERE NOT EXISTS (
                            SELECT 1 FROM data_conflicts
                            WHERE entity_type = 'drug_asset' AND entity_id = :entity_id
                              AND field_path = 'identity' AND conflict_type = 'duplicate_identity'
                              AND status = 'open'
                        )
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "entity_id": duplicate_id,
                        "reason": f"exact_identity_candidate:{canonical_id}",
                    },
                )
                created += 1
            await db.commit()
            return {"status": "success", "candidates": len(rows), "conflicts_considered": created}

    return run_coroutine(_run())


@celery_app.task(
    name="workers.tasks.process.link_trials_to_assets",
    queue="process",
    bind=True,
    max_retries=2,
)
def link_trials_to_assets(self) -> dict:
    """Link ClinicalTrial records to DrugAsset records by drug name matching."""
    logger.info("link_trials_to_assets: starting")
    from workers.tasks.ingest import _get_async_session, link_existing_trials_to_assets

    async def _run():
        async_session = _get_async_session()
        async with async_session() as db:
            return await link_existing_trials_to_assets(db)

    return run_coroutine(_run())


@celery_app.task(
    name="workers.tasks.process.compute_confidence_scores",
    queue="process",
    bind=True,
    max_retries=2,
)
def compute_confidence_scores(self) -> dict:
    """Recompute explainable confidence/completeness scores without an LLM."""
    logger.info("compute_confidence_scores: starting")
    from workers.tasks.ingest import _get_async_session

    async def _run():
        async_session = _get_async_session()
        async with async_session() as db:
            result = await db.execute(
                text("""
                    UPDATE drug_assets a
                    SET data_completeness_score = LEAST(1.0,
                            0.20
                          + CASE WHEN a.modality IS NOT NULL THEN 0.15 ELSE 0 END
                          + CASE WHEN a.inn IS NOT NULL THEN 0.15 ELSE 0 END
                          + CASE WHEN cardinality(a.indication_names) > 0 THEN 0.15 ELSE 0 END
                          + CASE WHEN cardinality(a.sponsor_names) > 0 THEN 0.10 ELSE 0 END
                          + CASE WHEN a.current_development_stage IS NOT NULL THEN 0.10 ELSE 0 END
                          + CASE WHEN a.external_ids IS NOT NULL AND a.external_ids <> '{}'::jsonb
                                 THEN 0.15 ELSE 0 END),
                        source_confidence = LEAST(1.0,
                            0.55
                          + CASE WHEN a.primary_source_id IS NOT NULL THEN 0.20 ELSE 0 END
                          + CASE WHEN EXISTS (
                                SELECT 1 FROM evidence_snippets e
                                WHERE e.entity_type = 'drug_asset' AND e.entity_id = a.id
                            ) THEN 0.20 ELSE 0 END
                          + CASE WHEN a.inn IS NOT NULL OR a.external_ids IS NOT NULL
                                 THEN 0.05 ELSE 0 END),
                        updated_at = now()
                    RETURNING id
                """)
            )
            updated = len(result.fetchall())
            await db.commit()
            return {"status": "success", "updated": updated, "rule_set_version": "2026-06-20.1"}

    return run_coroutine(_run())
