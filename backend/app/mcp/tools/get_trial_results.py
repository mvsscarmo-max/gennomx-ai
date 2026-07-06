"""MCP Tool: get_trial_results — retrieve results, endpoints, and AEs for a trial."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings

settings = get_settings()


async def get_trial_results(arguments: dict, db: AsyncSession | None = None) -> dict:
    nct_id = str(arguments.get("nct_id", ""))[:20]
    trial_id = str(arguments.get("trial_id", ""))[:50]
    endpoint_type = str(arguments.get("endpoint_type", ""))[:50]

    if not db:
        return {"data": {}, "count": 0, "limitations": ["Database unavailable"]}

    if not nct_id and not trial_id:
        return {"data": {}, "count": 0, "limitations": ["Provide nct_id or trial_id"]}

    # Resolve trial
    if nct_id:
        trial_row = (
            await db.execute(
                text(
                    "SELECT id::text, nct_id, brief_title, phase_normalized, status_normalized, "
                    "sponsor_name, conditions FROM clinical_trials "
                    "WHERE nct_id = :nct_id AND is_current = true"
                ),
                {"nct_id": nct_id.upper()},
            )
        ).fetchone()
    else:
        trial_row = (
            await db.execute(
                text(
                    "SELECT id::text, nct_id, brief_title, phase_normalized, status_normalized, "
                    "sponsor_name, conditions FROM clinical_trials "
                    "WHERE id = :tid::uuid AND is_current = true"
                ),
                {"tid": trial_id},
            )
        ).fetchone()

    if not trial_row:
        return {"data": {}, "count": 0, "limitations": ["Trial not found"]}

    resolved_id = trial_row[0]

    # Endpoints
    ep_filter = "AND ep.endpoint_type = :ep_type" if endpoint_type else ""
    ep_params = {"trial_id": resolved_id}
    if endpoint_type:
        ep_params["ep_type"] = endpoint_type.lower()

    endpoints = (
        await db.execute(
            text(
                f"SELECT id::text, endpoint_name, endpoint_type, category, timepoint, "
                f"measurement_unit FROM endpoints ep "
                f"WHERE trial_id = :trial_id AND ep.is_current = true {ep_filter}"
            ),
            ep_params,
        )
    ).fetchall()

    # Results
    results_rows = (
        await db.execute(
            text(
                "SELECT id::text, endpoint_id, arm_label, result_value, comparator_value, "
                "p_value, hazard_ratio, confidence_interval_lower, confidence_interval_upper, "
                "timepoint, n_analyzed, confidence_score, extraction_method "
                "FROM trial_results WHERE trial_id = :trial_id "
                "AND is_current = true LIMIT 50"
            ),
            {"trial_id": resolved_id},
        )
    ).fetchall()

    trial_data = {
        "trial": {
            "id": trial_row[0],
            "nct_id": trial_row[1],
            "title": trial_row[2],
            "phase": trial_row[3],
            "status": trial_row[4],
            "sponsor": trial_row[5],
            "conditions": trial_row[6] or [],
        },
        "endpoints": [
            {
                "id": e[0],
                "name": e[1],
                "type": e[2],
                "category": e[3],
                "timepoint": e[4],
                "unit": e[5],
            }
            for e in endpoints
        ],
        "results": [
            {
                "id": r[0],
                "endpoint_id": r[1],
                "arm": r[2],
                "value": r[3],
                "comparator_value": r[4],
                "p_value": r[5],
                "hazard_ratio": r[6],
                "ci_lower": r[7],
                "ci_upper": r[8],
                "timepoint": r[9],
                "n_analyzed": r[10],
                "confidence_score": r[11],
                "extraction_method": r[12],
            }
            for r in results_rows
        ],
    }

    total = len(endpoints) + len(results_rows)
    gaps = []
    if not endpoints:
        gaps.append("No endpoints found. May not have been ingested yet.")
    if not results_rows:
        gaps.append(
            "No quantitative results found. Results may be unpublished or not yet ingested."
        )

    return {
        "data": trial_data,
        "count": total,
        "limitations": ["Results reflect data available at time of ingestion."],
        "gaps": gaps,
    }
