"""Parse DailyMed SPL list records (GET /services/v2/spls.json) to internal structures."""

from __future__ import annotations

from datetime import date, datetime


class ParsedLabel:
    def __init__(self) -> None:
        self.external_id: str | None = None  # setid
        self.asset_name: str | None = None
        self.asset_aliases: list[str] = []
        self.title: str | None = None
        self.published_date: date | None = None
        self.label_url: str | None = None


class DailyMedParser:
    def parse_record(self, record: dict) -> ParsedLabel:
        parsed = ParsedLabel()
        parsed.external_id = record.get("setid")
        parsed.title = record.get("title")
        parsed.published_date = self._parse_date(record.get("published_date"))
        if parsed.external_id:
            parsed.label_url = (
                f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={parsed.external_id}"
            )
        self._parse_title(parsed)
        return parsed

    @staticmethod
    def _parse_title(parsed: ParsedLabel) -> None:
        title = parsed.title or ""
        # DailyMed titles follow "DRUG NAME- description dosage form" convention.
        separator = "- " if "- " in title else ("-" if "-" in title else None)
        if separator:
            head, _, tail = title.partition(separator)
            name = head.strip().rstrip(",;").title()
            parsed.asset_name = name or None
            tail_tokens = [t.strip().title() for t in tail.replace(",", " ").split() if t.strip()]
            parsed.asset_aliases = list(dict.fromkeys(tail_tokens))[:3]
        else:
            parsed.asset_name = title.strip().title() or None

    @staticmethod
    def _parse_date(value: str | None) -> date | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            return None
