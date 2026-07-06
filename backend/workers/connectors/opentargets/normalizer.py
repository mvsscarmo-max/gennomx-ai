"""Normalize a parsed Open Targets row to canonical targets fields."""

from __future__ import annotations

from workers.connectors.opentargets.parser import ParsedTarget

_BIOTYPE_MAP = {
    "protein_coding": "protein",
    "lncrna": "gene",
    "processed_pseudogene": "gene",
}


class OpenTargetsNormalizer:
    def normalize(self, target: ParsedTarget) -> dict:
        external_ids: dict = {}
        if target.external_id:
            external_ids["ensembl"] = target.external_id
        if target.uniprot_id:
            external_ids["uniprot"] = target.uniprot_id

        return {
            "symbol": target.symbol or "",
            "name": target.name,
            "aliases": target.aliases or [],
            "organism": "Homo sapiens",
            "target_type": _BIOTYPE_MAP.get((target.biotype or "").lower(), "gene"),
            "external_ids": external_ids,
            "open_targets_score": target.open_targets_score,
            "associated_indication_names": [target.disease_name] if target.disease_name else [],
        }
