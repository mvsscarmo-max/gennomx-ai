"""Unit tests for PubMed XML parser."""

from xml.etree import ElementTree as ET

import pytest

from workers.connectors.pubmed.parser import PubMedParser

VALID_XML = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE PubmedArticleSet PUBLIC "-//NLM//DTD PubMedArticle, 1st January 2024//EN" "https://dtd.nlm.nih.gov/ncbi/pubmed/out/pubmed_240101.dtd">
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation Status="MEDLINE" Owner="NLM">
      <PMID Version="1">39567890</PMID>
      <DateRevised>
        <Year>2026</Year>
        <Month>01</Month>
        <Day>15</Day>
      </DateRevised>
      <Article PubModel="Print-Electronic">
        <Journal>
          <ISSN IssnType="Electronic">1533-4406</ISSN>
          <JournalIssue CitedMedium="Internet">
            <Volume>392</Volume>
            <Issue>10</Issue>
            <PubDate>
              <Year>2025</Year>
              <Month>Mar</Month>
              <Day>06</Day>
            </PubDate>
          </JournalIssue>
          <Title>The New England journal of medicine</Title>
          <ISOAbbreviation>N Engl J Med</ISOAbbreviation>
        </Journal>
        <ArticleTitle>Pembrolizumab plus Chemotherapy in Advanced Endometrial Cancer</ArticleTitle>
        <Abstract>
          <AbstractText Label="BACKGROUND" NlmCategory="BACKGROUND">
            Standard first-line treatment...
          </AbstractText>
          <AbstractText Label="METHODS" NlmCategory="METHODS">
            In this phase 3 trial...
          </AbstractText>
          <AbstractText Label="RESULTS" NlmCategory="RESULTS">
            Overall survival was significantly longer...
          </AbstractText>
          <AbstractText Label="CONCLUSIONS" NlmCategory="CONCLUSIONS">
            Pembrolizumab plus chemotherapy improved outcomes.
          </AbstractText>
        </Abstract>
        <AuthorList CompleteYN="Y">
          <Author ValidYN="Y">
            <LastName>Smith</LastName>
            <ForeName>John A</ForeName>
            <Initials>JA</Initials>
            <AffiliationInfo>
              <Affiliation>Harvard Medical School</Affiliation>
            </AffiliationInfo>
          </Author>
          <Author ValidYN="Y">
            <LastName>Doe</LastName>
            <ForeName>Jane</ForeName>
            <Initials>J</Initials>
          </Author>
        </AuthorList>
        <Language>eng</Language>
        <PublicationTypeList>
          <PublicationType UI="D016428">Journal Article</PublicationType>
          <PublicationType UI="D016449">Randomized Controlled Trial</PublicationType>
        </PublicationTypeList>
        <ArticleDate DateType="Electronic">
          <Year>2025</Year>
          <Month>03</Month>
          <Day>06</Day>
        </ArticleDate>
      </Article>
      <MeshHeadingList>
        <MeshHeading>
          <DescriptorName UI="D010146" MajorTopicYN="N">Endometrial Neoplasms</DescriptorName>
        </MeshHeading>
        <MeshHeading>
          <DescriptorName UI="D000068877" MajorTopicYN="Y">Pembrolizumab</DescriptorName>
        </MeshHeading>
        <MeshHeading>
          <DescriptorName UI="D000069552" MajorTopicYN="N">
            Antineoplastic Agents, Immunological
          </DescriptorName>
        </MeshHeading>
      </MeshHeadingList>
      <DataBankList CompleteYN="Y">
        <DataBank>
          <DataBankName>ClinicalTrials.gov</DataBankName>
          <AccessionNumberList>
            <AccessionNumber>NCT03914612</AccessionNumber>
          </AccessionNumberList>
        </DataBank>
      </DataBankList>
    </MedlineCitation>
    <PubmedData>
      <History>
        <PubMedPubDate PubStatus="pubmed">
          <Year>2025</Year><Month>3</Month><Day>6</Day>
        </PubMedPubDate>
        <PubMedPubDate PubStatus="medline">
          <Year>2025</Year><Month>03</Month><Day>10</Day>
        </PubMedPubDate>
      </History>
      <ArticleIdList>
        <ArticleId IdType="pubmed">39567890</ArticleId>
        <ArticleId IdType="doi">10.1056/NEJMoa2411764</ArticleId>
        <ArticleId IdType="pmc">PMC11876543</ArticleId>
      </ArticleIdList>
    </PubmedData>
  </PubmedArticle>
</PubmedArticleSet>"""

MINIMAL_XML = """<?xml version="1.0" encoding="utf-8"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation Status="MEDLINE">
      <PMID Version="1">12345678</PMID>
      <Article>
        <Journal>
          <Title>Test Journal</Title>
        </Journal>
        <ArticleTitle>Minimal Article</ArticleTitle>
        <AuthorList>
          <Author>
            <CollectiveName>WHO Working Group</CollectiveName>
          </Author>
        </AuthorList>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>"""


@pytest.mark.unit
@pytest.mark.connector
class TestPubMedParser:
    def setup_method(self):
        self.parser = PubMedParser()

    def test_parse_full_article(self):
        root = ET.fromstring(VALID_XML)
        articles = root.findall(".//PubmedArticle")
        pub = self.parser.parse_article(articles[0])

        assert pub.pmid == "39567890"
        assert pub.doi == "10.1056/NEJMoa2411764"
        assert pub.pmcid == "PMC11876543"
        assert pub.title == "Pembrolizumab plus Chemotherapy in Advanced Endometrial Cancer"
        assert pub.journal == "The New England journal of medicine"
        assert pub.abstract is not None
        assert "BACKGROUND: Standard first-line treatment" in pub.abstract
        assert "METHODS: In this phase 3 trial" in pub.abstract
        assert "RESULTS: Overall survival was significantly longer" in pub.abstract
        assert "CONCLUSIONS: Pembrolizumab plus chemotherapy improved outcomes" in pub.abstract
        assert len(pub.authors) == 2
        assert pub.authors[0] == "Smith John A"
        assert pub.publication_date is not None
        assert pub.publication_date.year == 2025
        assert pub.publication_date.month == 3
        assert pub.publication_date.day == 6
        assert pub.date_revised is not None
        assert pub.date_revised.year == 2026
        assert pub.publication_type == "article"
        assert len(pub.keywords) == 3
        assert "Endometrial Neoplasms" in pub.keywords
        assert "Pembrolizumab" in pub.keywords
        assert len(pub.nct_ids) == 1
        assert pub.nct_ids[0] == "NCT03914612"

    def test_parse_minimal(self):
        root = ET.fromstring(MINIMAL_XML)
        articles = root.findall(".//PubmedArticle")
        pub = self.parser.parse_article(articles[0])

        assert pub.pmid == "12345678"
        assert pub.title == "Minimal Article"
        assert pub.journal == "Test Journal"
        assert len(pub.authors) == 1
        assert pub.authors[0] == "WHO Working Group"
        assert pub.doi is None
        assert pub.pmcid is None
        assert pub.abstract is None
        assert pub.nct_ids == []

    def test_parse_review_type(self):
        xml = """<PubmedArticleSet><PubmedArticle><MedlineCitation>
            <PMID>1</PMID>
            <Article>
                <Journal><Title>J</Title></Journal>
                <ArticleTitle>Review</ArticleTitle>
                <PublicationTypeList>
                  <PublicationType>Review</PublicationType>
                  <PublicationType>Systematic Review</PublicationType>
                </PublicationTypeList>
            </Article>
        </MedlineCitation></PubmedArticle></PubmedArticleSet>"""
        root = ET.fromstring(xml)
        pub = self.parser.parse_article(root.findall(".//PubmedArticle")[0])
        assert pub.publication_type == "review"

    def test_parse_no_databank(self):
        xml = """<PubmedArticleSet><PubmedArticle><MedlineCitation>
            <PMID>1</PMID>
            <Article>
                <Journal><Title>J</Title></Journal>
                <ArticleTitle>T</ArticleTitle>
            </Article>
        </MedlineCitation></PubmedArticle></PubmedArticleSet>"""
        root = ET.fromstring(xml)
        pub = self.parser.parse_article(root.findall(".//PubmedArticle")[0])
        assert pub.nct_ids == []

    def test_year_only_date(self):
        xml = """<PubmedArticleSet><PubmedArticle><MedlineCitation>
            <PMID>1</PMID>
            <DateRevised><Year>2024</Year></DateRevised>
            <Article>
                <Journal><Title>J</Title><JournalIssue><PubDate><Year>2023</Year></PubDate></JournalIssue></Journal>
                <ArticleTitle>T</ArticleTitle>
            </Article>
        </MedlineCitation></PubmedArticle></PubmedArticleSet>"""
        root = ET.fromstring(xml)
        pub = self.parser.parse_article(root.findall(".//PubmedArticle")[0])
        assert pub.publication_date is not None
        assert pub.publication_date.year == 2023
        assert pub.publication_date.month == 1
        assert pub.publication_date.day == 1
        assert pub.date_revised is not None
        assert pub.date_revised.year == 2024
        assert pub.date_revised.month == 1
        assert pub.date_revised.day == 1
