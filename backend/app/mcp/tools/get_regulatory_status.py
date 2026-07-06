"""MCP Tool: get_regulatory_status."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_regulatory_status(arguments: dict, db: AsyncSession | None = None) -> dict:
    asset = str(arguments.get("asset", ""))[:200]
    indication = str(arguments.get("indication", ""))[:200]
    region = str(arguments.get("region", ""))[:100]
    agency = str(arguments.get("agency", ""))[:100]

    if not db or not asset:
        return {"data": [], "count": 0, "limitations": ["asset name required"]}

    filters = [
        "(da.primary_name ILIKE :asset OR :asset_exact = ANY(da.aliases))",
        "ra.is_current = true",
    ]
    params = {"asset": f"%{asset}%", "asset_exact": asset}

    if region:
        filters.append("ra.region ILIKE :region")
        params["region"] = f"%{region}%"

    if agency:
        filters.append("ra.agency ILIKE :agency")
        params["agency"] = f"%{agency}%"

    if indication:
        filters.append("ra.indication_name ILIKE :indication")
        params["indication"] = f"%{indication}%"

    where = " AND ".join(filters)

    rows = (
        await db.execute(
            text(f"""
            SELECT
                ra.id::text,
                da.primary_name,
                ra.region,
                ra.agency,
                ra.approval_status,
                ra.approval_date,
                ra.indication_name,
                ra.pathway,
                ra.special_designations,
                ra.application_number,
                ra.label_url,
                ra.updated_at
            FROM regulatory_approvals ra
            JOIN drug_assets da ON da.id = ra.drug_asset_id
            WHERE {where}
            ORDER BY ra.approval_date DESC NULLS LAST
            LIMIT 50
        """),
            params,
        )
    ).fetchall()

    results = [
        {
            "id": r[0],
            "asset": r[1],
            "region": r[2],
            "agency": r[3],
            "status": r[4],
            "approval_date": str(r[5]) if r[5] else None,
            "indication": r[6],
            "pathway": r[7],
            "special_designations": r[8] or [],
            "application_number": r[9],
            "label_url": r[10],
            "last_updated": r[11].isoformat() if r[11] else None,
            "_source": "gennomx_regulatory_approvals",
        }
        for r in rows
    ]

    gaps = []
    if not results:
        gaps.append("No regulatory data found. May not be ingested or approved yet.")

    return {
        "data": results,
        "count": len(results),
        "limitations": [
            "Data reflects ingested regulatory sources. Verify against official sources."
        ],
        "gaps": gaps,
    }
