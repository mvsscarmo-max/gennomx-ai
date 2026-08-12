"""Parse ClinicalTrials.gov API v2 JSON response to internal structures."""

from __future__ import annotations

from datetime import date


class ParsedTrial:
    """Intermediate representation of a parsed clinical trial."""

    def __init__(self) -> None:
        self.nct_id: str | None = None
        self.title: str | None = None
        self.brief_title: str | None = None
        self.official_title: str | None = None
        self.phase: str | None = None
        self.status: str | None = None
        self.sponsor_name: str | None = None
        self.collaborators: list[dict] = []
        self.conditions: list[str] = []
        self.interventions: list[dict] = []
        self.arms: list[dict] = []
        self.enrollment: int | None = None
        self.enrollment_type: str | None = None
        self.start_date: date | None = None
        self.primary_completion_date: date | None = None
        self.completion_date: date | None = None
        self.last_update_date: date | None = None
        self.countries: list[str] = []
        self.locations: list[dict] = []
        self.eligibility_criteria: str | None = None
        self.minimum_age: str | None = None
        self.maximum_age: str | None = None
        self.sex: str | None = None
        self.primary_outcomes: list[dict] = []
        self.secondary_outcomes: list[dict] = []
        self.result_outcomes: list[dict] = []
        self.adverse_events: list[dict] = []
        self.adverse_event_groups: dict[str, dict] = {}
        self.has_results: bool = False


class ClinicalTrialsParser:
    """Parses the ClinicalTrials.gov API v2 study object."""

    def parse_study(self, raw: dict) -> ParsedTrial:
        trial = ParsedTrial()
        protocol = raw.get("protocolSection", {})

        self._parse_identification(trial, protocol.get("identificationModule", {}))
        self._parse_status(trial, protocol.get("statusModule", {}))
        self._parse_sponsor(trial, protocol.get("sponsorCollaboratorsModule", {}))
        self._parse_conditions(trial, protocol.get("conditionsModule", {}))
        self._parse_design(trial, protocol.get("designModule", {}))
        self._parse_interventions(trial, protocol.get("armsInterventionsModule", {}))
        self._parse_eligibility(trial, protocol.get("eligibilityModule", {}))
        self._parse_locations(trial, protocol.get("contactsLocationsModule", {}))
        self._parse_outcomes(trial, protocol.get("outcomesModule", {}))

        results = raw.get("resultsSection")
        trial.has_results = isinstance(results, dict) and bool(results)
        if isinstance(results, dict) and results:
            self._parse_result_outcomes(trial, results.get("outcomeMeasuresModule", {}))
            self._parse_adverse_events(trial, results.get("adverseEventsModule", {}))

        return trial

    def _parse_identification(self, trial: ParsedTrial, module: dict) -> None:
        trial.nct_id = module.get("nctId")
        trial.title = module.get("briefTitle") or module.get("officialTitle", "")
        trial.brief_title = module.get("briefTitle")
        trial.official_title = module.get("officialTitle")

    def _parse_status(self, trial: ParsedTrial, module: dict) -> None:
        trial.status = module.get("overallStatus")
        last_update = module.get("lastUpdatePostDateStruct", {}).get("date")
        trial.last_update_date = self._parse_date(last_update)

    def _parse_sponsor(self, trial: ParsedTrial, module: dict) -> None:
        lead = module.get("leadSponsor", {})
        trial.sponsor_name = lead.get("name")
        trial.collaborators = [
            {"name": c.get("name"), "class": c.get("class")}
            for c in module.get("collaborators", [])
        ]

    def _parse_conditions(self, trial: ParsedTrial, module: dict) -> None:
        trial.conditions = module.get("conditions", [])

    def _parse_design(self, trial: ParsedTrial, module: dict) -> None:
        trial.phase = self._normalize_phases(module.get("phases", []))
        enrollment = module.get("enrollmentInfo", {})
        count = enrollment.get("count")
        trial.enrollment = int(count) if count is not None else None
        trial.enrollment_type = enrollment.get("type")

    def _parse_interventions(self, trial: ParsedTrial, module: dict) -> None:
        trial.arms = [
            {
                "label": a.get("label"),
                "type": a.get("type"),
                "description": a.get("description"),
            }
            for a in module.get("armGroups", [])
        ]
        trial.interventions = [
            {
                "name": i.get("name"),
                "type": i.get("type"),
                "description": i.get("description"),
                "arm_group_labels": i.get("armGroupLabels", []),
                "other_names": i.get("otherNames", []),
            }
            for i in module.get("interventions", [])
        ]

    def _parse_eligibility(self, trial: ParsedTrial, module: dict) -> None:
        trial.eligibility_criteria = module.get("eligibilityCriteria")
        trial.minimum_age = module.get("minimumAge")
        trial.maximum_age = module.get("maximumAge")
        trial.sex = module.get("sex")

    def _parse_locations(self, trial: ParsedTrial, module: dict) -> None:
        locations = module.get("locations", [])
        country_set: set[str] = set()
        parsed_locations = []
        for loc in locations:
            country = loc.get("country")
            if country:
                country_set.add(country)
            parsed_locations.append(
                {
                    "facility": loc.get("facility"),
                    "city": loc.get("city"),
                    "state": loc.get("state"),
                    "country": country,
                    "status": loc.get("status"),
                }
            )
        trial.countries = sorted(country_set)
        trial.locations = parsed_locations

    def _parse_outcomes(self, trial: ParsedTrial, module: dict) -> None:
        trial.primary_outcomes = [
            {
                "measure": o.get("measure"),
                "description": o.get("description"),
                "timeframe": o.get("timeFrame"),
            }
            for o in module.get("primaryOutcomes", [])
        ]
        trial.secondary_outcomes = [
            {
                "measure": o.get("measure"),
                "description": o.get("description"),
                "timeframe": o.get("timeFrame"),
            }
            for o in module.get("secondaryOutcomes", [])
        ]

    def _parse_result_outcomes(self, trial: ParsedTrial, module: dict) -> None:
        trial.result_outcomes = [
            {
                "type": outcome.get("type"),
                "title": outcome.get("title"),
                "description": outcome.get("description"),
                "timeframe": outcome.get("timeFrame"),
                "population": outcome.get("populationDescription"),
                "units": outcome.get("units"),
                "param_type": outcome.get("paramType"),
                "dispersion_type": outcome.get("dispersionType"),
                "groups": outcome.get("groups", []),
                "denoms": outcome.get("denoms", []),
                "classes": outcome.get("classes", []),
                "analyses": outcome.get("analyses", []),
                "raw": outcome,
            }
            for outcome in module.get("outcomeMeasures", [])
            if outcome.get("title")
        ]

    def _parse_adverse_events(self, trial: ParsedTrial, module: dict) -> None:
        groups = {
            group.get("id"): group for group in module.get("eventGroups", []) if group.get("id")
        }
        trial.adverse_event_groups = groups
        parsed_events: list[dict] = []
        for field, seriousness in (
            ("seriousEvents", "serious"),
            ("otherEvents", "non_serious"),
        ):
            for event in module.get(field, []):
                term = event.get("term")
                if not term:
                    continue
                for stat in event.get("stats", []):
                    group_id = stat.get("groupId")
                    parsed_events.append(
                        {
                            "term": term,
                            "organ_system": event.get("organSystem"),
                            "source_vocabulary": event.get("sourceVocabulary"),
                            "assessment_type": event.get("assessmentType"),
                            "seriousness": seriousness,
                            "group_id": group_id,
                            "group": groups.get(group_id, {}),
                            "num_events": stat.get("numEvents"),
                            "num_affected": stat.get("numAffected"),
                            "num_at_risk": stat.get("numAtRisk"),
                            "raw": {"event": event, "stat": stat},
                        }
                    )
        trial.adverse_events = parsed_events

    @staticmethod
    def _normalize_phases(phases: list[str]) -> str | None:
        if not phases:
            return None
        phase_map = {
            "PHASE1": "PHASE1",
            "PHASE2": "PHASE2",
            "PHASE3": "PHASE3",
            "PHASE4": "PHASE4",
            "EARLY_PHASE1": "PHASE1_EARLY",
            "NA": "NA",
        }
        normalized = [phase_map.get(p, p) for p in phases]
        return "/".join(normalized)

    @staticmethod
    def _parse_date(date_str: str | None) -> date | None:
        if not date_str:
            return None
        try:
            from datetime import date as date_cls

            parts = date_str.split("-")
            if len(parts) == 3:
                return date_cls(int(parts[0]), int(parts[1]), int(parts[2]))
            elif len(parts) == 2:
                return date_cls(int(parts[0]), int(parts[1]), 1)
            elif len(parts) == 1 and len(parts[0]) == 4:
                return date_cls(int(parts[0]), 1, 1)
        except (ValueError, IndexError):
            pass
        return None
