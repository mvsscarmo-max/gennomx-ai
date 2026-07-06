"""Executable data-granularity and freshness policy registry."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any


@dataclass(frozen=True)
class FieldPolicy:
    entity_type: str
    field_path: str
    granularity_dimensions: tuple[str, ...]
    freshness_days: int | None
    required: bool = False
    critical: bool = True
    default_authority: float = 0.8
    data_class: str = "operational"

    def granularity_key(self, dimensions: dict[str, Any] | None = None) -> str:
        values = dimensions or {}
        if not self.granularity_dimensions:
            return "entity"
        parts: list[str] = []
        for name in self.granularity_dimensions:
            value = values.get(name)
            if value in (None, ""):
                raise ValueError(f"missing_granularity_dimension:{name}")
            normalized = str(value).strip().casefold().replace("|", "%7c")
            parts.append(f"{name}={normalized}")
        return "|".join(parts)

    def expires_at(self, observed_at: datetime | None = None) -> datetime | None:
        if self.freshness_days is None:
            return None
        base = observed_at or datetime.now(UTC)
        return base + timedelta(days=self.freshness_days)


POLICIES: dict[tuple[str, str], FieldPolicy] = {
    ("clinical_trial", "status_normalized"): FieldPolicy(
        "clinical_trial", "status_normalized", ("registry",), 14, required=True
    ),
    ("clinical_trial", "phase_normalized"): FieldPolicy(
        "clinical_trial", "phase_normalized", ("registry",), 90
    ),
    ("clinical_trial", "enrollment"): FieldPolicy(
        "clinical_trial", "enrollment", ("registry",), 30
    ),
    ("clinical_trial", "sponsor_name"): FieldPolicy(
        "clinical_trial", "sponsor_name", ("registry",), 30
    ),
    ("trial_result", "result_value"): FieldPolicy(
        "trial_result",
        "result_value",
        ("trial_id", "arm", "population", "timepoint", "measure"),
        None,
        required=True,
        data_class="clinical_critical",
    ),
    ("adverse_event", "incidence"): FieldPolicy(
        "adverse_event",
        "incidence",
        ("trial_id", "arm", "term", "grade", "population"),
        None,
        data_class="clinical_critical",
    ),
    ("regulatory_approval", "status"): FieldPolicy(
        "regulatory_approval",
        "status",
        ("product", "indication", "region"),
        7,
        required=True,
        default_authority=0.98,
        data_class="regulatory_critical",
    ),
    ("company_pipeline", "stage"): FieldPolicy(
        "company_pipeline", "stage", ("asset", "indication", "company"), 60
    ),
    ("publication", "status"): FieldPolicy(
        "publication", "status", ("doi_or_pmid",), None, default_authority=0.9
    ),
    ("target", "ontology_release"): FieldPolicy(
        "target", "ontology_release", ("identifier", "release"), None
    ),
}


def get_field_policy(entity_type: str, field_path: str) -> FieldPolicy:
    try:
        return POLICIES[(entity_type, field_path)]
    except KeyError as exc:
        raise ValueError(f"undefined_data_policy:{entity_type}.{field_path}") from exc
