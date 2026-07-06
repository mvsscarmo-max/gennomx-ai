"""Normalize parsed ClinicalTrial to canonical DB fields."""

from __future__ import annotations

from datetime import UTC, datetime, time

from workers.connectors.clinicaltrials.parser import ParsedTrial

# Normalized status map (ClinicalTrials.gov → internal)
STATUS_MAP = {
    "RECRUITING": "RECRUITING",
    "NOT_YET_RECRUITING": "NOT_YET_RECRUITING",
    "ENROLLING_BY_INVITATION": "ENROLLING_BY_INVITATION",
    "ACTIVE_NOT_RECRUITING": "ACTIVE_NOT_RECRUITING",
    "COMPLETED": "COMPLETED",
    "SUSPENDED": "SUSPENDED",
    "TERMINATED": "TERMINATED",
    "WITHDRAWN": "WITHDRAWN",
    "AVAILABLE": "AVAILABLE",
    "NO_LONGER_AVAILABLE": "NO_LONGER_AVAILABLE",
    "TEMPORARILY_NOT_AVAILABLE": "TEMPORARILY_NOT_AVAILABLE",
    "APPROVED_FOR_MARKETING": "APPROVED_FOR_MARKETING",
    "WITHHELD": "WITHHELD",
    "UNKNOWN": "UNKNOWN",
}

PHASE_MAP = {
    "PHASE1": "PHASE1",
    "PHASE2": "PHASE2",
    "PHASE3": "PHASE3",
    "PHASE4": "PHASE4",
    "PHASE1/PHASE2": "PHASE1_2",
    "PHASE2/PHASE3": "PHASE2_3",
    "PHASE1_EARLY": "EARLY_PHASE1",
    "NA": "NA",
}


class ClinicalTrialsNormalizer:
    STATUS_MAP = STATUS_MAP
    PHASE_MAP = PHASE_MAP

    def normalize(self, trial: ParsedTrial) -> dict:
        """Return dict ready to be inserted into clinical_trials table."""
        source_updated_at = (
            datetime.combine(trial.last_update_date, time.min, tzinfo=UTC)
            if trial.last_update_date
            else None
        )
        return {
            "nct_id": trial.nct_id,
            "title": trial.title or "",
            "brief_title": trial.brief_title,
            "official_title": trial.official_title,
            "phase": trial.phase,
            "phase_normalized": PHASE_MAP.get(trial.phase or "", trial.phase),
            "status": trial.status,
            "status_normalized": STATUS_MAP.get(trial.status or "", trial.status),
            "sponsor_name": trial.sponsor_name,
            "collaborators": trial.collaborators or [],
            "conditions": trial.conditions or [],
            "interventions": trial.interventions or [],
            "arms": trial.arms or [],
            "enrollment": trial.enrollment,
            "enrollment_type": trial.enrollment_type,
            "start_date": trial.start_date,
            "primary_completion_date": trial.primary_completion_date,
            "completion_date": trial.completion_date,
            "last_update_date": trial.last_update_date,
            "source_updated_at": source_updated_at,
            "countries": trial.countries or [],
            "locations": trial.locations[:50] if trial.locations else [],  # cap to 50
            "eligibility_criteria": trial.eligibility_criteria,
            "minimum_age": trial.minimum_age,
            "maximum_age": trial.maximum_age,
            "sex": trial.sex,
            "registry_source": "clinicaltrials_gov",
        }

    @staticmethod
    def extract_drug_names(trial: ParsedTrial) -> list[str]:
        """Extract likely drug names from interventions."""
        drug_types = {"DRUG", "BIOLOGICAL", "DEVICE", "GENETIC", "PROCEDURE"}
        names = []
        for iv in trial.interventions:
            if iv.get("type", "").upper() in drug_types:
                name = iv.get("name")
                if name:
                    names.append(name)
        return names
