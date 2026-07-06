"""MCP Tool: compare_assets — structured data for head-to-head comparison."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def compare_assets(arguments: dict, db: AsyncSession | None = None) -> dict:
    assets = [str(a)[:200] for a in arguments.get("assets", [])][:5]
    indication = str(arguments.get("indication", ""))[:200]

    if not db or len(assets) < 2:
        return {
            "data": {},
            "count": 0,
            "limitations": ["Provide at least 2 asset names in 'assets' list"],
        }

    comparison: dict = {"assets": [], "trials_by_asset": {}, "indication": indication}

    for asset_name in assets:
        asset = (
            await db.execute(
                text(
                    "SELECT id::text, primary_name, modality, development_stage, indication_names, "
                    "target_symbols, sponsor_names, source_confidence "
                    "FROM drug_assets WHERE primary_name ILIKE :n LIMIT 1"
                ),
                {"n": f"%{asset_name}%"},
            )
        ).fetchone()

        if asset:
            comparison["assets"].append(
                {
                    "id": asset[0],
                    "name": asset[1],
                    "modality": asset[2],
                    "stage": asset[3],
                    "indications": asset[4] or [],
                    "targets": asset[5] or [],
                    "sponsors": asset[6] or [],
                    "confidence": asset[7],
                }
            )
            trials = (
                await db.execute(
                    text(
                        "SELECT nct_id, brief_title, phase_normalized, "
                        "status_normalized, enrollment FROM clinical_trials "
                        "WHERE interventions::text ILIKE :n LIMIT 10"
                    ),
                    {"n": f"%{asset_name}%"},
                )
            ).fetchall()
            comparison["trials_by_asset"][asset[1]] = [
                {"nct_id": t[0], "title": t[1], "phase": t[2], "status": t[3], "enrollment": t[4]}
                for t in trials
            ]

    total = len(comparison["assets"])
    return {
        "data": comparison,
        "count": total,
        "limitations": [
            "Comparisons are indirect. Trials have different designs, populations, timepoints.",
            (
                "Statistical comparisons across trials are not valid without accounting for "
                "methodological differences."
            ),
        ],
        "gaps": [
            f"Asset '{a}' not found"
            for a in assets
            if not any(x["name"].lower() == a.lower() for x in comparison["assets"])
        ],
    }
