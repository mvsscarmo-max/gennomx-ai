"""MCP Tool: search_drugs — searches the DrugAsset table."""

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()
MAX_RESULTS = settings.MCP_MAX_RESULTS_PER_TOOL


async def search_drugs(arguments: dict, db: AsyncSession | None = None) -> dict:
    """
    Search therapeutic assets by name, indication, target, modality, phase, or company.

    Returns structured list with aliases, phase, targets, companies, status, sources.
    """
    q = str(arguments.get("query", ""))[:200]
    indication = str(arguments.get("indication", ""))[:200]
    target = str(arguments.get("target", ""))[:200]
    modality = str(arguments.get("modality", ""))[:100]
    company = str(arguments.get("company", ""))[:200]
    limit = min(int(arguments.get("limit", 20)), MAX_RESULTS)

    if not db:
        return {"data": [], "count": 0, "limitations": ["Database unavailable"]}

    filters = []
    params: dict = {"limit": limit}

    if q:
        filters.append("(da.primary_name ILIKE :q OR :q = ANY(da.aliases))")
        params["q"] = f"%{q}%"

    if indication:
        filters.append("da.indication_names @> ARRAY[:indication]::text[]")
        params["indication"] = indication

    if target:
        filters.append("da.target_symbols @> ARRAY[:target]::text[]")
        params["target"] = target

    if modality:
        filters.append("da.modality ILIKE :modality")
        params["modality"] = f"%{modality}%"

    if company:
        filters.append("da.sponsor_names @> ARRAY[:company]::text[]")
        params["company"] = company

    where = f"WHERE {' AND '.join(filters)}" if filters else ""

    sql = text(f"""
        SELECT
            da.id::text,
            da.primary_name,
            da.aliases,
            da.inn,
            da.modality,
            da.mechanism_of_action,
            da.development_stage,
            da.indication_names,
            da.target_symbols,
            da.sponsor_names,
            da.regulatory_status_summary,
            da.source_confidence,
            da.updated_at
        FROM drug_assets da
        {where}
        ORDER BY da.source_confidence DESC NULLS LAST, da.primary_name
        LIMIT :limit
    """)

    try:
        rows = (await db.execute(sql, params)).fetchall()
    except Exception as e:
        logger.error("mcp_tool_query_failed", tool="search_drugs", error=str(e))
        return {"data": [], "count": 0, "limitations": ["Query failed"]}

    results = [
        {
            "id": r[0],
            "primary_name": r[1],
            "aliases": r[2] or [],
            "inn": r[3],
            "modality": r[4],
            "mechanism_of_action": r[5],
            "development_stage": r[6],
            "indications": r[7] or [],
            "targets": r[8] or [],
            "companies": r[9] or [],
            "regulatory_status": r[10],
            "confidence_score": r[11],
            "last_updated": r[12].isoformat() if r[12] else None,
            "_source": "gennomx_drug_assets",
        }
        for r in rows
    ]

    limitations = []
    if not results:
        limitations.append("No matching assets found. Try broader search terms.")
    if limit == MAX_RESULTS:
        limitations.append(
            f"Results capped at {MAX_RESULTS}. Narrow your query for more precise results."
        )

    return {
        "data": results,
        "count": len(results),
        "limitations": limitations,
        "gaps": ["Results limited to sources ingested into GennomX AI. Not exhaustive."],
    }
