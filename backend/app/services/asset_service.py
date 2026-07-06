"""Service layer for DrugAsset queries."""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError


class AssetService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_assets(
        self,
        q: str | None = None,
        indication: str | None = None,
        target: str | None = None,
        company: str | None = None,
        phase: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        filters = []
        params: dict = {"offset": (page - 1) * page_size, "limit": page_size}

        if q:
            filters.append("(da.primary_name ILIKE :q OR :q_exact = ANY(da.aliases))")
            params["q"] = f"%{q}%"
            params["q_exact"] = q

        if indication:
            filters.append("da.indication_names @> ARRAY[:indication]::text[]")
            params["indication"] = indication

        if target:
            filters.append("da.target_symbols @> ARRAY[:target]::text[]")
            params["target"] = target

        if company:
            filters.append("da.sponsor_names @> ARRAY[:company]::text[]")
            params["company"] = company

        if phase:
            filters.append("da.development_stage = :phase")
            params["phase"] = phase.upper()

        where = f"WHERE {' AND '.join(filters)}" if filters else ""

        count_sql = text(f"SELECT COUNT(*) FROM drug_assets da {where}")
        count_result = await self.db.execute(count_sql, params)
        total = count_result.scalar() or 0

        data_sql = text(f"""
            SELECT id::text, primary_name, aliases, inn, modality, development_stage,
                   indication_names, target_symbols, sponsor_names,
                   source_confidence, updated_at
            FROM drug_assets da
            {where}
            ORDER BY source_confidence DESC NULLS LAST, primary_name
            LIMIT :limit OFFSET :offset
        """)
        rows = (await self.db.execute(data_sql, params)).fetchall()

        items = [
            {
                "id": r[0],
                "primary_name": r[1],
                "aliases": r[2] or [],
                "inn": r[3],
                "modality": r[4],
                "development_stage": r[5],
                "indication_names": r[6] or [],
                "target_symbols": r[7] or [],
                "sponsor_names": r[8] or [],
                "source_confidence": r[9],
                "updated_at": r[10].isoformat() if r[10] else None,
            }
            for r in rows
        ]
        return items, total

    async def get_asset_detail(self, asset_id: UUID) -> dict:
        row = (
            await self.db.execute(
                text(
                    "SELECT id::text, primary_name, aliases, inn, modality, mechanism_of_action, "
                    "development_stage, external_ids, indication_names, target_symbols, "
                    "sponsor_names, regulatory_status_summary, source_confidence, "
                    "data_completeness_score, ingestion_metadata, created_at, updated_at "
                    "FROM drug_assets WHERE id = :id::uuid"
                ),
                {"id": str(asset_id)},
            )
        ).fetchone()

        if not row:
            raise NotFoundError("DrugAsset", str(asset_id))

        return {
            "id": row[0],
            "primary_name": row[1],
            "aliases": row[2] or [],
            "inn": row[3],
            "modality": row[4],
            "mechanism_of_action": row[5],
            "development_stage": row[6],
            "external_ids": row[7],
            "indication_names": row[8] or [],
            "target_symbols": row[9] or [],
            "sponsor_names": row[10] or [],
            "regulatory_status_summary": row[11],
            "source_confidence": row[12],
            "data_completeness_score": row[13],
            "created_at": row[15].isoformat() if row[15] else None,
            "updated_at": row[16].isoformat() if row[16] else None,
        }
