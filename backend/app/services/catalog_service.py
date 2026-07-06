"""Read-only catalog queries used by the operational dashboard."""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError


class CatalogService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_indications(
        self,
        *,
        q: str | None = None,
        therapeutic_area: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        filters: list[str] = []
        params: dict = {"offset": (page - 1) * page_size, "limit": page_size}
        if q:
            filters.append(
                "(preferred_name ILIKE :q OR :q_exact = ANY(COALESCE(aliases, ARRAY[]::text[])))"
            )
            params.update(q=f"%{q}%", q_exact=q)
        if therapeutic_area:
            filters.append("therapeutic_area ILIKE :therapeutic_area")
            params["therapeutic_area"] = f"%{therapeutic_area}%"
        where = f"WHERE {' AND '.join(filters)}" if filters else ""
        total = (
            await self.db.execute(text(f"SELECT COUNT(*) FROM indications {where}"), params)
        ).scalar() or 0
        rows = (
            await self.db.execute(
                text(f"""
            SELECT id::text, preferred_name, aliases, therapeutic_area, ontology_ids,
                   parent_indication_id::text, updated_at
            FROM indications {where}
            ORDER BY preferred_name LIMIT :limit OFFSET :offset
        """),
                params,
            )
        ).fetchall()
        return [
            {
                "id": row[0],
                "preferred_name": row[1],
                "aliases": row[2] or [],
                "therapeutic_area": row[3],
                "ontology_ids": row[4] or {},
                "parent_indication_id": row[5],
                "updated_at": row[6].isoformat() if row[6] else None,
            }
            for row in rows
        ], total

    async def get_indication(self, indication_id: UUID) -> dict:
        row = (
            await self.db.execute(
                text("""
            SELECT id::text, preferred_name, aliases, therapeutic_area, ontology_ids,
                   parent_indication_id::text, updated_at
            FROM indications WHERE id = CAST(:id AS uuid)
        """),
                {"id": str(indication_id)},
            )
        ).fetchone()
        if not row:
            raise NotFoundError("Indication", str(indication_id))
        return {
            "id": row[0],
            "preferred_name": row[1],
            "aliases": row[2] or [],
            "therapeutic_area": row[3],
            "ontology_ids": row[4] or {},
            "parent_indication_id": row[5],
            "updated_at": row[6].isoformat() if row[6] else None,
        }

    async def list_targets(
        self,
        *,
        q: str | None = None,
        target_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        filters: list[str] = []
        params: dict = {"offset": (page - 1) * page_size, "limit": page_size}
        if q:
            filters.append(
                "(symbol ILIKE :q OR name ILIKE :q OR "
                ":q_exact = ANY(COALESCE(aliases, ARRAY[]::text[])))"
            )
            params.update(q=f"%{q}%", q_exact=q)
        if target_type:
            filters.append("target_type = :target_type")
            params["target_type"] = target_type
        where = f"WHERE {' AND '.join(filters)}" if filters else ""
        total = (
            await self.db.execute(text(f"SELECT COUNT(*) FROM targets {where}"), params)
        ).scalar() or 0
        rows = (
            await self.db.execute(
                text(f"""
            SELECT id::text, symbol, name, aliases, organism, target_type, external_ids,
                   open_targets_score, associated_indication_ids, updated_at
            FROM targets {where}
            ORDER BY symbol LIMIT :limit OFFSET :offset
        """),
                params,
            )
        ).fetchall()
        return [
            {
                "id": row[0],
                "symbol": row[1],
                "name": row[2],
                "aliases": row[3] or [],
                "organism": row[4],
                "target_type": row[5],
                "external_ids": row[6] or {},
                "open_targets_score": row[7],
                "associated_indication_ids": row[8] or [],
                "updated_at": row[9].isoformat() if row[9] else None,
            }
            for row in rows
        ], total
