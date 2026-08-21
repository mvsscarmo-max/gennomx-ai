"""Filesystem reference implementation for VLAEG coordination Profiles 0-2."""
from __future__ import annotations

import json
import hashlib
import os
import re
import subprocess
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

from capture_policy import require_redaction_patterns, redact_text, redact_value

from .errors import CoordinationError
from .provider import invoke_operation
from .schema_validation import SchemaValidator

MODES = {"disabled", "single-agent", "shared-files"}
ID_PREFIXES = {
    "agents": "AGENT",
    "messages": "MSG",
    "threads": "THREAD",
    "claims": "CLAIM",
    "conflicts": "CONFLICT",
    "work": "WORK",
    "handoffs": "HANDOFF",
}
MESSAGE_TYPES = {
    "inform", "request", "response", "proposal", "decision-required",
    "approval-required", "warning", "conflict", "blocker", "handoff",
    "review-request", "review-result", "task-completed",
}
PRIORITIES = {"low", "normal", "high", "critical"}
CLAIM_TYPES = {
    "task", "workstream", "module", "directory", "file", "symbol",
    "contract", "migration", "integration",
}
CLAIM_MODES = {"read", "write", "exclusive"}
AGENT_STATUSES = {
    "starting", "available", "assigned", "working", "waiting", "blocked",
    "reviewing", "paused", "disconnected", "completed", "failed",
}
HARNESSES = {"claude-code", "codex", "opencode", "cursor", "cursor-agent", "other"}
CAPABILITY_STATUS = {
    "supported": [
        "agent_registration", "capability_discovery", "structured_messages",
        "acknowledgements", "mailbox_polling", "presence_heartbeat", "work_lifecycle",
        "scope_claims", "conflict_reporting", "handoffs",
    ],
    "partially_supported": [],
    "emulated": ["task_claims"],
    "unsupported": [
        "persistent_sessions", "shared_state", "approvals", "reviews",
        "evidence_submission", "lifecycle_hooks", "mcp_tools", "live_session_injection",
        "forced_interruption", "worktree_provisioning",
    ],
    "unverified": [],
}
LOCK_TIMEOUT_SECONDS = 2.0
LOCK_POLL_SECONDS = 0.01


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_time(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CoordinationError("invalid-envelope", f"invalid timestamp: {value}") from exc


class FilesystemProvider:
    SUPPORTED_OPERATIONS = {
        "coord.register_agent": "register_agent",
        "coord.unregister_agent": "unregister_agent",
        "coord.get_agent": "get_agent",
        "coord.list_agents": "list_agents",
        "coord.discover_capabilities": "discover_capabilities",
        "coord.update_agent_status": "heartbeat",
        "coord.heartbeat": "heartbeat",
        "coord.get_presence": "get_presence",
        "coord.list_presence": "list_presence",
        "coord.open_thread": "open_thread",
        "coord.send_message": "send_message",
        "coord.read_messages": "read_messages",
        "coord.ack_message": "acknowledge",
        "coord.close_thread": "close_thread",
        "coord.create_work": "create_work",
        "coord.update_work": "update_work",
        "coord.claim_scope": "claim_scope",
        "coord.release_scope": "release_claim",
        "coord.list_claims": "list_claims",
        "coord.report_conflict": "report_conflict",
        "coord.resolve_conflict": "resolve_conflict",
        "coord.get_runtime_state": "get_runtime_state",
        "coord.create_handoff": "create_handoff",
        "coord.audit": "audit",
    }

    def __init__(
        self,
        project_root: Path,
        runtime_root: Path | None = None,
        *,
        lock_timeout_seconds: float = LOCK_TIMEOUT_SECONDS,
    ) -> None:
        if lock_timeout_seconds < 0:
            raise ValueError("lock_timeout_seconds cannot be negative")
        self.project_root = project_root.resolve()
        self.runtime_root = (runtime_root or self.project_root / ".coordination").resolve()
        self.store = self.runtime_root / "stores"
        self.config_path = self.runtime_root / "config.json"
        self.owner_path = self.runtime_root / "owner.json"
        self.lock_path = self.runtime_root / ".write-lock"
        self.lock_timeout_seconds = lock_timeout_seconds
        self.redaction_patterns = require_redaction_patterns(self.project_root)
        self.schemas = SchemaValidator(self.project_root / ".agents" / "coordination" / "schemas")
        self.project_fingerprint = hashlib.sha256(
            os.path.normcase(str(self.project_root)).encode("utf-8")
        ).hexdigest()

    def invoke(self, operation: str, payload: dict[str, Any]) -> Any:
        return invoke_operation(self, operation, payload)

    def initialize(self, mode: str, project_id: str = "PROJECT-LOCAL") -> dict[str, Any]:
        if mode not in MODES:
            raise CoordinationError("invalid-envelope", f"unsupported mode: {mode}")
        project_id = self._structural_text(project_id, 120, "project_id")
        with self._locked():
            self._mkdir(self.store)
            self._ensure_store()
            if self.owner_path.is_file():
                owner = self._read_json(self.owner_path)
                if owner.get("project_fingerprint") != self.project_fingerprint:
                    raise CoordinationError("runtime-conflict", "runtime belongs to another project root")
            elif any(any((self.store / kind).glob("*.json")) for kind in ID_PREFIXES):
                raise CoordinationError("runtime-conflict", "cannot adopt an orphaned runtime with records")
            else:
                self._write_json(self.owner_path, {"project_fingerprint": self.project_fingerprint})
            if self.config_path.exists():
                existing = self._read_json(self.config_path)
                if (existing.get("mode") != mode or existing.get("project_id") != project_id
                        or existing.get("project_fingerprint") != self.project_fingerprint):
                    raise CoordinationError(
                        "runtime-conflict",
                        "runtime is already initialized for a different project or mode",
                    )
                self._repair_counters()
                return existing
            config = {
                "contract_version": "1",
                "provider": "filesystem",
                "mode": mode,
                "enabled": mode != "disabled",
                "project_id": project_id,
                "project_fingerprint": self.project_fingerprint,
                "sandbox": {"enabled": False, "required": False},
                "created_at": utc_now(),
            }
            self._repair_counters()
            self._write_json(self.config_path, config)
        return config

    def register_agent(
        self,
        display_name: str,
        harness: str,
        *,
        workstream_id: str | None = None,
        task_id: str | None = None,
        branch: str | None = None,
        worktree: str | None = None,
        capabilities: list[str] | None = None,
    ) -> dict[str, Any]:
        config = self._require("agent_registration")
        display_name = self._free_text(display_name, 120)
        harness = self._structural_text(harness, 40, "harness")
        if harness not in HARNESSES:
            raise CoordinationError("invalid-envelope", f"unsupported harness: {harness}")
        branch = self._optional_structural_text(branch, 500, "branch")
        worktree = self._optional_structural_text(worktree, 1000, "worktree")
        capabilities = [self._structural_text(item, 120, "capability") for item in capabilities or []]
        if task_id and not workstream_id:
            raise CoordinationError("invalid-envelope", "task_id requires workstream_id")
        if workstream_id:
            self._require_canonical_work(workstream_id, task_id)
        with self._locked():
            agents = self._list("agents")
            active_agents = [agent for agent in agents if agent["status"] not in {"disconnected", "completed", "failed"}]
            if config["mode"] == "single-agent" and active_agents:
                raise CoordinationError("capability-not-enabled", "single-agent mode already has an agent")
            agent_id = self._allocate("agents")
            now = utc_now()
            record = {
                "agent_id": agent_id,
                "display_name": display_name,
                "harness": harness,
                "provider": "filesystem",
                "provider_agent_id": None,
                "session_id": None,
                "project_id": config["project_id"],
                "workstream_id": workstream_id,
                "task_id": task_id,
                "branch": branch,
                "worktree": worktree,
                "capabilities": sorted(set(capabilities)),
                "status": "available",
                "registered_at": now,
                "last_seen_at": now,
                "metadata": {},
            }
            self._write_record("agents", agent_id, record)
            return record

    def list_agents(self) -> list[dict[str, Any]]:
        self._require("agent_registration")
        return self._list("agents")

    def get_agent(self, agent_id: str) -> dict[str, Any]:
        self._require("agent_registration")
        return self._read_record("agents", agent_id)

    def unregister_agent(self, agent_id: str) -> dict[str, Any]:
        self._require("agent_registration")
        with self._locked():
            agent = self._read_record("agents", agent_id)
            if any(item["agent_id"] == agent_id and item["status"] == "active" for item in self._active_claims()):
                raise CoordinationError("claim-conflict", "release active claims before unregistering")
            agent["status"] = "disconnected"
            agent["last_seen_at"] = utc_now()
            self._write_record("agents", agent_id, agent)
            return agent

    def discover_capabilities(self) -> dict[str, list[str]]:
        self._config()
        return {status: list(values) for status, values in CAPABILITY_STATUS.items()}

    def heartbeat(self, agent_id: str, status: str = "available") -> dict[str, Any]:
        self._require("presence_heartbeat")
        if status not in AGENT_STATUSES:
            raise CoordinationError("invalid-envelope", f"unsupported agent status: {status}")
        with self._locked():
            agent = self._read_record("agents", agent_id)
            agent["status"] = status
            agent["last_seen_at"] = utc_now()
            self._write_record("agents", agent_id, agent)
            return agent

    def get_presence(self, agent_id: str) -> dict[str, Any]:
        agent = self.get_agent(agent_id)
        return self._presence(agent)

    def list_presence(self) -> list[dict[str, Any]]:
        return [self._presence(agent) for agent in self.list_agents()]

    def send_message(
        self,
        from_agent: str,
        to_agents: list[str],
        message_type: str,
        subject: str,
        body: str,
        *,
        priority: str = "normal",
        requires_ack: bool = False,
        workstream_id: str | None = None,
        task_id: str | None = None,
        thread_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        config = self._require("structured_messages")
        if message_type not in MESSAGE_TYPES or priority not in PRIORITIES or not to_agents:
            raise CoordinationError("invalid-envelope", "invalid message type, priority or recipients")
        subject = self._free_text(subject, 200)
        body = self._free_text(body, 16000, allow_empty=True)
        idempotency_key = self._optional_structural_text(idempotency_key, 200, "idempotency_key")
        if task_id and not workstream_id:
            raise CoordinationError("invalid-envelope", "task_id requires workstream_id")
        if workstream_id:
            self._require_canonical_work(workstream_id, task_id)
        with self._locked():
            self._read_record("agents", from_agent)
            for recipient in set(to_agents):
                self._read_record("agents", recipient)
            fingerprint = self._message_fingerprint(
                from_agent, to_agents, message_type, subject, body, priority,
                requires_ack, workstream_id, task_id, thread_id,
            )
            if idempotency_key:
                existing = self._idempotent_message(idempotency_key, fingerprint)
                if existing:
                    return existing
            message_id = self._allocate("messages")
            if thread_id is None:
                thread = self._open_thread_locked(from_agent, subject, workstream_id, task_id)
                thread_id = thread["thread_id"]
            else:
                thread = self._read_record("threads", thread_id)
                if thread["status"] != "open":
                    raise CoordinationError("invalid-envelope", f"thread is closed: {thread_id}")
            record = {
                "message_id": message_id,
                "thread_id": thread_id,
                "project_id": config["project_id"],
                "workstream_id": workstream_id,
                "task_id": task_id,
                "from": from_agent,
                "to": sorted(set(to_agents)),
                "type": message_type,
                "priority": priority,
                "subject": subject,
                "body": body,
                "created_at": utc_now(),
                "requires_ack": requires_ack or priority == "critical",
                "ack_deadline": None,
                "provider_reference": None,
                "related_artifacts": [],
                "metadata": {},
            }
            if idempotency_key:
                self._write_idempotency(idempotency_key, fingerprint, record, "pending")
            self._write_record("messages", message_id, record)
            if idempotency_key:
                self._write_idempotency(idempotency_key, fingerprint, record, "committed")
            return record

    def open_thread(
        self,
        created_by: str,
        subject: str,
        *,
        workstream_id: str | None = None,
        task_id: str | None = None,
    ) -> dict[str, Any]:
        self._require("structured_messages")
        subject = self._free_text(subject, 200)
        if task_id and not workstream_id:
            raise CoordinationError("invalid-envelope", "task_id requires workstream_id")
        if workstream_id:
            self._require_canonical_work(workstream_id, task_id)
        with self._locked():
            self._read_record("agents", created_by)
            return self._open_thread_locked(created_by, subject, workstream_id, task_id)

    def close_thread(self, thread_id: str, closed_by: str) -> dict[str, Any]:
        self._require("structured_messages")
        with self._locked():
            self._read_record("agents", closed_by)
            thread = self._read_record("threads", thread_id)
            if thread["status"] == "open":
                thread["status"] = "closed"
                thread["closed_at"] = utc_now()
                thread["closed_by"] = closed_by
                self._write_record("threads", thread_id, thread)
            return thread

    def read_messages(self, agent_id: str, *, unacknowledged_only: bool = False) -> list[dict[str, Any]]:
        self._require("structured_messages")
        self._read_record("agents", agent_id)
        result = []
        for message in self._list("messages"):
            if agent_id not in message["to"]:
                continue
            if unacknowledged_only and self._valid_ack(message["message_id"], agent_id):
                continue
            result.append(message)
        return result

    def acknowledge(self, message_id: str, agent_id: str, status: str = "received") -> dict[str, Any]:
        self._require("acknowledgements")
        if status not in {"received", "accepted", "rejected"}:
            raise CoordinationError("invalid-envelope", f"invalid acknowledgment status: {status}")
        with self._locked():
            message = self._read_record("messages", message_id)
            if agent_id not in message["to"]:
                raise CoordinationError("unknown-reference", "agent is not a message recipient", reference=agent_id)
            path = self._ack_path(message_id, agent_id)
            if path.exists():
                return self._read_ack(message_id, agent_id)
            record = {
                "message_id": message_id,
                "agent_id": agent_id,
                "acknowledged_at": utc_now(),
                "status": status,
                "detail": None,
                "provider_reference": None,
            }
            self.schemas.validate("acknowledgment", record)
            self._write_json(path, record)
            return record

    def create_work(self, workstream_id: str, task_id: str, summary: str = "") -> dict[str, Any]:
        config = self._require("work_lifecycle")
        self._require_canonical_work(workstream_id, task_id)
        summary = self._free_text(summary, 1000, allow_empty=True)
        with self._locked():
            work_id = self._allocate("work")
            now = utc_now()
            record = {
                "work_id": work_id,
                "project_id": config["project_id"],
                "workstream_id": workstream_id,
                "task_id": task_id,
                "assigned_to": None,
                "status": "created",
                "progress": 0,
                "summary": summary,
                "created_at": now,
                "updated_at": now,
                "updated_by": None,
                "provider_reference": None,
                "metadata": {},
            }
            self._write_record("work", work_id, record)
            return record

    def update_work(
        self,
        work_id: str,
        status: str,
        *,
        actor_id: str,
        progress: int | None = None,
    ) -> dict[str, Any]:
        self._require("work_lifecycle")
        allowed = {"created", "assigned", "accepted", "working", "needs_input", "completed", "failed", "cancelled"}
        if status not in allowed or progress is not None and not 0 <= progress <= 100:
            raise CoordinationError("invalid-envelope", "invalid work status or progress")
        transitions = {
            "created": {"assigned", "cancelled"},
            "assigned": {"accepted", "cancelled"},
            "accepted": {"working", "cancelled"},
            "working": {"needs_input", "completed", "failed", "cancelled"},
            "needs_input": {"working", "failed", "cancelled"},
            "completed": set(),
            "failed": set(),
            "cancelled": set(),
        }
        with self._locked():
            work = self._read_record("work", work_id)
            actor = self._read_record("agents", actor_id)
            if actor["status"] in {"disconnected", "completed", "failed"}:
                raise CoordinationError("unknown-reference", "work actor is not active")
            if (actor.get("workstream_id"), actor.get("task_id")) != (work["workstream_id"], work["task_id"]):
                raise CoordinationError("unknown-reference", "work actor is registered for another task")
            if status not in transitions[work["status"]]:
                raise CoordinationError(
                    "invalid-envelope",
                    f"invalid work transition: {work['status']} -> {status}",
                )
            if work["status"] == "created" and status == "assigned":
                work["assigned_to"] = actor_id
            elif work["assigned_to"] not in {None, actor_id}:
                raise CoordinationError("unknown-reference", "only the assigned agent may update work")
            if progress is not None and progress < work["progress"]:
                raise CoordinationError("invalid-envelope", "work progress cannot decrease")
            work["status"] = status
            if progress is not None:
                work["progress"] = progress
            elif status == "completed":
                work["progress"] = 100
            work["updated_at"] = utc_now()
            work["updated_by"] = actor_id
            self._write_record("work", work_id, work)
            return work

    def claim_scope(
        self,
        agent_id: str,
        workstream_id: str,
        task_id: str,
        scope_type: str,
        scope_value: str,
        mode: str,
        *,
        ttl_minutes: int = 30,
    ) -> dict[str, Any]:
        self._require("scope_claims")
        if scope_type not in CLAIM_TYPES or mode not in CLAIM_MODES or not 1 <= ttl_minutes <= 1440:
            raise CoordinationError("invalid-envelope", "invalid claim type, mode or TTL")
        scope_value = self._structural_text(scope_value, 1000, "scope_value")
        self._require_canonical_work(workstream_id, task_id)
        with self._locked():
            agent = self._read_record("agents", agent_id)
            if (agent.get("workstream_id"), agent.get("task_id")) != (workstream_id, task_id):
                raise CoordinationError("unknown-reference", "claim actor is registered for another task")
            if mode != "read" and (not agent["branch"] or not agent["worktree"]):
                raise CoordinationError(
                    "worktree-required",
                    "write and exclusive claims require registered branch and worktree coordinates",
                )
            if mode != "read":
                self._verified_worktree(agent)
            active_claims = self._active_claims()
            for existing in active_claims:
                same_scope = existing["scope"] == {"type": scope_type, "value": scope_value}
                conflicts = existing["agent_id"] != agent_id and (mode != "read" or existing["mode"] != "read")
                if same_scope and conflicts:
                    conflict = self._record_claim_conflict(existing, agent_id, workstream_id, scope_type, scope_value)
                    raise CoordinationError(
                        "claim-conflict",
                        f"scope already claimed by {existing['agent_id']}",
                        reference=conflict["conflict_id"],
                    )
                if mode != "read" and existing["mode"] != "read" and existing["agent_id"] != agent_id:
                    owner = self._read_record("agents", existing["agent_id"])
                    if (self._worktree_key(owner.get("worktree")) == self._worktree_key(agent["worktree"])
                            or owner.get("branch") == agent["branch"]):
                        conflict = self._record_claim_conflict(
                            existing, agent_id, workstream_id, scope_type, scope_value,
                            conflict_type="write-conflict",
                            description="parallel write claims share the same worktree",
                        )
                        raise CoordinationError(
                            "claim-conflict",
                            "parallel writes require distinct worktrees",
                            reference=conflict["conflict_id"],
                        )
            now = datetime.now(timezone.utc).replace(microsecond=0)
            claim_id = self._allocate("claims")
            fencing_value = self._next_fencing_token()
            record = {
                "claim_id": claim_id,
                "agent_id": agent_id,
                "workstream_id": workstream_id,
                "task_id": task_id,
                "scope": {"type": scope_type, "value": scope_value},
                "mode": mode,
                "status": "active",
                "fencing_token": fencing_value,
                "created_at": now.isoformat().replace("+00:00", "Z"),
                "expires_at": (now + timedelta(minutes=ttl_minutes)).isoformat().replace("+00:00", "Z"),
                "provider_reference": None,
            }
            self._write_record("claims", claim_id, record)
            return record

    def release_claim(self, claim_id: str, agent_id: str, fencing_token: int) -> dict[str, Any]:
        self._require("scope_claims")
        with self._locked():
            claim = self._read_record("claims", claim_id)
            if claim["agent_id"] != agent_id or claim["fencing_token"] != fencing_token:
                raise CoordinationError("unknown-reference", "claim owner or fencing token does not match")
            if claim["status"] == "active":
                claim["status"] = "released"
                self._write_record("claims", claim_id, claim)
            return claim

    def list_claims(self) -> list[dict[str, Any]]:
        self._require("scope_claims")
        with self._locked():
            self._active_claims()
            return self._list("claims")

    def create_handoff(self, agent_id: str, workstream_id: str, target: str, summary: str) -> dict[str, Any]:
        self._require("handoffs")
        self._read_record("agents", agent_id)
        self._require_canonical_work(workstream_id, None)
        target = self._structural_text(target, 120, "target")
        summary = self._free_text(summary, 4000)
        with self._locked():
            handoff_id = self._allocate("handoffs")
            record = {
                "handoff_id": handoff_id,
                "agent_id": agent_id,
                "workstream_id": workstream_id,
                "target": target,
                "summary": summary,
                "created_at": utc_now(),
                "authority": "operational-state",
            }
            self._write_record("handoffs", handoff_id, record)
            return record

    def report_conflict(
        self,
        workstream_id: str,
        agents: list[str],
        conflict_type: str,
        description: str,
        *,
        severity: str = "high",
        requires_human: bool = False,
        task_id: str | None = None,
    ) -> dict[str, Any]:
        self._require("conflict_reporting")
        self._require_canonical_work(workstream_id, task_id)
        if conflict_type not in {
            "write-conflict", "claim-conflict", "contract-conflict", "decision-conflict",
            "dependency-conflict", "integration-conflict", "priority-conflict", "scope-conflict",
            "provider-conflict",
        } or severity not in {"low", "medium", "high", "critical"} or not agents:
            raise CoordinationError("invalid-envelope", "invalid conflict envelope")
        description = self._free_text(description, 2000)
        with self._locked():
            for agent_id in set(agents):
                agent = self._read_record("agents", agent_id)
                if agent.get("workstream_id") != workstream_id:
                    raise CoordinationError("unknown-reference", "conflict agent is registered elsewhere")
                if task_id and agent.get("task_id") != task_id:
                    raise CoordinationError("unknown-reference", "conflict agent is registered for another task")
            conflict_id = self._allocate("conflicts")
            record = {
                "conflict_id": conflict_id,
                "type": conflict_type,
                "severity": severity,
                "workstream_id": workstream_id,
                "task_id": task_id,
                "agents": sorted(set(agents)),
                "artifacts": [],
                "description": description,
                "status": "open",
                "requires_human": requires_human,
                "resolution": None,
                "provider_reference": None,
                "created_at": utc_now(),
                "resolved_at": None,
            }
            self._write_record("conflicts", conflict_id, record)
            return record

    def resolve_conflict(
        self,
        conflict_id: str,
        resolution: str,
        resolved_by: str,
        *,
        approval_reference: str | None = None,
    ) -> dict[str, Any]:
        self._require("conflict_reporting")
        resolution = self._free_text(resolution, 2000)
        with self._locked():
            conflict = self._read_record("conflicts", conflict_id)
            actor = self._read_record("agents", resolved_by)
            if actor.get("workstream_id") != conflict["workstream_id"]:
                raise CoordinationError("unknown-reference", "conflict actor is registered for another workstream")
            if conflict.get("task_id") and actor.get("task_id") != conflict["task_id"]:
                raise CoordinationError("unknown-reference", "conflict actor is registered for another task")
            if conflict["requires_human"]:
                if not approval_reference:
                    raise CoordinationError("invalid-envelope", "human conflict requires an approved decision")
                self._require_decision(
                    approval_reference,
                    conflict_id=conflict_id,
                    workstream_id=conflict["workstream_id"],
                    resolution=resolution,
                )
            conflict["status"] = "resolved"
            conflict["resolution"] = resolution
            conflict["resolved_by"] = resolved_by
            conflict["approval_reference"] = approval_reference
            conflict["resolved_at"] = utc_now()
            self._write_record("conflicts", conflict_id, conflict)
            return conflict

    def get_runtime_state(self) -> dict[str, Any]:
        config = self._config()
        return {
            "provider": "filesystem",
            "contract_version": config["contract_version"],
            "project_id": config["project_id"],
            "mode": config["mode"],
            "counts": {kind: len(self._list(kind)) for kind in ID_PREFIXES},
        }

    def audit(self) -> dict[str, Any]:
        if not self.config_path.is_file():
            orphaned = any(self.store.glob("*/*.json")) if self.store.is_dir() else False
            issues = ["runtime records exist without config"] if orphaned else []
            return {
                "provider": "filesystem",
                "contract_version": "1",
                "mode": "disabled",
                "initialized": False,
                "counts": {kind: 0 for kind in ID_PREFIXES},
                "issues": issues,
                "ok": not issues,
            }
        config = self._config()
        issues: list[str] = []
        agent_records = self._list("agents")
        agents = {item["agent_id"] for item in agent_records}
        if config["mode"] == "single-agent" and len(agent_records) > 1:
            issues.append("single-agent mode contains multiple agents")
        for agent in agent_records:
            if agent["project_id"] != config["project_id"]:
                issues.append(f"{agent['agent_id']}: project mismatch")
        messages = self._list("messages")
        for message in messages:
            if message["project_id"] != config["project_id"]:
                issues.append(f"{message['message_id']}: project mismatch")
            if message["from"] not in agents:
                issues.append(f"{message['message_id']}: unknown sender")
            for recipient in message["to"]:
                if recipient not in agents:
                    issues.append(f"{message['message_id']}: unknown recipient {recipient}")
                if message["requires_ack"]:
                    try:
                        if not self._valid_ack(message["message_id"], recipient):
                            issues.append(f"{message['message_id']}: missing ack from {recipient}")
                    except CoordinationError:
                        issues.append(f"{message['message_id']}: invalid ack from {recipient}")
        active_writers: dict[str, str] = {}
        active_branches: dict[str, str] = {}
        with self._locked():
            active_claims = self._active_claims()
        for claim in self._list("claims"):
            if claim["agent_id"] not in agents:
                issues.append(f"{claim['claim_id']}: unknown agent")
        for claim in active_claims:
            if claim["mode"] == "read" or claim["agent_id"] not in agents:
                continue
            agent = self._read_record("agents", claim["agent_id"])
            if not agent["branch"] or not agent["worktree"]:
                issues.append(f"{claim['claim_id']}: write claim lacks branch or worktree")
                continue
            try:
                self._verified_worktree(agent)
            except CoordinationError as exc:
                issues.append(f"{claim['claim_id']}: {exc}")
                continue
            key = self._worktree_key(agent["worktree"])
            other = active_writers.get(key)
            if other and other != agent["agent_id"]:
                issues.append(f"{claim['claim_id']}: worktree shared with {other}")
            branch_owner = active_branches.get(agent["branch"])
            if branch_owner and branch_owner != agent["agent_id"]:
                issues.append(f"{claim['claim_id']}: branch shared with {branch_owner}")
            active_writers[key] = agent["agent_id"]
            active_branches[agent["branch"]] = agent["agent_id"]
        for work in self._list("work"):
            if work["project_id"] != config["project_id"]:
                issues.append(f"{work['work_id']}: project mismatch")
        return {
            "provider": "filesystem",
            "contract_version": config["contract_version"],
            "mode": config["mode"],
            "initialized": True,
            "counts": {kind: len(self._list(kind)) for kind in ID_PREFIXES},
            "issues": issues,
            "ok": not issues,
        }

    @contextmanager
    def _locked(self) -> Iterator[None]:
        self._mkdir(self.runtime_root)
        try:
            lock = self.lock_path.open("a+b")
        except OSError as exc:
            raise CoordinationError("filesystem-error", "cannot access coordination lock") from exc
        if os.name == "nt":
            import msvcrt

            try:
                if lock.seek(0, os.SEEK_END) == 0:
                    lock.write(b"\0")
                    lock.flush()
            except OSError as exc:
                lock.close()
                raise CoordinationError("filesystem-error", "cannot prepare coordination lock") from exc
        deadline = time.monotonic() + self.lock_timeout_seconds
        while True:
            try:
                if os.name == "nt":
                    lock.seek(0)
                    msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as exc:
                if time.monotonic() >= deadline:
                    lock.close()
                    raise CoordinationError("coordination-busy", "filesystem provider is locked") from exc
                time.sleep(LOCK_POLL_SECONDS)
        try:
            yield
        finally:
            try:
                if os.name == "nt":
                    lock.seek(0)
                    msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            except OSError as exc:
                raise CoordinationError("filesystem-error", "cannot release coordination lock") from exc
            finally:
                lock.close()

    def _config(self) -> dict[str, Any]:
        if not self.config_path.is_file():
            raise CoordinationError("capability-not-enabled", "coordination runtime is not initialized")
        config = self._read_json(self.config_path)
        owner = self._read_json(self.owner_path) if self.owner_path.is_file() else {}
        if (config.get("project_fingerprint") != self.project_fingerprint
                or owner.get("project_fingerprint") != self.project_fingerprint):
            raise CoordinationError("runtime-conflict", "runtime belongs to another project root")
        return config

    def _require(self, capability: str) -> dict[str, Any]:
        config = self._config()
        mode = config["mode"]
        if mode == "disabled":
            raise CoordinationError("capability-not-enabled", f"{capability} is disabled")
        shared_only = {"structured_messages", "acknowledgements", "scope_claims", "conflict_reporting"}
        if capability in shared_only and mode != "shared-files":
            raise CoordinationError("capability-not-enabled", f"{capability} requires shared-files mode")
        return config

    def _require_canonical_work(self, workstream_id: str, task_id: str | None) -> None:
        if not re.fullmatch(r"WS-[0-9]{3,}", workstream_id):
            raise CoordinationError("invalid-envelope", f"invalid workstream ID: {workstream_id}")
        if task_id is not None and not re.fullmatch(r"T-[0-9]{3,}", task_id):
            raise CoordinationError("invalid-envelope", f"invalid task ID: {task_id}")
        matches = list((self.project_root / "project_state" / "workstreams").glob(f"{workstream_id}-*/STATE.md"))
        if len(matches) != 1:
            raise CoordinationError("unknown-reference", f"unknown workstream: {workstream_id}")
        if task_id and not re.search(
            rf"^- \[[ xX]\]\s+{re.escape(task_id)}\b",
            matches[0].read_text(encoding="utf-8"),
            re.M,
        ):
            raise CoordinationError("unknown-reference", f"unknown task {task_id} in {workstream_id}")

    def _require_decision(
        self,
        decision_id: str,
        *,
        conflict_id: str,
        workstream_id: str,
        resolution: str,
    ) -> None:
        if not re.fullmatch(r"D-[0-9]{3,}", decision_id):
            raise CoordinationError("invalid-envelope", f"invalid decision ID: {decision_id}")
        path = self.project_root / "project_state" / "DECISIONS.md"
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        match = re.search(
            rf"^## {re.escape(decision_id)}\b.*?(?=^## D-[0-9]{{3,}}\b|\Z)",
            text,
            re.M | re.S,
        )
        if not match:
            raise CoordinationError("unknown-reference", f"active human decision not found: {decision_id}")
        block = match.group(0)
        status = re.search(r"\*\*Status:\*\*\s*([^|·\n]+)", block)
        author = re.search(r"\*\*Autor:\*\*\s*([^|·\n]+)", block)
        authority = re.search(r"\*\*Autoridade:\*\*\s*([^|·\n]+)", block)

        def field(label: str) -> str | None:
            value = re.search(rf"^\*\*{re.escape(label)}:\*\*\s*(.*?)\s*$", block, re.M)
            return value.group(1) if value else None

        human = (field("Decisor humano") == "true"
                 or (author is not None and re.search(
                     r"\b(?:fundador|fundadora|usu[aá]rio|usu[aá]ria)\b",
                     author.group(1), re.I) is not None))
        valid = (
            status is not None and status.group(1).strip() == "ativa"
            and authority is not None and authority.group(1).strip() == "approved-decision"
            and human
            and field("Coordination conflict") == conflict_id
            and field("Workstream") == workstream_id
            and field("Approved resolution") == resolution
        )
        if not valid:
            raise CoordinationError("unknown-reference", f"active human decision not found: {decision_id}")

    def _allocate(self, kind: str) -> str:
        counters_path = self.store / "counters.json"
        counters = self._read_json(counters_path)
        counters[kind] += 1
        self._write_json(counters_path, counters)
        return f"{ID_PREFIXES[kind]}-{counters[kind]:03d}"

    def _ensure_store(self) -> None:
        for kind in [*ID_PREFIXES, "acknowledgments", "idempotency"]:
            self._mkdir(self.store / kind)

    def _repair_counters(self) -> None:
        counters_path = self.store / "counters.json"
        counters = self._read_json(counters_path) if counters_path.is_file() else {}
        repaired: dict[str, int] = {}
        for kind, prefix in ID_PREFIXES.items():
            observed = [
                int(match.group(1))
                for path in (self.store / kind).glob(f"{prefix}-*.json")
                if (match := re.fullmatch(rf"{prefix}-([0-9]+)\.json", path.name))
            ]
            repaired[kind] = max([int(counters.get(kind, 0)), *observed])
        self._write_json(counters_path, repaired)

    def _next_fencing_token(self) -> int:
        path = self.store / "fencing-token.json"
        record = self._read_json(path) if path.exists() else {"value": 0}
        record["value"] += 1
        self._write_json(path, record)
        return record["value"]

    def _record_claim_conflict(
        self,
        existing: dict[str, Any],
        agent_id: str,
        workstream_id: str,
        scope_type: str,
        scope_value: str,
        *,
        conflict_type: str = "claim-conflict",
        description: str | None = None,
    ) -> dict[str, Any]:
        conflict_id = self._allocate("conflicts")
        record = {
            "conflict_id": conflict_id,
            "type": conflict_type,
            "severity": "high",
            "workstream_id": workstream_id,
            "task_id": existing.get("task_id"),
            "agents": sorted({existing["agent_id"], agent_id}),
            "artifacts": [existing["claim_id"]],
            "description": description or f"conflicting claim for {scope_type}:{scope_value}",
            "status": "open",
            "requires_human": False,
            "resolution": None,
            "provider_reference": None,
            "created_at": utc_now(),
            "resolved_at": None,
        }
        self._write_record("conflicts", conflict_id, record)
        return record

    def _active_claims(self) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc).replace(microsecond=0)
        active: list[dict[str, Any]] = []
        for claim in self._list("claims"):
            if claim["status"] != "active":
                continue
            if parse_time(claim["expires_at"]) <= now:
                claim["status"] = "expired"
                self._write_record("claims", claim["claim_id"], claim)
            else:
                active.append(claim)
        return active

    def _presence(self, agent: dict[str, Any]) -> dict[str, Any]:
        status = agent["status"]
        if status not in {"available", "working", "waiting", "blocked", "paused", "disconnected"}:
            status = "working" if status in {"assigned", "reviewing"} else "disconnected"
        record = {
            "agent_id": agent["agent_id"],
            "provider": "filesystem",
            "status": status,
            "workstream_id": agent["workstream_id"],
            "task_id": agent["task_id"],
            "last_activity_at": agent["last_seen_at"],
            "heartbeat_at": agent["last_seen_at"],
            "lease_expires_at": None,
            "current_activity": None,
        }
        self.schemas.validate("presence", record)
        return record

    def _open_thread_locked(
        self,
        created_by: str,
        subject: str,
        workstream_id: str | None,
        task_id: str | None,
    ) -> dict[str, Any]:
        thread_id = self._allocate("threads")
        record = {
            "thread_id": thread_id,
            "project_id": self._config()["project_id"],
            "workstream_id": workstream_id,
            "task_id": task_id,
            "subject": subject,
            "created_by": created_by,
            "status": "open",
            "created_at": utc_now(),
            "closed_at": None,
            "closed_by": None,
        }
        self._write_record("threads", thread_id, record)
        return record

    def _message_fingerprint(self, *values: Any) -> str:
        encoded = json.dumps(values, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _idempotency_path(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.store / "idempotency" / f"{digest}.json"

    def _idempotent_message(self, key: str, fingerprint: str) -> dict[str, Any] | None:
        path = self._idempotency_path(key)
        if not path.exists():
            return None
        record = self._read_json(path)
        if record.get("fingerprint") != fingerprint:
            raise CoordinationError("duplicate-id", "idempotency key was reused with another message")
        message = record.get("message")
        if not isinstance(message, dict):
            raise CoordinationError("invalid-envelope", "invalid idempotency record")
        self.schemas.validate("message", message)
        message_id = message.get("message_id")
        message_path = self._record_path("messages", message_id)
        if not message_path.is_file():
            self._write_record("messages", message_id, message)
        if record.get("state") != "committed":
            self._write_idempotency(key, fingerprint, message, "committed")
        return self._read_record("messages", message_id)

    def _write_idempotency(
        self,
        key: str,
        fingerprint: str,
        message: dict[str, Any],
        state: str,
    ) -> None:
        self._write_json(
            self._idempotency_path(key),
            {"fingerprint": fingerprint, "message": message, "state": state},
        )

    def _free_text(self, value: str, limit: int, *, allow_empty: bool = False) -> str:
        if not isinstance(value, str) or not value and not allow_empty:
            raise CoordinationError("invalid-envelope", "text is required")
        value, _ = redact_text(value, self.redaction_patterns)
        if len(value) <= limit:
            return value
        marker = f"[TRUNCATED: {len(value) - limit} characters omitted]"
        return value[: max(0, limit - len(marker))] + marker

    def _structural_text(self, value: str, limit: int, field: str) -> str:
        if not isinstance(value, str) or not value or len(value) > limit:
            raise CoordinationError("invalid-envelope", f"invalid {field}")
        redacted, matches = redact_text(value, self.redaction_patterns)
        if matches:
            raise CoordinationError("unsafe-payload", f"{field} resembles a credential")
        return redacted

    def _optional_structural_text(self, value: str | None, limit: int, field: str) -> str | None:
        return None if value is None else self._structural_text(value, limit, field)

    def _worktree_key(self, value: str | None) -> str:
        if not value:
            return ""
        path = Path(value)
        if not path.is_absolute():
            path = self.project_root / path
        return os.path.normcase(str(path.resolve(strict=False)))

    def _verified_worktree(self, agent: dict[str, Any]) -> tuple[str, str]:
        try:
            completed = subprocess.run(
                ["git", "-C", str(self.project_root), "worktree", "list", "--porcelain"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
                timeout=20,
            )
        except (OSError, UnicodeError, subprocess.SubprocessError) as exc:
            raise CoordinationError("worktree-required", "cannot verify Git worktrees") from exc
        if completed.returncode != 0:
            raise CoordinationError("worktree-required", "project is not a Git worktree")
        declared_path = self._worktree_key(agent.get("worktree"))
        declared_branch = agent.get("branch")
        records: list[dict[str, str]] = []
        current: dict[str, str] = {}
        for line in [*completed.stdout.splitlines(), ""]:
            if not line:
                if current:
                    records.append(current)
                    current = {}
                continue
            key, _, value = line.partition(" ")
            current[key] = value
        for record in records:
            path = os.path.normcase(str(Path(record.get("worktree", "")).resolve(strict=False)))
            branch = record.get("branch", "").removeprefix("refs/heads/")
            if path == declared_path and branch == declared_branch:
                return path, branch
        raise CoordinationError(
            "worktree-required",
            "registered branch and worktree do not match git worktree list",
        )

    def _record_path(self, kind: str, record_id: str) -> Path:
        if not re.fullmatch(r"[A-Z]+-[0-9]{3,}", record_id):
            raise CoordinationError("invalid-envelope", f"invalid record ID: {record_id}")
        return self.store / kind / f"{record_id}.json"

    def _write_record(self, kind: str, record_id: str, record: dict[str, Any]) -> None:
        self.schemas.validate(self._schema_for(kind), record)
        self._write_json(self._record_path(kind, record_id), record)

    def _read_record(self, kind: str, record_id: str) -> dict[str, Any]:
        path = self._record_path(kind, record_id)
        if not path.is_file():
            raise CoordinationError("unknown-reference", f"unknown {kind} record: {record_id}")
        record = self._read_json(path)
        self.schemas.validate(self._schema_for(kind), record)
        return record

    def _list(self, kind: str) -> list[dict[str, Any]]:
        directory = self.store / kind
        if not directory.is_dir():
            return []
        records = [self._read_json(path) for path in sorted(directory.glob("*.json"))]
        for record in records:
            self.schemas.validate(self._schema_for(kind), record)
        return records

    @staticmethod
    def _schema_for(kind: str) -> str:
        return {"agents": "agent", "acknowledgments": "acknowledgment"}.get(kind, kind.rstrip("s"))

    def _ack_path(self, message_id: str, agent_id: str) -> Path:
        if not re.fullmatch(r"MSG-[0-9]{3,}", message_id) or not re.fullmatch(r"AGENT-[0-9]{3,}", agent_id):
            raise CoordinationError("invalid-envelope", "invalid message or agent ID")
        return self.store / "acknowledgments" / f"{message_id}__{agent_id}.json"

    def _read_ack(self, message_id: str, agent_id: str) -> dict[str, Any]:
        record = self._read_json(self._ack_path(message_id, agent_id))
        self.schemas.validate("acknowledgment", record)
        if record["message_id"] != message_id or record["agent_id"] != agent_id:
            raise CoordinationError("invalid-envelope", "acknowledgment identity mismatch")
        return record

    def _valid_ack(self, message_id: str, agent_id: str) -> bool:
        path = self._ack_path(message_id, agent_id)
        if not path.is_file():
            return False
        self._read_ack(message_id, agent_id)
        return True

    def _read_json(self, path: Path) -> dict[str, Any]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CoordinationError("invalid-envelope", f"cannot read {path}") from exc
        if not isinstance(value, dict):
            raise CoordinationError("invalid-envelope", f"expected object in {path}")
        return value

    @staticmethod
    def _mkdir(path: Path) -> None:
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise CoordinationError("filesystem-error", "cannot create coordination runtime directory") from exc

    def _write_json(self, path: Path, value: dict[str, Any]) -> None:
        self._mkdir(path.parent)
        temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        safe_value = redact_value(value, self.redaction_patterns)
        try:
            temporary.write_text(
                json.dumps(safe_value, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            os.replace(temporary, path)
        except OSError as exc:
            cleanup_failed = False
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                cleanup_failed = True
            detail = " and temporary cleanup failed" if cleanup_failed else ""
            raise CoordinationError("filesystem-error", f"cannot write coordination runtime file{detail}") from exc
