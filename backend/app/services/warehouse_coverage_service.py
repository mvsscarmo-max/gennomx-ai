"""Read-only operational coverage and traceability metrics for the warehouse."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class WarehouseCoverageService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_coverage(self) -> dict:
        entities = (
            await self.db.execute(
                text("""
                    SELECT
                        (SELECT COUNT(*) FROM drug_assets) AS assets,
                        (SELECT COUNT(*) FROM clinical_trials) AS trials,
                        (SELECT COUNT(*) FROM publications) AS publications,
                        (SELECT COUNT(*) FROM targets) AS targets,
                        (SELECT COUNT(*) FROM regulatory_approvals) AS regulatory_approvals,
                        (SELECT COUNT(*) FROM endpoints) AS endpoints,
                        (SELECT COUNT(*) FROM trial_results) AS trial_results,
                        (SELECT COUNT(*) FROM adverse_events) AS adverse_events
                """)
            )
        ).fetchone()
        traceability = (
            await self.db.execute(
                text("""
                    SELECT
                        (SELECT COUNT(*) FROM source_documents) AS source_documents,
                        (SELECT COUNT(*) FROM evidence_snippets) AS evidence_snippets,
                        (SELECT COUNT(*) FROM field_assertions) AS field_assertions,
                        (SELECT COUNT(*) FROM data_conflicts
                         WHERE status = 'open') AS open_conflicts,
                        (SELECT COUNT(*) FROM mcp_query_logs
                         WHERE created_at >= now() - interval '24 hours') AS mcp_queries_24h
                """)
            )
        ).fetchone()
        source_rows = (
            await self.db.execute(
                text("""
                    SELECT slug, is_enabled, connector_status, last_successful_run, last_failed_run
                    FROM data_sources
                    ORDER BY slug
                """)
            )
        ).fetchall()
        job_rows = (
            await self.db.execute(
                text("""
                    SELECT data_source_slug, status, COUNT(*)
                    FROM ingestion_jobs
                    GROUP BY data_source_slug, status
                    ORDER BY data_source_slug, status
                """)
            )
        ).fetchall()
        assert entities is not None
        assert traceability is not None

        return {
            "entities": {
                "assets": entities[0],
                "trials": entities[1],
                "publications": entities[2],
                "targets": entities[3],
                "regulatory_approvals": entities[4],
                "endpoints": entities[5],
                "trial_results": entities[6],
                "adverse_events": entities[7],
            },
            "traceability": {
                "source_documents": traceability[0],
                "evidence_snippets": traceability[1],
                "field_assertions": traceability[2],
                "open_conflicts": traceability[3],
                "mcp_queries_24h": traceability[4],
            },
            "sources": [
                {
                    "slug": row[0],
                    "is_enabled": row[1],
                    "connector_status": row[2],
                    "last_successful_run": row[3].isoformat() if row[3] else None,
                    "last_failed_run": row[4].isoformat() if row[4] else None,
                }
                for row in source_rows
            ],
            "jobs": [
                {"source_slug": row[0], "status": row[1], "count": row[2]} for row in job_rows
            ],
            "limitations": [
                "Entity counts measure ingested inventory, not global market coverage.",
                "Traceability counts are not a percentage until entity-level denominators exist.",
                "Sources without a successful run have no demonstrated coverage.",
                (
                    "Clinical result, adverse-event, company, and indication coverage remain "
                    "incomplete."
                ),
            ],
        }
