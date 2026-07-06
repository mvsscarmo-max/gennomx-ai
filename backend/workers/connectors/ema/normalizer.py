"""Normalize a parsed EMA medicines-export row to canonical regulatory_approvals fields."""

from __future__ import annotations

from datetime import UTC, datetime, time

from workers.connectors.ema.parser import ParsedEMARecord


class EMANormalizer:
    def normalize(self, record: ParsedEMARecord) -> dict:
        source_updated_at = (
            datetime.combine(record.authorisation_date, time.min, tzinfo=UTC)
            if record.authorisation_date
            else None
        )
        special_designations = ["orphan_drug"] if record.orphan else []
        return {
            "asset_name": record.asset_name or "",
            "asset_aliases": record.asset_aliases or [],
            "agency": "EMA",
            "region": "EU",
            "approval_status": record.approval_status or "pending",
            "approval_date": record.authorisation_date,
            "submission_date": None,
            "pathway": None,
            "special_designations": special_designations,
            "application_number": record.product_number,
            "label_url": record.epar_url,
            "indication_name": record.therapeutic_area,
            "indication_id": None,
            "source_updated_at": source_updated_at,
            "raw_data": {
                "therapeutic_area": record.therapeutic_area,
                "row_index": record.row_index,
            },
        }
