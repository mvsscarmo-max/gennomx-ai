"""MCP Tool: find_trials — search clinical trials."""

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()
MAX_RESULTS = settings.MCP_MAX_RESULTS_PER_TOOL


async def find_trials(arguments: dict, db: AsyncSession | None = None) -> dict:
    """
    Search clinical trials by drug, indication, phase, status, sponsor, country or date range.
    Returns trial metadata with NCT ID, phase, status, interventions, endpoints, and sources.
    """
    drug = str(arguments.get("drug_asset", ""))[:200]
    indication = str(arguments.get("indication", ""))[:200]
    phase = str(arguments.get("phase", ""))[:50]
    trial_status = str(arguments.get("status", ""))[:100]
    sponsor = str(arguments.get("sponsor", ""))[:200]
    country = str(arguments.get("country", ""))[:100]
    nct_id = str(arguments.get("nct_id", ""))[:20]
    limit = min(int(arguments.get("limit", 20)), MAX_RESULTS)

    if not db:
        return {"data": [], "count": 0, "limitations": ["Database unavailable"]}

    filters = ["ct.is_current = true"]
    params: dict = {"limit": limit}

    if nct_id:
        filters.append("ct.nct_id = :nct_id")
        params["nct_id"] = nct_id.upper()

    if drug:
        filters.append("(ct.sponsor_name ILIKE :drug OR ct.interventions::text ILIKE :drug_like)")
        params["drug"] = f"%{drug}%"
        params["drug_like"] = f"%{drug}%"

    if indication:
        filters.append("ct.conditions @> ARRAY[:indication]::text[]")
        params["indication"] = indication

    if phase:
        filters.append("ct.phase_normalized = :phase")
        params["phase"] = phase.upper()

    if trial_status:
        filters.append("ct.status_normalized = :status")
        params["status"] = trial_status.upper()

    if sponsor:
        filters.append("ct.sponsor_name ILIKE :sponsor")
        params["sponsor"] = f"%{sponsor}%"

    if country:
        filters.append("ct.countries @> ARRAY[:country]::text[]")
        params["country"] = country

    where = f"WHERE {' AND '.join(filters)}" if filters else ""

    sql = text(f"""
        SELECT
            ct.id::text,
            ct.nct_id,
            ct.brief_title,
            ct.phase,
            ct.phase_normalized,
            ct.status,
            ct.status_normalized,
            ct.sponsor_name,
            ct.conditions,
            ct.enrollment,
            ct.start_date,
            ct.primary_completion_date,
            ct.countries,
            ct.interventions,
            ct.registry_source,
            ct.updated_at,
            ct.source_updated_at,
            ct.lifecycle_status
        FROM clinical_trials ct
        {where}
        ORDER BY ct.start_date DESC NULLS LAST
        LIMIT :limit
    """)

    try:
        rows = (await db.execute(sql, params)).fetchall()
    except Exception as e:
        logger.error("mcp_tool_query_failed", tool="find_trials", error=str(e))
        return {"data": [], "count": 0, "limitations": ["Query failed"]}

    results = [
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
            "interventions": r[13] or [],
            "registry_source": r[14],
            "last_updated": r[15].isoformat() if r[15] else None,
            "source_updated_at": r[16].isoformat() if r[16] else None,
            "freshness_status": "revalidation_required" if r[17] == "stale" else "current",
            "_source": "gennomx_clinical_trials",
        }
        for r in rows
    ]

    return {
        "data": results,
        "count": len(results),
        "limitations": [f"Results capped at {MAX_RESULTS}."] if limit == MAX_RESULTS else [],
        "gaps": ["Results limited to sources ingested. Endpoint/result data may be incomplete."],
    }
