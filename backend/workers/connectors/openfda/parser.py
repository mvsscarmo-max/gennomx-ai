"""Parse openFDA Drugs@FDA (drugsfda) API records to internal structures."""

from __future__ import annotations

import re
from datetime import date, datetime


class ParsedApproval:
    def __init__(self) -> None:
        self.external_id: str | None = None
        self.asset_name: str | None = None
        self.asset_aliases: list[str] = []
        self.agency: str = "FDA"
        self.region: str = "US"
        self.approval_status: str | None = None
        self.approval_date: date | None = None
        self.submission_date: date | None = None
        self.pathway: str | None = None
        self.special_designations: list[str] = []
        self.application_number: str | None = None
        self.label_url: str | None = None
        self.indication_name: str | None = None
        self.source_updated_at: datetime | None = None
        self.sponsor_name: str | None = None


class OpenFDAParser:
    """Parse one result item from GET /drug/drugsfda.json."""

    SUBMISSION_STATUS_MAP = {
        "AP": "approved",
        "TA": "approved",
        "AN": "pending",
        "WD": "withdrawn",
    }

    def parse_record(self, record: dict) -> ParsedApproval:
        parsed = ParsedApproval()
        parsed.application_number = record.get("application_number")
        parsed.external_id = parsed.application_number
        parsed.sponsor_name = record.get("sponsor_name")

        self._parse_product_names(parsed, record.get("products") or [])
        self._parse_submissions(parsed, record.get("submissions") or [])
        self._parse_openfda_block(parsed, record.get("openfda") or {})

        if parsed.application_number:
            appl_no = re.sub(r"^[A-Z]+", "", parsed.application_number).strip()
            parsed.label_url = (
                "https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm"
                f"?event=overview.process&ApplNo={appl_no}"
            )
        return parsed

    def _parse_product_names(self, parsed: ParsedApproval, products: list[dict]) -> None:
        names: list[str] = []
        for product in products:
            brand = product.get("brand_name")
            if brand:
                names.append(str(brand).strip().title())
            for ingredient in product.get("active_ingredients") or []:
                name = ingredient.get("name")
                if name:
                    names.append(str(name).strip().title())
        deduped: list[str] = []
        seen: set[str] = set()
        for name in names:
            key = name.casefold()
            if key not in seen:
                seen.add(key)
                deduped.append(name)
        if deduped:
            parsed.asset_name = deduped[0]
            parsed.asset_aliases = deduped[1:]

    def _parse_submissions(self, parsed: ParsedApproval, submissions: list[dict]) -> None:
        parsed_dates: list[tuple[date, dict]] = []
        for submission in submissions:
            raw_date = submission.get("submission_status_date")
            parsed_date = self._parse_yyyymmdd(raw_date)
            if parsed_date:
                parsed_dates.append((parsed_date, submission))

        if not parsed_dates:
            return

        parsed_dates.sort(key=lambda item: item[0])
        parsed.submission_date = parsed_dates[0][0]

        latest_date, latest_submission = parsed_dates[-1]
        parsed.approval_date = latest_date
        parsed.source_updated_at = datetime.combine(latest_date, datetime.min.time())

        status_code = str(latest_submission.get("submission_status") or "").upper()
        parsed.approval_status = self.SUBMISSION_STATUS_MAP.get(status_code, "pending")

        review_priority = str(latest_submission.get("review_priority") or "").upper()
        if review_priority == "PRIORITY":
            parsed.special_designations.append("priority_review")
        submission_class = latest_submission.get("submission_class_code_description")
        if submission_class:
            parsed.pathway = str(submission_class)

    def _parse_openfda_block(self, parsed: ParsedApproval, openfda: dict) -> None:
        for key in ("brand_name", "generic_name", "substance_name"):
            for value in openfda.get(key) or []:
                cleaned = str(value).strip().title()
                is_new_alias = (
                    cleaned and cleaned.casefold() != (parsed.asset_name or "").casefold()
                )
                if is_new_alias and cleaned not in parsed.asset_aliases:
                    parsed.asset_aliases.append(cleaned)
        if not parsed.asset_name:
            brand_names = openfda.get("brand_name") or []
            if brand_names:
                parsed.asset_name = str(brand_names[0]).strip().title()

    @staticmethod
    def _parse_yyyymmdd(value: str | None) -> date | None:
        if not value or not isinstance(value, str) or len(value) != 8:
            return None
        try:
            return datetime.strptime(value, "%Y%m%d").date()
        except ValueError:
            return None
