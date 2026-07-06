"""Normalize parsed DailyMed SPL label to canonical regulatory_approvals fields."""

from __future__ import annotations

from datetime import UTC, datetime, time

from workers.connectors.dailymed.parser import ParsedLabel


class DailyMedNormalizer:
    def normalize(self, label: ParsedLabel) -> dict:
        source_updated_at = (
            datetime.combine(label.published_date, time.min, tzinfo=UTC)
            if label.published_date
            else None
        )
        return {
            "asset_name": label.asset_name or "",
            "asset_aliases": label.asset_aliases or [],
            "agency": "FDA",
            "region": "US",
            "approval_status": "approved",
            "approval_date": label.published_date,
            "submission_date": None,
            "pathway": None,
            "special_designations": [],
            "application_number": None,
            "label_url": label.label_url,
            "indication_name": None,
            "indication_id": None,
            "source_updated_at": source_updated_at,
            "raw_data": {"setid": label.external_id, "title": label.title},
        }
