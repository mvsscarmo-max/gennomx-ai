"""Generic, deterministic pre-write persistence for governed field assertions."""

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.data_policy import get_field_policy
from app.services.persistence_decision import (
    AssertionCandidate,
    CurrentAssertion,
    PersistenceAction,
    PersistenceDecisionEngine,
)


@dataclass(frozen=True)
class GovernedCandidate:
    entity_type: str
    entity_id: str
    field_path: str
    value: Any
    dimensions: dict[str, Any]
    source_document_id: str | None
    evidence_snippet_id: str | None
    source_record_id: str | None
    source_version: str | None
    source_updated_at: datetime | None
    extraction_method: str
    confidence_score: float
    authority_score: float | None = None
    relevance_score: float | None = None
    freshness_score: float | None = None
    completeness_score: float | None = None
    source_type: str | None = None
    evidence_maturity: str = "unclassified"
    novelty_score: float | None = None
    clinical_impact_score: float | None = None
    validation_status: str = "unvalidated"
    priority: int = 50
    is_partial: bool = False


@dataclass(frozen=True)
class PersistenceOutcome:
    action: PersistenceAction
    reason_code: str
    assertion_id: str | None = None
    conflict_id: str | None = None


class AssertionService:
    RULE_SET_VERSION = "2026-06-21.1"

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.engine = PersistenceDecisionEngine()

    async def persist(self, candidate: GovernedCandidate) -> PersistenceOutcome:
        policy = get_field_policy(candidate.entity_type, candidate.field_path)
        granularity_key = policy.granularity_key(candidate.dimensions)
        value_hash = hashlib.sha256(
            json.dumps(candidate.value, sort_keys=True, separators=(",", ":"), default=str).encode()
        ).hexdigest()
        current_row = (
            (
                await self.db.execute(
                    text("""
                    SELECT id::text, value_json, value_hash, source_updated_at,
                           authority_score, confidence_score
                    FROM field_assertions
                    WHERE entity_type = :entity_type AND entity_id = :entity_id
                      AND field_path = :field_path AND granularity_key = :granularity_key
                      AND is_current = true
                    FOR UPDATE
                """),
                    {
                        "entity_type": candidate.entity_type,
                        "entity_id": candidate.entity_id,
                        "field_path": candidate.field_path,
                        "granularity_key": granularity_key,
                    },
                )
            )
            .mappings()
            .first()
        )
        current = None
        if current_row:
            current = CurrentAssertion(
                value=current_row["value_json"],
                value_hash=current_row["value_hash"],
                source_updated_at=current_row["source_updated_at"],
                authority_score=current_row["authority_score"] or 0,
            )
        authority = (
            candidate.authority_score
            if candidate.authority_score is not None
            else policy.default_authority
        )
        decision = self.engine.decide(
            AssertionCandidate(
                value=candidate.value,
                value_hash=value_hash,
                source_updated_at=candidate.source_updated_at,
                authority_score=authority,
                confidence_score=candidate.confidence_score,
                evidence_present=bool(candidate.evidence_snippet_id),
                is_partial=candidate.is_partial,
            ),
            current,
            required=policy.required,
            critical=policy.critical,
        )
        if decision.action in {PersistenceAction.NOOP, PersistenceAction.REJECT}:
            return PersistenceOutcome(decision.action, decision.reason_code)

        persisted_value = candidate.value
        if decision.action is PersistenceAction.ENRICH and current is not None:
            persisted_value = _merge_non_destructive(current.value, candidate.value)
            value_hash = hashlib.sha256(
                json.dumps(
                    persisted_value, sort_keys=True, separators=(",", ":"), default=str
                ).encode()
            ).hexdigest()

        assertion_id = str(uuid.uuid4())
        lifecycle = {
            PersistenceAction.ARCHIVE: "archived",
            PersistenceAction.CONFLICT: "disputed",
            PersistenceAction.QUARANTINE: "quarantine",
        }.get(decision.action, "active")
        is_current = decision.action in {
            PersistenceAction.INSERT,
            PersistenceAction.REPLACE,
            PersistenceAction.ENRICH,
        }
        previous_id = current_row["id"] if current_row else None
        if previous_id and is_current:
            await self.db.execute(
                text("""
                    UPDATE field_assertions
                    SET is_current = false, lifecycle_status = 'superseded',
                        valid_to = now(), system_to = now(), updated_at = now()
                    WHERE id = :id AND is_current = true
                """),
                {"id": previous_id},
            )

        observed_at = datetime.now(UTC)
        await self.db.execute(
            text("""
                INSERT INTO field_assertions (
                    id, entity_type, entity_id, field_path, granularity_key,
                    value_json, value_hash, source_document_id, evidence_snippet_id,
                    source_record_id, source_version, source_updated_at, observed_at,
                    valid_from, system_from, is_current, lifecycle_status, update_type,
                    supersedes_assertion_id, replacement_reason, extraction_method,
                    rule_set_version, authority_score, confidence_score, relevance_score,
                    freshness_score, completeness_score, data_class, source_type, priority,
                    evidence_maturity, novelty_score, clinical_impact_score,
                    validation_status, expires_at, archived_at, created_at, updated_at
                ) VALUES (
                    :id, :entity_type, :entity_id, :field_path, :granularity_key,
                    CAST(:value_json AS JSONB), :value_hash, :source_document_id,
                    :evidence_snippet_id, :source_record_id, :source_version,
                    :source_updated_at, :observed_at, :valid_from, now(), :is_current,
                    :lifecycle_status, :update_type, :supersedes_assertion_id,
                    :replacement_reason, :extraction_method, :rule_set_version,
                    :authority_score, :confidence_score, :relevance_score,
                    :freshness_score, :completeness_score, :data_class, :source_type,
                    :priority, :evidence_maturity, :novelty_score, :clinical_impact_score,
                    :validation_status, :expires_at, :archived_at, now(), now()
                )
            """),
            {
                "id": assertion_id,
                "entity_type": candidate.entity_type,
                "entity_id": candidate.entity_id,
                "field_path": candidate.field_path,
                "granularity_key": granularity_key,
                "value_json": json.dumps(persisted_value, default=str),
                "value_hash": value_hash,
                "source_document_id": candidate.source_document_id,
                "evidence_snippet_id": candidate.evidence_snippet_id,
                "source_record_id": candidate.source_record_id,
                "source_version": candidate.source_version,
                "source_updated_at": candidate.source_updated_at,
                "observed_at": observed_at,
                "valid_from": candidate.source_updated_at or observed_at,
                "is_current": is_current,
                "lifecycle_status": lifecycle,
                "update_type": decision.action.value,
                "supersedes_assertion_id": previous_id if is_current else None,
                "replacement_reason": decision.reason_code,
                "extraction_method": candidate.extraction_method,
                "rule_set_version": self.RULE_SET_VERSION,
                "authority_score": authority,
                "confidence_score": candidate.confidence_score,
                "relevance_score": candidate.relevance_score,
                "freshness_score": candidate.freshness_score,
                "completeness_score": candidate.completeness_score,
                "data_class": policy.data_class,
                "source_type": candidate.source_type,
                "priority": candidate.priority,
                "evidence_maturity": candidate.evidence_maturity,
                "novelty_score": candidate.novelty_score,
                "clinical_impact_score": candidate.clinical_impact_score,
                "validation_status": candidate.validation_status,
                "expires_at": policy.expires_at(observed_at),
                "archived_at": observed_at if lifecycle == "archived" else None,
            },
        )
        conflict_id = None
        if decision.action is PersistenceAction.CONFLICT:
            conflict_id = str(uuid.uuid4())
            await self.db.execute(
                text("""
                    INSERT INTO data_conflicts (
                        id, entity_type, entity_id, field_path, current_assertion_id,
                        candidate_assertion_id, conflict_type, severity, status,
                        resolution_reason, created_at, updated_at
                    ) VALUES (
                        :id, :entity_type, :entity_id, :field_path, :current_id,
                        :candidate_id, :conflict_type, 'high', 'open', :reason,
                        now(), now()
                    )
                """),
                {
                    "id": conflict_id,
                    "entity_type": candidate.entity_type,
                    "entity_id": candidate.entity_id,
                    "field_path": candidate.field_path,
                    "current_id": previous_id,
                    "candidate_id": assertion_id,
                    "conflict_type": decision.reason_code,
                    "reason": "deterministic_prewrite_policy",
                },
            )
        return PersistenceOutcome(decision.action, decision.reason_code, assertion_id, conflict_id)


def _merge_non_destructive(current: Any, candidate: Any) -> Any:
    if isinstance(current, dict) and isinstance(candidate, dict):
        return {**current, **{key: value for key, value in candidate.items() if value is not None}}
    if isinstance(current, list) and isinstance(candidate, list):
        merged = list(current)
        for value in candidate:
            if value not in merged:
                merged.append(value)
        return merged
    raise ValueError("partial_enrichment_requires_object_or_list")
