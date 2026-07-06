"""Service layer for the dashboard overview aggregate."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class OverviewService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_stats(self) -> dict:
        row = (
            await self.db.execute(
                text("""
                    SELECT
                        (SELECT COUNT(*) FROM drug_assets) AS total_assets,
                        (SELECT COUNT(*) FROM companies) AS total_companies,
                        (SELECT COUNT(*) FROM clinical_trials WHERE is_current = true)
                            AS total_trials,
                        (SELECT COUNT(*) FROM data_sources
                            WHERE is_enabled = true AND connector_status = 'active')
                            AS active_sources,
                        (SELECT MAX(last_successful_run) FROM data_sources) AS last_ingest
                """)
            )
        ).fetchone()

        if row is None:
            return {
                "total_assets": 0,
                "total_companies": 0,
                "total_trials": 0,
                "active_sources": 0,
                "last_ingest": None,
            }

        return {
            "total_assets": row[0] or 0,
            "total_companies": row[1] or 0,
            "total_trials": row[2] or 0,
            "active_sources": row[3] or 0,
            "last_ingest": row[4].isoformat() if row[4] else None,
        }
