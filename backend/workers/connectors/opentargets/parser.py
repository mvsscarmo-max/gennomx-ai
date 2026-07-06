"""Parse Open Targets Platform GraphQL target/associatedTargets rows to internal structures."""

from __future__ import annotations


class ParsedTarget:
    def __init__(self) -> None:
        self.external_id: str | None = None  # Ensembl gene id
        self.symbol: str | None = None
        self.name: str | None = None
        self.aliases: list[str] = []
        self.biotype: str | None = None
        self.uniprot_id: str | None = None
        self.open_targets_score: float | None = None
        self.disease_name: str | None = None


class OpenTargetsParser:
    def parse_associated_target_row(self, row: dict, disease_name: str | None) -> ParsedTarget:
        target = row.get("target") or {}
        parsed = ParsedTarget()
        parsed.external_id = target.get("id")
        parsed.symbol = target.get("approvedSymbol")
        parsed.name = target.get("approvedName")
        parsed.biotype = target.get("biotype")
        parsed.disease_name = disease_name

        synonyms = target.get("synonyms") or []
        parsed.aliases = list(
            dict.fromkeys(
                str(s.get("label")).strip()
                for s in synonyms
                if isinstance(s, dict) and s.get("label")
            )
        )[:10]

        for protein in target.get("proteinIds") or []:
            if isinstance(protein, dict) and protein.get("source") == "uniprot_swissprot":
                parsed.uniprot_id = protein.get("id")
                break

        score = row.get("score")
        if isinstance(score, int | float):
            parsed.open_targets_score = float(score)

        return parsed
