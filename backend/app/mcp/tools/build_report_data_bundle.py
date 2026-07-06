"""MCP Tool: build_report_data_bundle — assemble structured data bundle for external AI."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

BUNDLE_TYPES = {
    "asset_profile",
    "company_pipeline",
    "competitive_landscape",
    "regulatory_history",
    "safety_overview",
    "target_landscape",
    "trial_benchmark",
    "weekly_intelligence",
}


async def build_report_data_bundle(arguments: dict, db: AsyncSession | None = None) -> dict:
    """
    Assemble a structured data bundle for a specific report type.
    This does NOT generate the report — it provides the data for the host model to use.
    """
    report_type = str(arguments.get("report_type", "asset_profile"))[:50]
    entity_ids = [str(e)[:50] for e in arguments.get("entity_ids", [])][:10]
    indication = str(arguments.get("indication", ""))[:200]
    evidence_depth = str(arguments.get("evidence_depth", "standard"))[:20]
    include_limitations = bool(arguments.get("include_limitations", True))

    if report_type not in BUNDLE_TYPES:
        return {
            "data": {},
            "count": 0,
            "limitations": [f"Unknown report_type '{report_type}'. Valid: {sorted(BUNDLE_TYPES)}"],
        }

    if not db:
        return {"data": {}, "count": 0, "limitations": ["Database unavailable"]}

    bundle: dict = {
        "report_type": report_type,
        "requested_at": None,
        "scope": {
            "entity_ids": entity_ids,
            "indication": indication,
            "evidence_depth": evidence_depth,
        },
        "data": {},
        "evidence": [],
        "sources": [],
        "limitations": [],
        "gaps": [],
        "data_quality_notes": [],
    }

    if report_type == "asset_profile" and entity_ids:
        await _populate_asset_profile(bundle, entity_ids[0], db)
    elif report_type == "company_pipeline" and entity_ids:
        await _populate_company_pipeline(bundle, entity_ids[0], db)
    elif report_type == "competitive_landscape" and indication:
        await _populate_competitive_landscape(bundle, indication, db)

    if include_limitations:
        bundle["limitations"].extend(
            [
                "Data is limited to sources ingested into GennomX AI at time of bundle generation.",
                (
                    "Head-to-head comparisons are indirect; trials have different designs, "
                    "populations, and endpoints."
                ),
                (
                    "This bundle is structured data for AI analysis, not a verified regulatory "
                    "or clinical opinion."
                ),
            ]
        )

    total_records = sum(
        len(v) if isinstance(v, list) else (1 if v else 0) for v in bundle["data"].values()
    )

    return {
        "data": bundle,
        "count": total_records,
        "limitations": bundle["limitations"],
        "gaps": bundle["gaps"],
    }


async def _populate_asset_profile(bundle: dict, asset_id_or_name: str, db: AsyncSession) -> None:
    asset = (
        await db.execute(
            text("""
            SELECT id::text, primary_name, aliases, modality, mechanism_of_action,
                   development_stage, indication_names, target_symbols, sponsor_names,
                   regulatory_status_summary, source_confidence, updated_at
            FROM drug_assets
            WHERE id::text = :q OR primary_name ILIKE :qlike
            LIMIT 1
        """),
            {"q": asset_id_or_name, "qlike": f"%{asset_id_or_name}%"},
        )
    ).fetchone()

    if not asset:
        bundle["gaps"].append(f"Asset '{asset_id_or_name}' not found in GennomX.")
        return

    trials = (
        await db.execute(
            text("""
            SELECT nct_id, brief_title, phase_normalized, status_normalized,
                   conditions, sponsor_name, enrollment, start_date, primary_completion_date
            FROM clinical_trials
            WHERE :name = ANY(drug_asset_ids)
               OR sponsor_name ILIKE :sname
            ORDER BY start_date DESC NULLS LAST
            LIMIT 20
        """),
            {"name": asset[1], "sname": f"%{asset[7][0] if asset[7] else ''}%"},
        )
    ).fetchall()

    bundle["data"] = {
        "asset": {
            "id": asset[0],
            "name": asset[1],
            "aliases": asset[2] or [],
            "modality": asset[3],
            "moa": asset[4],
            "stage": asset[5],
            "indications": asset[6] or [],
            "targets": asset[7] or [],
            "sponsors": asset[8] or [],
            "regulatory_status": asset[9],
            "confidence": asset[10],
            "updated": asset[11].isoformat() if asset[11] else None,
        },
        "trials": [
            {
                "nct_id": t[0],
                "title": t[1],
                "phase": t[2],
                "status": t[3],
                "conditions": t[4] or [],
                "sponsor": t[5],
                "enrollment": t[6],
                "start_date": str(t[7]) if t[7] else None,
                "completion": str(t[8]) if t[8] else None,
            }
            for t in trials
        ],
    }


async def _populate_company_pipeline(bundle: dict, company: str, db: AsyncSession) -> None:
    assets = (
        await db.execute(
            text(
                "SELECT id::text, primary_name, modality, development_stage, indication_names "
                "FROM drug_assets WHERE sponsor_names @> ARRAY[:co]::text[] LIMIT 30"
            ),
            {"co": company},
        )
    ).fetchall()
    bundle["data"]["company"] = company
    bundle["data"]["assets"] = [
        {"id": a[0], "name": a[1], "modality": a[2], "stage": a[3], "indications": a[4] or []}
        for a in assets
    ]


async def _populate_competitive_landscape(bundle: dict, indication: str, db: AsyncSession) -> None:
    assets = (
        await db.execute(
            text(
                "SELECT id::text, primary_name, modality, development_stage, sponsor_names "
                "FROM drug_assets WHERE indication_names @> ARRAY[:ind]::text[] LIMIT 50"
            ),
            {"ind": indication},
        )
    ).fetchall()
    trials = (
        await db.execute(
            text(
                "SELECT nct_id, brief_title, phase_normalized, status_normalized, sponsor_name "
                "FROM clinical_trials WHERE conditions @> ARRAY[:ind]::text[] LIMIT 50"
            ),
            {"ind": indication},
        )
    ).fetchall()
    bundle["data"] = {
        "indication": indication,
        "assets": [
            {"id": a[0], "name": a[1], "modality": a[2], "stage": a[3], "sponsors": a[4] or []}
            for a in assets
        ],
        "trials": [
            {"nct_id": t[0], "title": t[1], "phase": t[2], "status": t[3], "sponsor": t[4]}
            for t in trials
        ],
    }
