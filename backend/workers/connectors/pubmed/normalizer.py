"""Normalize parsed PubMed publication to canonical DB fields."""

from __future__ import annotations

from datetime import UTC, datetime, time

from workers.connectors.pubmed.parser import ParsedPublication


class PubMedNormalizer:
    def normalize(self, pub: ParsedPublication) -> dict:
        source_updated_at = (
            datetime.combine(pub.date_revised, time.min, tzinfo=UTC) if pub.date_revised else None
        )
        return {
            "pmid": pub.pmid,
            "doi": pub.doi,
            "pmcid": pub.pmcid,
            "title": pub.title or "",
            "abstract": pub.abstract,
            "journal": pub.journal,
            "authors": pub.authors or [],
            "publication_date": pub.publication_date,
            "publication_type": pub.publication_type,
            "keywords": pub.keywords or [],
            "nct_ids": pub.nct_ids or [],
            "source_updated_at": source_updated_at,
            "registry_source": "pubmed",
            "evidence_maturity": "peer_reviewed_primary",
            "source_url": f"https://pubmed.ncbi.nlm.nih.gov/{pub.pmid}/" if pub.pmid else None,
            "open_access": False,
        }
