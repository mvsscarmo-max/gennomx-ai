from datetime import UTC, datetime, timedelta

import pytest

from app.services.persistence_decision import (
    AssertionCandidate,
    CurrentAssertion,
    PersistenceAction,
    PersistenceDecisionEngine,
)

NOW = datetime(2026, 6, 20, tzinfo=UTC)


def candidate(*, value_hash="new", updated=NOW, authority=1.0, confidence=0.99, evidence=True):
    return AssertionCandidate("new", value_hash, updated, authority, confidence, evidence)


def current(*, value_hash="old", updated=NOW - timedelta(days=1), authority=1.0):
    return CurrentAssertion("old", value_hash, updated, authority)


@pytest.mark.unit
def test_newer_source_version_replaces_current():
    result = PersistenceDecisionEngine().decide(candidate(), current())
    assert result.action == PersistenceAction.REPLACE
    assert result.reason_code == "source_version_newer"


@pytest.mark.unit
def test_late_payload_is_archived_without_regression():
    result = PersistenceDecisionEngine().decide(
        candidate(updated=NOW - timedelta(days=2)), current(updated=NOW)
    )
    assert result.action == PersistenceAction.ARCHIVE


@pytest.mark.unit
def test_same_hash_is_idempotent_noop():
    assert (
        PersistenceDecisionEngine()
        .decide(candidate(value_hash="same"), current(value_hash="same"))
        .action
        == PersistenceAction.NOOP
    )


@pytest.mark.unit
def test_peer_source_disagreement_opens_conflict():
    result = PersistenceDecisionEngine().decide(
        candidate(updated=None, authority=0.9), current(updated=None, authority=0.9)
    )
    assert result.action == PersistenceAction.CONFLICT


@pytest.mark.unit
def test_critical_fact_without_evidence_is_quarantined():
    assert PersistenceDecisionEngine().decide(candidate(evidence=False), None).action == (
        PersistenceAction.QUARANTINE
    )
