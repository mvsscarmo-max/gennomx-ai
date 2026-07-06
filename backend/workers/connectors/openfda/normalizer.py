"""Normalize parsed openFDA approval to canonical regulatory_approvals fields."""

from __future__ import annotations

from workers.connectors.openfda.parser import ParsedApproval


class OpenFDANormalizer:
    def normalize(self, approval: ParsedApproval) -> dict:
        return {
            "asset_name": approval.asset_name or "",
            "asset_aliases": approval.asset_aliases or [],
            "agency": approval.agency,
            "region": approval.region,
            "approval_status": approval.approval_status,
            "approval_date": approval.approval_date,
            "submission_date": approval.submission_date,
            "pathway": approval.pathway,
            "special_designations": approval.special_designations or [],
            "application_number": approval.application_number,
            "label_url": approval.label_url,
            "indication_name": approval.indication_name,
            "indication_id": None,
            "source_updated_at": approval.source_updated_at,
            "raw_data": {"sponsor_name": approval.sponsor_name},
        }
