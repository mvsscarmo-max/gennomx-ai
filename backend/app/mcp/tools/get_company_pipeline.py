"""MCP Tool: get_company_pipeline."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings

settings = get_settings()
MAX_RESULTS = settings.MCP_MAX_RESULTS_PER_TOOL


async def get_company_pipeline(arguments: dict, db: AsyncSession | None = None) -> dict:
    company_name = str(arguments.get("company_name", ""))[:200]

    if not db or not company_name:
        return {"data": {}, "count": 0, "limitations": ["company_name required"]}

    assets = (
        await db.execute(
            text("""
            SELECT id::text, primary_name, aliases, inn, modality, development_stage,
                   indication_names, target_symbols, regulatory_status_summary,
                   source_confidence, updated_at
            FROM drug_assets
            WHERE sponsor_names @> ARRAY[:company]::text[]
            LIMIT :limit
        """),
            {"company": company_name, "limit": MAX_RESULTS},
        )
    ).fetchall()

    trials = (
        await db.execute(
            text("""
            SELECT id::text, nct_id, brief_title, phase_normalized, status_normalized,
                   conditions, start_date, primary_completion_date
            FROM clinical_trials
            WHERE sponsor_name ILIKE :company
            ORDER BY start_date DESC NULLS LAST
            LIMIT :limit
        """),
            {"company": f"%{company_name}%", "limit": MAX_RESULTS},
        )
    ).fetchall()

    pipeline = {
        "company": company_name,
        "assets": [
            {
                "id": a[0],
                "name": a[1],
                "aliases": a[2] or [],
                "inn": a[3],
                "modality": a[4],
                "stage": a[5],
                "indications": a[6] or [],
                "targets": a[7] or [],
                "regulatory_status": a[8],
                "confidence": a[9],
                "updated": a[10].isoformat() if a[10] else None,
            }
            for a in assets
        ],
        "trials": [
            {
                "id": t[0],
                "nct_id": t[1],
                "title": t[2],
                "phase": t[3],
                "status": t[4],
                "conditions": t[5] or [],
                "start_date": str(t[6]) if t[6] else None,
                "primary_completion": str(t[7]) if t[7] else None,
            }
            for t in trials
        ],
    }

    total = len(assets) + len(trials)
    return {
        "data": pipeline,
        "count": total,
        "limitations": ["Pipeline data reflects ingested sources only."],
        "gaps": (
            []
            if total > 0
            else ["No data found for this company. The company may not be in GennomX yet."]
        ),
    }
