"""Small ClinicalTrials.gov outcome/safety projection for DRY-7 fixtures."""

import json
import uuid

from sqlalchemy import text

from workers.base.staging import canonical_value_hash


def _integer(value) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _number(value) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


async def _evidence_id(
    db,
    *,
    source_document_id: str,
    trial_id: str,
    field: str,
    section: str,
    fragment: object,
) -> str:
    evidence_id = str(uuid.uuid4())
    row = (
        await db.execute(
            text("""
                INSERT INTO evidence_snippets (
                    id, source_document_id, entity_type, entity_id, entity_field,
                    text_excerpt, section, extraction_method, confidence_score,
                    created_at, updated_at
                ) SELECT
                    :id, :source_document_id, 'clinical_trial', :trial_id, :field,
                    :excerpt, :section, 'api_source_fragment', 0.99, now(), now()
                WHERE NOT EXISTS (
                    SELECT 1 FROM evidence_snippets
                    WHERE source_document_id = :source_document_id
                      AND entity_type = 'clinical_trial' AND entity_id = :trial_id
                      AND entity_field = :field
                )
                RETURNING id::text
            """),
            {
                "id": evidence_id,
                "source_document_id": source_document_id,
                "trial_id": trial_id,
                "field": field,
                "excerpt": json.dumps(fragment, ensure_ascii=False, sort_keys=True),
                "section": section,
            },
        )
    ).fetchone()
    if row:
        return str(row[0])
    existing = (
        await db.execute(
            text("""
                SELECT id::text FROM evidence_snippets
                WHERE source_document_id = :source_document_id
                  AND entity_type = 'clinical_trial' AND entity_id = :trial_id
                  AND entity_field = :field
            """),
            {
                "source_document_id": source_document_id,
                "trial_id": trial_id,
                "field": field,
            },
        )
    ).fetchone()
    if not existing:
        raise RuntimeError("Outcome evidence could not be persisted")
    return str(existing[0])


async def _upsert_endpoint(db, *, trial_id: str, evidence_id: str, endpoint: dict) -> str:
    values = {
        "trial_id": trial_id,
        "arm_id": endpoint.get("arm_id"),
        "name": endpoint["name"],
        "type": endpoint.get("type"),
        "category": endpoint.get("category"),
        "timepoint": endpoint.get("timepoint"),
        "unit": endpoint.get("unit"),
        "evidence_id": evidence_id,
    }
    fingerprint = canonical_value_hash(values)
    existing = (
        await db.execute(
            text("""
                SELECT id::text, ingestion_metadata->>'source_fingerprint'
                FROM endpoints
                WHERE trial_id = :trial_id
                  AND COALESCE(arm_id, '') = COALESCE(:arm_id, '')
                  AND lower(endpoint_name) = lower(:name)
                  AND COALESCE(timepoint, '') = COALESCE(:timepoint, '')
                  AND is_current = true
                FOR UPDATE
            """),
            values,
        )
    ).fetchone()
    if existing and existing[1] == fingerprint:
        return str(existing[0])
    if existing:
        await db.execute(
            text("""
                UPDATE endpoints SET is_current = false, lifecycle_status = 'superseded',
                    valid_to = now(), system_to = now(), updated_at = now()
                WHERE id = :id
            """),
            {"id": str(existing[0])},
        )
    endpoint_id = str(uuid.uuid4())
    await db.execute(
        text("""
            INSERT INTO endpoints (
                id, trial_id, arm_id, endpoint_name, endpoint_type, category,
                timepoint, measurement_unit, source_evidence_id, ingestion_metadata,
                valid_from, system_from, is_current, lifecycle_status, created_at, updated_at
            ) VALUES (
                :id, :trial_id, :arm_id, :name, :type, :category,
                :timepoint, :unit, :evidence_id, CAST(:metadata AS jsonb),
                now(), now(), true, 'active', now(), now()
            )
        """),
        {
            **values,
            "id": endpoint_id,
            "metadata": json.dumps(
                {"source": "clinicaltrials_gov", "source_fingerprint": fingerprint}
            ),
        },
    )
    return endpoint_id


async def _upsert_result(
    db, *, trial_id: str, endpoint_id: str, evidence_id: str, result: dict
) -> bool:
    values = {
        "trial_id": trial_id,
        "endpoint_id": endpoint_id,
        "arm_id": result.get("arm_id"),
        "arm_label": result.get("arm_label"),
        "result_value": result.get("result_value"),
        "statistical_measure": result.get("statistical_measure"),
        "p_value": result.get("p_value"),
        "ci_lower": result.get("ci_lower"),
        "ci_upper": result.get("ci_upper"),
        "hazard_ratio": result.get("hazard_ratio"),
        "odds_ratio": result.get("odds_ratio"),
        "timepoint": result.get("timepoint"),
        "population": result.get("population"),
        "n_analyzed": result.get("n_analyzed"),
        "raw_result": json.dumps(result.get("raw_result", {}), ensure_ascii=False, sort_keys=True),
        "evidence_id": evidence_id,
    }
    fingerprint = canonical_value_hash(values)
    existing = (
        await db.execute(
            text("""
                SELECT id::text, ingestion_metadata->>'source_fingerprint'
                FROM trial_results
                WHERE trial_id = :trial_id AND endpoint_id = :endpoint_id
                  AND COALESCE(arm_id, '') = COALESCE(:arm_id, '')
                  AND COALESCE(timepoint, '') = COALESCE(:timepoint, '')
                  AND COALESCE(population, '') = COALESCE(:population, '')
                  AND is_current = true
                FOR UPDATE
            """),
            values,
        )
    ).fetchone()
    if existing and existing[1] == fingerprint:
        return False
    if existing:
        await db.execute(
            text("""
                UPDATE trial_results SET is_current = false, lifecycle_status = 'superseded',
                    valid_to = now(), system_to = now(), updated_at = now()
                WHERE id = :id
            """),
            {"id": str(existing[0])},
        )
    await db.execute(
        text("""
            INSERT INTO trial_results (
                id, trial_id, endpoint_id, arm_id, arm_label, result_value,
                statistical_measure, p_value, confidence_interval_lower,
                confidence_interval_upper, hazard_ratio, odds_ratio, timepoint,
                population, n_analyzed, raw_result, source_evidence_id,
                confidence_score, extraction_method, ingestion_metadata,
                valid_from, system_from, is_current, lifecycle_status, created_at, updated_at
            ) VALUES (
                :id, :trial_id, :endpoint_id, :arm_id, :arm_label, :result_value,
                :statistical_measure, :p_value, :ci_lower, :ci_upper, :hazard_ratio,
                :odds_ratio, :timepoint, :population, :n_analyzed,
                CAST(:raw_result AS jsonb), :evidence_id, 0.99, 'automatic',
                CAST(:metadata AS jsonb), now(), now(), true, 'active', now(), now()
            )
        """),
        {
            **values,
            "id": str(uuid.uuid4()),
            "metadata": json.dumps(
                {"source": "clinicaltrials_gov", "source_fingerprint": fingerprint}
            ),
        },
    )
    return True


async def _upsert_adverse_event(db, *, trial_id: str, evidence_id: str, event: dict) -> bool:
    population = event.get("group", {}).get("title") or event.get("group_id") or ""
    values = {
        "trial_id": trial_id,
        "name": event["term"],
        "seriousness": event["seriousness"],
        "n_events": _integer(event.get("num_events")),
        "n_at_risk": _integer(event.get("num_at_risk")),
        "population": population,
        "evidence_id": evidence_id,
    }
    fingerprint = canonical_value_hash({**values, "raw": event.get("raw")})
    existing = (
        await db.execute(
            text("""
                SELECT id::text, ingestion_metadata->>'source_fingerprint'
                FROM adverse_events
                WHERE trial_id = :trial_id AND lower(event_name) = lower(:name)
                  AND COALESCE(grade, '') = ''
                  AND COALESCE(population, '') = COALESCE(:population, '')
                  AND is_current = true
                FOR UPDATE
            """),
            values,
        )
    ).fetchone()
    if existing and existing[1] == fingerprint:
        return False
    if existing:
        await db.execute(
            text("""
                UPDATE adverse_events SET is_current = false, lifecycle_status = 'superseded',
                    valid_to = now(), system_to = now(), updated_at = now()
                WHERE id = :id
            """),
            {"id": str(existing[0])},
        )
    await db.execute(
        text("""
            INSERT INTO adverse_events (
                id, trial_id, source_type, event_name, seriousness, n_events,
                n_subjects_at_risk, population, source_evidence_id, ingestion_metadata,
                valid_from, system_from, is_current, lifecycle_status, created_at, updated_at
            ) VALUES (
                :id, :trial_id, 'trial', :name, :seriousness, :n_events,
                :n_at_risk, :population, :evidence_id, CAST(:metadata AS jsonb),
                now(), now(), true, 'active', now(), now()
            )
        """),
        {
            **values,
            "id": str(uuid.uuid4()),
            "metadata": json.dumps(
                {
                    "source": "clinicaltrials_gov",
                    "source_fingerprint": fingerprint,
                    "group_id": event.get("group_id"),
                    "num_affected": event.get("num_affected"),
                    "organ_system": event.get("organ_system"),
                    "source_vocabulary": event.get("source_vocabulary"),
                }
            ),
        },
    )
    return True


def _measurements_for_group(outcome: dict, group_id: str | None) -> list[dict]:
    measurements = []
    for outcome_class in outcome.get("classes", []):
        for category in outcome_class.get("categories", []):
            for measurement in category.get("measurements", []):
                if measurement.get("groupId") == group_id:
                    measurements.append(
                        {
                            "class": outcome_class.get("title"),
                            "category": category.get("title"),
                            **measurement,
                        }
                    )
    return measurements


async def persist_clinical_outcomes(
    db,
    *,
    trial_id: str,
    source_document_id: str,
    parsed,
    raw: dict,
) -> dict[str, int]:
    """Persist only literal planned outcomes, posted measures and adverse-event counts."""
    counts = {"endpoints": 0, "results": 0, "adverse_events": 0}
    primary_outcomes = getattr(parsed, "primary_outcomes", [])
    secondary_outcomes = getattr(parsed, "secondary_outcomes", [])
    result_outcomes = getattr(parsed, "result_outcomes", [])
    adverse_events = getattr(parsed, "adverse_events", [])
    protocol_module = raw.get("protocolSection", {}).get("outcomesModule", {})
    posted_endpoint_keys = {
        (
            str(outcome.get("title") or "").casefold(),
            str(outcome.get("type") or "").casefold(),
            outcome.get("timeframe") or "",
        )
        for outcome in result_outcomes
    }
    if primary_outcomes or secondary_outcomes:
        evidence_id = await _evidence_id(
            db,
            source_document_id=source_document_id,
            trial_id=trial_id,
            field="planned_outcomes",
            section="protocolSection.outcomesModule",
            fragment=protocol_module,
        )
        for endpoint_type, outcomes in (
            ("primary", primary_outcomes),
            ("secondary", secondary_outcomes),
        ):
            for outcome in outcomes:
                if not outcome.get("measure"):
                    continue
                if (
                    str(outcome["measure"]).casefold(),
                    endpoint_type,
                    outcome.get("timeframe") or "",
                ) in posted_endpoint_keys:
                    continue
                await _upsert_endpoint(
                    db,
                    trial_id=trial_id,
                    evidence_id=evidence_id,
                    endpoint={
                        "name": outcome["measure"],
                        "type": endpoint_type,
                        "timepoint": outcome.get("timeframe"),
                    },
                )
                counts["endpoints"] += 1

    results_module = raw.get("resultsSection", {}).get("outcomeMeasuresModule", {})
    if result_outcomes:
        evidence_id = await _evidence_id(
            db,
            source_document_id=source_document_id,
            trial_id=trial_id,
            field="posted_outcomes",
            section="resultsSection.outcomeMeasuresModule",
            fragment=results_module,
        )
        for outcome in result_outcomes:
            endpoint_id = await _upsert_endpoint(
                db,
                trial_id=trial_id,
                evidence_id=evidence_id,
                endpoint={
                    "name": outcome["title"],
                    "type": str(outcome.get("type") or "").lower() or None,
                    "timepoint": outcome.get("timeframe"),
                    "unit": outcome.get("units"),
                },
            )
            counts["endpoints"] += 1
            groups = outcome.get("groups") or [{"id": None, "title": None}]
            for group in groups:
                group_id = group.get("id")
                measurements = _measurements_for_group(outcome, group_id)
                if not measurements:
                    continue
                analysis: dict = next(iter(outcome.get("analyses", [])), {})
                result_values = [
                    {
                        "category": item.get("category"),
                        "value": item.get("value"),
                        "spread": item.get("spread"),
                    }
                    for item in measurements
                ]
                param_type = analysis.get("paramType") or outcome.get("param_type")
                param_value = _number(analysis.get("paramValue"))
                inserted = await _upsert_result(
                    db,
                    trial_id=trial_id,
                    endpoint_id=endpoint_id,
                    evidence_id=evidence_id,
                    result={
                        "arm_id": group_id,
                        "arm_label": group.get("title"),
                        "result_value": json.dumps(result_values, ensure_ascii=False),
                        "statistical_measure": param_type,
                        "p_value": _number(analysis.get("pValue")),
                        "ci_lower": _number(analysis.get("ciLowerLimit")),
                        "ci_upper": _number(analysis.get("ciUpperLimit")),
                        "hazard_ratio": (
                            param_value if str(param_type).upper() == "HAZARD RATIO" else None
                        ),
                        "odds_ratio": (
                            param_value if str(param_type).upper() == "ODDS RATIO" else None
                        ),
                        "timepoint": outcome.get("timeframe"),
                        "population": outcome.get("population") or "",
                        "n_analyzed": next(
                            (
                                _integer(item.get("numParticipants"))
                                for item in measurements
                                if item.get("numParticipants") is not None
                            ),
                            None,
                        ),
                        "raw_result": {
                            "measurements": measurements,
                            "analyses": outcome.get("analyses", []),
                            "denoms": outcome.get("denoms", []),
                        },
                    },
                )
                counts["results"] += int(inserted)

    adverse_module = raw.get("resultsSection", {}).get("adverseEventsModule", {})
    if adverse_events:
        evidence_id = await _evidence_id(
            db,
            source_document_id=source_document_id,
            trial_id=trial_id,
            field="adverse_events",
            section="resultsSection.adverseEventsModule",
            fragment=adverse_module,
        )
        for event in adverse_events:
            inserted = await _upsert_adverse_event(
                db, trial_id=trial_id, evidence_id=evidence_id, event=event
            )
            counts["adverse_events"] += int(inserted)
    return counts
