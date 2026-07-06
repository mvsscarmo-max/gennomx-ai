"""Service layer for Company queries."""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError


class CompanyService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_companies(
        self,
        q: str | None = None,
        company_type: str | None = None,
        country: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        filters = []
        params: dict = {"offset": (page - 1) * page_size, "limit": page_size}

        if q:
            filters.append("(c.legal_name ILIKE :q OR :q_exact = ANY(c.aliases))")
            params["q"] = f"%{q}%"
            params["q_exact"] = q
        if company_type:
            filters.append("c.company_type = :ct")
            params["ct"] = company_type
        if country:
            filters.append("c.country ILIKE :country")
            params["country"] = f"%{country}%"

        where = f"WHERE {' AND '.join(filters)}" if filters else ""

        count = (
            await self.db.execute(text(f"SELECT COUNT(*) FROM companies c {where}"), params)
        ).scalar() or 0

        rows = (
            await self.db.execute(
                text(f"""
                SELECT id::text, legal_name, aliases, company_type, country,
                       website, asset_count, active_trial_count, updated_at
                FROM companies c {where}
                ORDER BY legal_name
                LIMIT :limit OFFSET :offset
            """),
                params,
            )
        ).fetchall()

        items = [
            {
                "id": r[0],
                "legal_name": r[1],
                "aliases": r[2] or [],
                "company_type": r[3],
                "country": r[4],
                "website": r[5],
                "asset_count": r[6],
                "active_trial_count": r[7],
                "updated_at": r[8].isoformat() if r[8] else None,
            }
            for r in rows
        ]
        return items, count

    async def get_company_detail(self, company_id: UUID) -> dict:
        row = (
            await self.db.execute(
                text(
                    "SELECT id::text, legal_name, aliases, company_type, country, website, "
                    "investor_relations_url, pipeline_url, external_ids, asset_count, "
                    "active_trial_count, updated_at "
                    "FROM companies WHERE id = :id::uuid"
                ),
                {"id": str(company_id)},
            )
        ).fetchone()

        if not row:
            raise NotFoundError("Company", str(company_id))

        return {
            "id": row[0],
            "legal_name": row[1],
            "aliases": row[2] or [],
            "company_type": row[3],
            "country": row[4],
            "website": row[5],
            "investor_relations_url": row[6],
            "pipeline_url": row[7],
            "external_ids": row[8],
            "asset_count": row[9],
            "active_trial_count": row[10],
            "updated_at": row[11].isoformat() if row[11] else None,
        }
