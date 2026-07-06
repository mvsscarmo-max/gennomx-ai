"""Drug-asset extraction and upsert logic derived from clinical-trial interventions."""

import json
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import text

from workers.persistence.evidence import _insert_asset_evidence_snippet

THERAPEUTIC_INTERVENTION_TYPES = {"DRUG", "BIOLOGICAL", "GENETIC"}
PHASE_RANK = {
    "EARLY_PHASE1": 1,
    "PHASE1": 2,
    "PHASE1_2": 3,
    "PHASE2": 4,
    "PHASE2_3": 5,
    "PHASE3": 6,
    "PHASE4": 7,
}


def _clean_asset_name(name: str | None) -> str | None:
    if not name:
        return None
    cleaned = " ".join(name.split()).strip(" ;,")
    if not cleaned or cleaned.lower() in {"placebo", "standard of care"}:
        return None
    return cleaned


def _merge_unique(existing: list[str] | None, incoming: Sequence[str | None]) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for item in [*(existing or []), *incoming]:
        cleaned = _clean_asset_name(item)
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key not in seen:
            seen.add(key)
            values.append(cleaned)
    return values


def _select_development_stage(current: str | None, candidate: str | None) -> str | None:
    if not current:
        return candidate
    if not candidate:
        return current
    return candidate if PHASE_RANK.get(candidate, 0) > PHASE_RANK.get(current, 0) else current


def _extract_asset_candidates(parsed) -> list[dict]:
    """Return unique asset candidates inferred from therapeutic interventions."""
    candidates: list[dict] = []
    seen: set[str] = set()

    for intervention in parsed.interventions or []:
        intervention_type = str(intervention.get("type") or "").upper()
        if intervention_type not in THERAPEUTIC_INTERVENTION_TYPES:
            continue

        name = _clean_asset_name(intervention.get("name"))
        if not name:
            continue

        key = name.casefold()
        if key in seen:
            continue

        aliases = _merge_unique([], intervention.get("other_names") or [])
        candidates.append(
            {
                "primary_name": name,
                "aliases": aliases,
                "modality": intervention_type,
            }
        )
        seen.add(key)

    return candidates


async def _upsert_drug_assets_from_trial(
    *,
    db,
    parsed,
    source_document_id: str | None,
    raw: dict | None = None,
) -> list[str]:
    asset_ids: list[str] = []
    conditions = _merge_unique([], parsed.conditions or [])
    sponsors = _merge_unique([], [parsed.sponsor_name])
    phase_normalized = getattr(parsed, "phase_normalized", None)

    for candidate in _extract_asset_candidates(parsed):
        existing = (
            await db.execute(
                text("""
                    SELECT id::text, aliases, indication_names, sponsor_names,
                           max_historical_stage, ingestion_metadata,
                           current_development_stage, development_status
                    FROM drug_assets
                    WHERE lower(primary_name) = lower(:primary_name)
                    LIMIT 1
                """),
                {"primary_name": candidate["primary_name"]},
            )
        ).fetchone()

        if existing:
            asset_id = str(existing[0])
            metadata = dict(existing[5] or {})
            nct_ids = _merge_unique(metadata.get("nct_ids"), [parsed.nct_id])
            metadata.update(
                {
                    "source": "clinicaltrials_gov",
                    "last_linked_at": datetime.now(UTC).isoformat(),
                    "nct_ids": nct_ids,
                }
            )
            await db.execute(
                text("""
                    UPDATE drug_assets
                    SET aliases = :aliases,
                        indication_names = :indication_names,
                        sponsor_names = :sponsor_names,
                        development_stage = :max_historical_stage,
                        max_historical_stage = :max_historical_stage,
                        current_development_stage = :current_development_stage,
                        development_status = :development_status,
                        primary_source_id = COALESCE(primary_source_id, :primary_source_id),
                        ingestion_metadata = CAST(:ingestion_metadata AS jsonb),
                        updated_at = now()
                    WHERE id = :asset_id
                """),
                {
                    "asset_id": asset_id,
                    "aliases": _merge_unique(existing[1], candidate["aliases"]),
                    "indication_names": _merge_unique(existing[2], conditions),
                    "sponsor_names": _merge_unique(existing[3], sponsors),
                    "max_historical_stage": _select_development_stage(
                        existing[4], phase_normalized
                    ),
                    "current_development_stage": (
                        existing[6]
                        if getattr(parsed, "status_normalized", None)
                        in {"COMPLETED", "TERMINATED", "WITHDRAWN", "SUSPENDED"}
                        else phase_normalized or existing[6]
                    ),
                    "development_status": (
                        "discontinued"
                        if getattr(parsed, "status_normalized", None) in {"TERMINATED", "WITHDRAWN"}
                        else "active"
                        if getattr(parsed, "status_normalized", None)
                        in {"RECRUITING", "NOT_YET_RECRUITING", "ACTIVE_NOT_RECRUITING"}
                        else existing[7] or "unknown"
                    ),
                    "primary_source_id": source_document_id,
                    "ingestion_metadata": json.dumps(metadata),
                },
            )
        else:
            asset_id = str(uuid.uuid4())
            await db.execute(
                text("""
                    INSERT INTO drug_assets (
                        id, primary_name, aliases, modality, development_stage,
                        current_development_stage, max_historical_stage, development_status,
                        indication_names, sponsor_names, source_confidence,
                        data_completeness_score, primary_source_id,
                        ingestion_metadata, created_at, updated_at
                    )
                    VALUES (
                        :asset_id, :primary_name, :aliases, :modality, :development_stage,
                        :development_stage, :development_stage, :development_status,
                        :indication_names, :sponsor_names, 0.78,
                        0.35, :primary_source_id,
                        CAST(:ingestion_metadata AS jsonb), now(), now()
                    )
                """),
                {
                    "asset_id": asset_id,
                    "primary_name": candidate["primary_name"],
                    "aliases": candidate["aliases"],
                    "modality": candidate["modality"],
                    "development_stage": phase_normalized,
                    "development_status": "active",
                    "indication_names": conditions,
                    "sponsor_names": sponsors,
                    "primary_source_id": source_document_id,
                    "ingestion_metadata": json.dumps(
                        {
                            "source": "clinicaltrials_gov",
                            "created_from": "trial_intervention",
                            "nct_ids": _merge_unique([], [parsed.nct_id]),
                            "last_linked_at": datetime.now(UTC).isoformat(),
                        }
                    ),
                },
            )

        asset_ids.append(asset_id)
        if source_document_id:
            await _insert_asset_evidence_snippet(
                db=db,
                source_document_id=source_document_id,
                asset_id=asset_id,
                parsed=parsed,
                primary_name=candidate["primary_name"],
                raw=raw,
            )

    return asset_ids
