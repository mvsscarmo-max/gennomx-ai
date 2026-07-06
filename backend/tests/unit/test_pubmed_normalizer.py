"""Unit tests for PubMed normalizer."""

from datetime import date

import pytest

from workers.connectors.pubmed.normalizer import PubMedNormalizer
from workers.connectors.pubmed.parser import ParsedPublication


@pytest.mark.unit
@pytest.mark.connector
class TestPubMedNormalizer:
    def setup_method(self):
        self.normalizer = PubMedNormalizer()

    def test_full_normalization(self):
        pub = ParsedPublication()
        pub.pmid = "39567890"
        pub.doi = "10.1056/NEJMoa2411764"
        pub.pmcid = "PMC11876543"
        pub.title = "Pembrolizumab in Endometrial Cancer"
        pub.abstract = "Background: Standard treatment..."
        pub.journal = "N Engl J Med"
        pub.authors = ["Smith JA", "Doe J"]
        pub.publication_date = date(2025, 3, 6)
        pub.date_revised = date(2026, 1, 15)
        pub.publication_type = "article"
        pub.keywords = ["Endometrial Neoplasms", "Pembrolizumab"]
        pub.nct_ids = ["NCT03914612"]

        result = self.normalizer.normalize(pub)

        assert result["pmid"] == "39567890"
        assert result["doi"] == "10.1056/NEJMoa2411764"
        assert result["pmcid"] == "PMC11876543"
        assert result["title"] == "Pembrolizumab in Endometrial Cancer"
        assert result["abstract"] == "Background: Standard treatment..."
        assert result["journal"] == "N Engl J Med"
        assert result["authors"] == ["Smith JA", "Doe J"]
        assert result["publication_date"] == date(2025, 3, 6)
        assert result["publication_type"] == "article"
        assert result["keywords"] == ["Endometrial Neoplasms", "Pembrolizumab"]
        assert result["nct_ids"] == ["NCT03914612"]
        assert result["evidence_maturity"] == "peer_reviewed_primary"
        assert result["registry_source"] == "pubmed"
        assert not result["open_access"]
        assert result["source_url"] == "https://pubmed.ncbi.nlm.nih.gov/39567890/"
        assert result["source_updated_at"] is not None

    def test_minimal_normalization(self):
        pub = ParsedPublication()
        pub.pmid = "1"
        pub.title = "Test"

        result = self.normalizer.normalize(pub)

        assert result["pmid"] == "1"
        assert result["title"] == "Test"
        assert result["doi"] is None
        assert result["authors"] == []
        assert result["nct_ids"] == []
        assert result["keywords"] == []
        assert result["evidence_maturity"] == "peer_reviewed_primary"
        assert result["registry_source"] == "pubmed"
        assert result["source_updated_at"] is None

    def test_null_pmid_source_url(self):
        pub = ParsedPublication()
        pub.pmid = None

        result = self.normalizer.normalize(pub)
        assert result["source_url"] is None
