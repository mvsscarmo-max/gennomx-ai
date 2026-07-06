"""Service layer for ClinicalTrial queries."""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError


class TrialService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_trials(
        self,
        q: str | None = None,
        nct_id: str | None = None,
        phase: str | None = None,
        status: str | None = None,
        sponsor: str | None = None,
        indication: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        filters = ["ct.is_current = true"]
        params: dict = {"offset": (page - 1) * page_size, "limit": page_size}

        if nct_id:
            filters.append("ct.nct_id = :nct_id")
            params["nct_id"] = nct_id.upper()
        if q:
            filters.append("(ct.brief_title ILIKE :q OR ct.official_title ILIKE :q)")
            params["q"] = f"%{q}%"
        if phase:
            filters.append("ct.phase_normalized = :phase")
            params["phase"] = phase.upper()
        if status:
            filters.append("ct.status_normalized = :status")
            params["status"] = status.upper()
        if sponsor:
            filters.append("ct.sponsor_name ILIKE :sponsor")
            params["sponsor"] = f"%{sponsor}%"
        if indication:
            filters.append("ct.conditions @> ARRAY[:indication]::text[]")
            params["indication"] = indication

        where = f"WHERE {' AND '.join(filters)}" if filters else ""

        count = (
            await self.db.execute(text(f"SELECT COUNT(*) FROM clinical_trials ct {where}"), params)
        ).scalar() or 0

        rows = (
            await self.db.execute(
                text(f"""
                SELECT id::text, nct_id, brief_title, phase, phase_normalized,
                       status, status_normalized, sponsor_name, conditions,
                       enrollment, start_date, primary_completion_date, countries, updated_at,
                       source_updated_at, lifecycle_status
                FROM clinical_trials ct
                {where}
                ORDER BY start_date DESC NULLS LAST
                LIMIT :limit OFFSET :offset
            """),
                params,
            )
        ).fetchall()

        items = [
            {
                "id": r[0],
                "nct_id": r[1],
                "title": r[2],
                "phase": r[3],
                "phase_normalized": r[4],
                "status": r[5],
                "status_normalized": r[6],
                "sponsor": r[7],
                "conditions": r[8] or [],
                "enrollment": r[9],
                "start_date": str(r[10]) if r[10] else None,
                "primary_completion_date": str(r[11]) if r[11] else None,
                "countries": r[12] or [],
                "updated_at": r[13].isoformat() if r[13] else None,
                "source_updated_at": r[14].isoformat() if r[14] else None,
                "freshness_status": ("revalidation_required" if r[15] == "stale" else "current"),
            }
            for r in rows
        ]
        return items, count

    async def get_trial_detail(self, trial_id: UUID) -> dict:
        row = (
            await self.db.execute(
                text(
                    "SELECT id::text, nct_id, brief_title, official_title, phase_normalized, "
                    "status_normalized, sponsor_name, collaborators, conditions, interventions, "
                    "arms, enrollment, start_date, primary_completion_date, completion_date, "
                    "countries, eligibility_criteria, registry_source, updated_at, "
                    "source_updated_at, lifecycle_status "
                    "FROM clinical_trials WHERE id = :id::uuid AND is_current = true"
                ),
                {"id": str(trial_id)},
            )
        ).fetchone()

        if not row:
            raise NotFoundError("ClinicalTrial", str(trial_id))

        return {
            "id": row[0],
            "nct_id": row[1],
            "brief_title": row[2],
            "official_title": row[3],
            "phase": row[4],
            "status": row[5],
            "sponsor": row[6],
            "collaborators": row[7] or [],
            "conditions": row[8] or [],
            "interventions": row[9] or [],
            "arms": row[10] or [],
            "enrollment": row[11],
            "start_date": str(row[12]) if row[12] else None,
            "primary_completion_date": str(row[13]) if row[13] else None,
            "completion_date": str(row[14]) if row[14] else None,
            "countries": row[15] or [],
            "eligibility_criteria": row[16],
            "registry_source": row[17],
            "updated_at": row[18].isoformat() if row[18] else None,
            "source_updated_at": row[19].isoformat() if row[19] else None,
            "freshness_status": ("revalidation_required" if row[20] == "stale" else "current"),
        }
