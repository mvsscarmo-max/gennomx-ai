"""Auditable propose/review workflow for non-destructive factual corrections."""

import hashlib
import json
import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError


class CorrectionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def propose(
        self,
        *,
        entity_type: str,
        entity_id: str,
        field_path: str,
        granularity_key: str,
        proposed_value: Any,
        reason: str,
        requested_by: str,
        evidence_snippet_id: str | None,
    ) -> dict:
        current = (
            await self.db.execute(
                text("""
                    SELECT id::text FROM field_assertions
                    WHERE entity_type = :entity_type AND entity_id = :entity_id
                      AND field_path = :field_path AND granularity_key = :granularity_key
                      AND is_current = true
                """),
                {
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "field_path": field_path,
                    "granularity_key": granularity_key,
                },
            )
        ).first()
        correction_id = str(uuid.uuid4())
        await self.db.execute(
            text("""
                INSERT INTO manual_corrections (
                    id, entity_type, entity_id, field_path, granularity_key,
                    previous_assertion_id, proposed_value, reason, evidence_snippet_id,
                    requested_by, review_status, created_at, updated_at
                ) VALUES (
                    :id, :entity_type, :entity_id, :field_path, :granularity_key,
                    :previous_assertion_id, CAST(:proposed_value AS JSONB), :reason,
                    :evidence_snippet_id, :requested_by, 'pending', now(), now()
                )
            """),
            {
                "id": correction_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "field_path": field_path,
                "granularity_key": granularity_key,
                "previous_assertion_id": str(current[0]) if current else None,
                "proposed_value": json.dumps(proposed_value, default=str),
                "reason": reason,
                "evidence_snippet_id": evidence_snippet_id,
                "requested_by": requested_by,
            },
        )
        return {"id": correction_id, "review_status": "pending"}

    async def review(
        self, *, correction_id: str, approve: bool, reviewer: str, decision_reason: str
    ) -> dict:
        correction = (
            (
                await self.db.execute(
                    text("""
                    SELECT id::text, entity_type, entity_id::text, field_path,
                           COALESCE(granularity_key, 'entity') AS granularity_key,
                           proposed_value, previous_assertion_id::text, evidence_snippet_id::text,
                           requested_by
                    FROM manual_corrections
                    WHERE id = :id AND review_status = 'pending'
                    FOR UPDATE
                """),
                    {"id": correction_id},
                )
            )
            .mappings()
            .first()
        )
        if not correction:
            raise NotFoundError("Pending correction", correction_id)
        if correction["requested_by"] == reviewer:
            raise AuthorizationError(
                "Reviewer must be different from the correction requester (four-eyes principle)"
            )
        status = "approved" if approve else "rejected"
        resulting_assertion_id = None
        if approve:
            if not correction["evidence_snippet_id"]:
                raise ValidationError("Approved corrections require an evidence snippet")
            previous_id = correction["previous_assertion_id"]
            if previous_id:
                await self.db.execute(
                    text("""
                        UPDATE field_assertions
                        SET is_current = false, lifecycle_status = 'superseded',
                            valid_to = now(), system_to = now(), updated_at = now()
                        WHERE id = :id AND is_current = true
                    """),
                    {"id": previous_id},
                )
            value = correction["proposed_value"]
            value_hash = hashlib.sha256(
                json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
            ).hexdigest()
            resulting_assertion_id = str(uuid.uuid4())
            await self.db.execute(
                text("""
                    INSERT INTO field_assertions (
                        id, entity_type, entity_id, field_path, granularity_key,
                        value_json, value_hash, evidence_snippet_id, observed_at,
                        valid_from, system_from, is_current, lifecycle_status, update_type,
                        supersedes_assertion_id, replacement_reason, extraction_method,
                        rule_set_version, authority_score, confidence_score, relevance_score,
                        freshness_score, completeness_score, data_class, priority,
                        evidence_maturity, validation_status, review_status,
                        created_at, updated_at
                    ) VALUES (
                        :id, :entity_type, :entity_id, :field_path, :granularity_key,
                        CAST(:value_json AS JSONB), :value_hash, :evidence_snippet_id, now(),
                        now(), now(), true, 'active', 'manual_correction',
                        :previous_assertion_id, :replacement_reason, 'human_review',
                        '2026-06-21.1', 1.0, 1.0, 1.0, 1.0, 1.0,
                        'curated', 100, 'human_verified', 'confirmed', 'reviewed',
                        now(), now()
                    )
                """),
                {
                    "id": resulting_assertion_id,
                    "entity_type": correction["entity_type"],
                    "entity_id": correction["entity_id"],
                    "field_path": correction["field_path"],
                    "granularity_key": correction["granularity_key"],
                    "value_json": json.dumps(value, default=str),
                    "value_hash": value_hash,
                    "evidence_snippet_id": correction["evidence_snippet_id"],
                    "previous_assertion_id": previous_id,
                    "replacement_reason": decision_reason,
                },
            )
        await self.db.execute(
            text("""
                UPDATE manual_corrections
                SET review_status = :status, reviewed_by = :reviewer,
                    reviewed_at = now(), decision_reason = :decision_reason,
                    resulting_assertion_id = :resulting_assertion_id, updated_at = now()
                WHERE id = :id
            """),
            {
                "id": correction_id,
                "status": status,
                "reviewer": reviewer,
                "decision_reason": decision_reason,
                "resulting_assertion_id": resulting_assertion_id,
            },
        )
        return {
            "id": correction_id,
            "review_status": status,
            "resulting_assertion_id": resulting_assertion_id,
        }
