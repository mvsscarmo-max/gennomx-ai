"""Núcleo portátil de overlay semântico / paridade (federation/protocol 1.1.0).

Os nomes de campo coincidem com ``tools/protocol_core.py``. O validador da raiz
continua a autoridade de ``snapshot_from_repo``; este módulo é o subconjunto
que as irmãs instalam com o bundle.
"""
from __future__ import annotations

from typing import Any

ALLOWED_OVERLAY_FIELDS = frozenset({
    "stack",
    "local_commands",
    "agents_local",
    "project_local",
    "extra_skills",
    "extra_templates",
    "extra_validation_commands",
    "extra_event_types",
    "extra_policies",
})
FORBIDDEN_OVERLAY_FIELDS = frozenset({
    "human_authority",
    "privacy",
    "capture_policy",
    "privacy_policy",
    "g14_signer",
    "rc_required_from_risk",
    "gates_floor",
    "editorial_human_review",
})


def overlay_field_names(document: dict[str, Any]) -> list[str]:
    fields = document.get("fields")
    if not isinstance(fields, list):
        return []
    names: list[str] = []
    for item in fields:
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            names.append(item["name"])
    return names


def forbidden_overlay_fields(document: dict[str, Any]) -> list[str]:
    return [name for name in overlay_field_names(document) if name in FORBIDDEN_OVERLAY_FIELDS]


def unknown_overlay_fields(document: dict[str, Any]) -> list[str]:
    return [
        name for name in overlay_field_names(document)
        if name not in ALLOWED_OVERLAY_FIELDS and name not in FORBIDDEN_OVERLAY_FIELDS
    ]


def overlay_is_portable(document: dict[str, Any]) -> bool:
    return not forbidden_overlay_fields(document) and not unknown_overlay_fields(document)
