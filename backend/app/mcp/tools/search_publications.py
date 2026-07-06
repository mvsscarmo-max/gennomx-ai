"""MCP Tool: search_publications."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings

settings = get_settings()
MAX_RESULTS = settings.MCP_MAX_RESULTS_PER_TOOL


async def search_publications(arguments: dict, db: AsyncSession | None = None) -> dict:
    asset = str(arguments.get("asset", ""))[:200]
    indication = str(arguments.get("indication", ""))[:200]
    q = str(arguments.get("query", ""))[:200]
    limit = min(int(arguments.get("limit", 20)), MAX_RESULTS)

    if not db:
        return {"data": [], "count": 0, "limitations": ["Database unavailable"]}

    filters = ["p.is_current = true"]
    params: dict = {"limit": limit}

    if q:
        filters.append("(p.title ILIKE :q OR p.abstract ILIKE :q)")
        params["q"] = f"%{q}%"

    if asset:
        filters.append("p.linked_asset_ids @> ARRAY[:asset]::text[]")
        params["asset"] = asset

    if indication:
        filters.append("p.linked_indication_ids @> ARRAY[:indication]::text[]")
        params["indication"] = indication

    where = f"WHERE {' AND '.join(filters)}" if filters else ""

    rows = (
        await db.execute(
            text(f"""
            SELECT id::text, title, journal, publication_date, publication_type,
                   doi, pmid, pmcid, abstract, authors, open_access, source_url, updated_at
            FROM publications p
            {where}
            ORDER BY publication_date DESC NULLS LAST
            LIMIT :limit
        """),
            params,
        )
    ).fetchall()

    results = [
        {
            "id": r[0],
            "title": r[1],
            "journal": r[2],
            "date": str(r[3]) if r[3] else None,
            "type": r[4],
            "doi": r[5],
            "pmid": r[6],
            "pmcid": r[7],
            "abstract": (r[8] or "")[:500],  # truncate abstract to 500 chars
            "authors": (r[9] or [])[:5],  # top 5 authors
            "open_access": r[10],
            "url": r[11],
            "last_updated": r[12].isoformat() if r[12] else None,
            "_source": "gennomx_publications",
        }
        for r in rows
    ]

    return {
        "data": results,
        "count": len(results),
        "limitations": [
            "Publications limited to ingested sources. Full text only for open access."
        ],
        "gaps": [],
    }
