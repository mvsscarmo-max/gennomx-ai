"""Shared helpers used across persistence modules."""

from sqlalchemy import text

from app.config import get_settings
from app.db_url import coerce_database_url
from app.services.persistence_decision import PersistenceDecisionEngine
from workers.base.connector import ConnectorResult

settings = get_settings()
DECISION_ENGINE = PersistenceDecisionEngine()
FATAL_CONNECTOR_ERRORS = {"connector_error", "fetch_error"}


def _has_fatal_connector_error(result: ConnectorResult) -> bool:
    return any(error["type"] in FATAL_CONNECTOR_ERRORS for error in result.errors)


def _get_async_session():
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    engine = create_async_engine(
        coerce_database_url(settings.WORKER_DATABASE_URL, async_driver=True),
        pool_size=5,
    )
    return async_sessionmaker(engine, expire_on_commit=False)


async def _get_data_source_id(db, source_slug: str) -> str | None:
    row = (
        await db.execute(
            text("SELECT id::text FROM data_sources WHERE slug = :slug"),
            {"slug": source_slug},
        )
    ).fetchone()
    return str(row[0]) if row else None


async def _get_last_successful_run(db, source_slug: str):
    row = (
        await db.execute(
            text("SELECT last_successful_run FROM data_sources WHERE slug = :slug"),
            {"slug": source_slug},
        )
    ).fetchone()
    return row[0] if row and row[0] else None


async def _record_data_conflict(
    db, entity_id: str, field_path: str, reason: str, entity_type: str = "clinical_trial"
) -> None:
    import uuid

    await db.execute(
        text("""
            INSERT INTO data_conflicts (
                id, entity_type, entity_id, field_path, conflict_type,
                severity, status, created_at, updated_at
            ) VALUES (
                :id, :entity_type, :entity_id, :field_path, :reason,
                'medium', 'open', now(), now()
            )
        """),
        {
            "id": str(uuid.uuid4()),
            "entity_type": entity_type,
            "entity_id": entity_id,
            "field_path": field_path,
            "reason": reason,
        },
    )
