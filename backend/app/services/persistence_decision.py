"""Deterministic pre-persistence decisions for canonical biomedical data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

RULE_SET_VERSION = "2026-06-20.1"


class PersistenceAction(StrEnum):
    INSERT = "insert"
    REPLACE = "replace"
    ENRICH = "enrich"
    NOOP = "noop"
    REJECT = "reject"
    SUPERSEDE = "supersede"
    ARCHIVE = "archive"
    CONFLICT = "conflict"
    QUARANTINE = "quarantine"


@dataclass(frozen=True)
class AssertionCandidate:
    value: Any
    value_hash: str
    source_updated_at: datetime | None
    authority_score: float
    confidence_score: float
    evidence_present: bool
    is_partial: bool = False


@dataclass(frozen=True)
class CurrentAssertion:
    value: Any
    value_hash: str
    source_updated_at: datetime | None
    authority_score: float


@dataclass(frozen=True)
class PersistenceDecision:
    action: PersistenceAction
    reason_code: str
    rule_set_version: str = RULE_SET_VERSION


class PersistenceDecisionEngine:
    """Pure policy engine. It never writes to the database or calls an LLM."""

    def decide(
        self,
        candidate: AssertionCandidate,
        current: CurrentAssertion | None,
        *,
        required: bool = False,
        critical: bool = True,
    ) -> PersistenceDecision:
        if required and candidate.value in (None, "", [], {}):
            return PersistenceDecision(PersistenceAction.REJECT, "required_value_missing")
        if critical and not candidate.evidence_present:
            return PersistenceDecision(PersistenceAction.QUARANTINE, "critical_evidence_missing")
        if not 0 <= candidate.confidence_score <= 1:
            return PersistenceDecision(PersistenceAction.REJECT, "confidence_out_of_range")
        if candidate.confidence_score < 0.6:
            return PersistenceDecision(PersistenceAction.QUARANTINE, "confidence_below_threshold")
        if current is None:
            return PersistenceDecision(PersistenceAction.INSERT, "no_current_assertion")
        if candidate.value_hash == current.value_hash:
            return PersistenceDecision(PersistenceAction.NOOP, "same_canonical_value")

        if candidate.source_updated_at and current.source_updated_at:
            if candidate.source_updated_at < current.source_updated_at:
                return PersistenceDecision(PersistenceAction.ARCHIVE, "source_version_older")
            if candidate.source_updated_at > current.source_updated_at:
                return PersistenceDecision(PersistenceAction.REPLACE, "source_version_newer")

        authority_delta = candidate.authority_score - current.authority_score
        if authority_delta >= 0.15:
            return PersistenceDecision(PersistenceAction.REPLACE, "higher_source_authority")
        if authority_delta <= -0.15:
            return PersistenceDecision(PersistenceAction.CONFLICT, "lower_authority_disagrees")
        if candidate.is_partial:
            return PersistenceDecision(PersistenceAction.ENRICH, "partial_non_destructive_update")
        return PersistenceDecision(PersistenceAction.CONFLICT, "peer_sources_disagree")
