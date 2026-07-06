"""Parse PubMed EFetch XML response to internal structures."""

from __future__ import annotations

from datetime import date
from xml.etree import ElementTree as ET


class ParsedPublication:
    def __init__(self) -> None:
        self.pmid: str | None = None
        self.doi: str | None = None
        self.pmcid: str | None = None
        self.title: str | None = None
        self.abstract: str | None = None
        self.journal: str | None = None
        self.authors: list[str] = []
        self.publication_date: date | None = None
        self.date_revised: date | None = None
        self.publication_type: str | None = None
        self.keywords: list[str] = []
        self.nct_ids: list[str] = []


class PubMedParser:
    def parse_article(self, article_elem: ET.Element) -> ParsedPublication:
        pub = ParsedPublication()
        medline = article_elem.find("MedlineCitation")
        if medline is None:
            return pub

        self._parse_pmid(pub, medline)
        self._parse_dates(pub, medline)
        self._parse_article(pub, medline.find("Article"))
        self._parse_mesh(pub, medline.find("MeshHeadingList"))
        self._parse_databanks(pub, medline.find("DataBankList"))

        pubmed_data = article_elem.find("PubmedData")
        if pubmed_data is not None:
            self._parse_article_ids(pub, pubmed_data.find("ArticleIdList"))

        return pub

    def _parse_pmid(self, pub: ParsedPublication, medline: ET.Element) -> None:
        pmid_elem = medline.find("PMID")
        if pmid_elem is not None and pmid_elem.text:
            pub.pmid = pmid_elem.text.strip()

    def _parse_dates(self, pub: ParsedPublication, medline: ET.Element) -> None:
        dr_elem = medline.find("DateRevised")
        if dr_elem is not None:
            pub.date_revised = self._parse_date_from_elements(dr_elem)

    def _parse_article(self, pub: ParsedPublication, article: ET.Element | None) -> None:
        if article is None:
            return
        pub.title = _elem_text(article.find("ArticleTitle"))
        pub.abstract = self._parse_abstract(article.find("Abstract"))
        journal_elem = article.find("Journal")
        if journal_elem is not None:
            title_elem = journal_elem.find("Title")
            if title_elem is not None and title_elem.text:
                pub.journal = title_elem.text.strip()
        self._parse_authors(pub, article.find("AuthorList"))
        self._parse_pub_types(pub, article.find("PublicationTypeList"))
        self._parse_article_date(pub, article)

    def _parse_abstract(self, abstract: ET.Element | None) -> str | None:
        if abstract is None:
            return None
        parts: list[str] = []
        for at in abstract.findall("AbstractText"):
            label = at.get("Label", "")
            text = (
                " ".join(at.itertext()).strip() if at.text or list(at) else (at.text or "").strip()
            )
            if label:
                parts.append(f"{label}: {text}")
            else:
                parts.append(text)
        result = "\n".join(parts).strip()
        return result or None

    def _parse_authors(self, pub: ParsedPublication, author_list: ET.Element | None) -> None:
        if author_list is None:
            return
        for author in author_list.findall("Author"):
            last = _elem_text(author.find("LastName"))
            fore = _elem_text(author.find("ForeName"))
            initials = _elem_text(author.find("Initials"))
            collective = _elem_text(author.find("CollectiveName"))
            if collective:
                pub.authors.append(collective)
            elif last:
                name = last
                if fore:
                    name = f"{last} {fore}"
                elif initials:
                    name = f"{last} {initials}"
                pub.authors.append(name)

    def _parse_pub_types(self, pub: ParsedPublication, pt_list: ET.Element | None) -> None:
        if pt_list is None:
            return
        types: list[str] = []
        for pt in pt_list.findall("PublicationType"):
            if pt.text:
                types.append(pt.text.strip())
        pub.publication_type = self._map_publication_type(types)

    def _parse_article_date(self, pub: ParsedPublication, article: ET.Element) -> None:
        for tag in ("ArticleDate", "Journal/JournalIssue/PubDate"):
            date_elem = article.find(tag)
            if date_elem is not None:
                parsed = self._parse_date_from_elements(date_elem)
                if parsed:
                    pub.publication_date = parsed
                    return

    def _parse_mesh(self, pub: ParsedPublication, mesh_list: ET.Element | None) -> None:
        if mesh_list is None:
            return
        for mh in mesh_list.findall("MeshHeading"):
            desc = mh.find("DescriptorName")
            if desc is not None and desc.text:
                pub.keywords.append(desc.text.strip())

    def _parse_databanks(self, pub: ParsedPublication, db_list: ET.Element | None) -> None:
        if db_list is None:
            return
        for db in db_list.findall("DataBank"):
            name_elem = db.find("DataBankName")
            if name_elem is None or not name_elem.text:
                continue
            if "ClinicalTrials.gov" not in name_elem.text:
                continue
            acc_list = db.find("AccessionNumberList")
            if acc_list is None:
                continue
            for acc in acc_list.findall("AccessionNumber"):
                if acc.text and acc.text.strip().upper().startswith("NCT"):
                    pub.nct_ids.append(acc.text.strip().upper())

    def _parse_article_ids(self, pub: ParsedPublication, id_list: ET.Element | None) -> None:
        if id_list is None:
            return
        for aid in id_list.findall("ArticleId"):
            id_type = aid.get("IdType", "")
            if id_type == "doi" and aid.text:
                pub.doi = aid.text.strip()
            elif id_type == "pmc" and aid.text and not pub.pmcid:
                pub.pmcid = aid.text.strip()

    @staticmethod
    def _map_publication_type(types: list[str]) -> str | None:
        joined = " ".join(types).lower()
        if "review" in joined:
            return "review"
        if "letter" in joined:
            return "letter"
        if "abstract" in joined or "meeting" in joined or "conference" in joined:
            return "abstract"
        if "preprint" in joined:
            return "preprint"
        if "journal article" in joined or "article" in joined:
            return "article"
        if types:
            return "article"
        return None

    @staticmethod
    def _parse_date_from_elements(parent: ET.Element) -> date | None:
        year = _int_elem(parent.find("Year"))
        if not year:
            return None
        month = _int_elem(parent.find("Month"))
        day = _int_elem(parent.find("Day"))
        try:
            return date(year, month or 1, day or 1)
        except ValueError:
            return None


def _elem_text(elem: ET.Element | None) -> str | None:
    if elem is None:
        return None
    text = "".join(elem.itertext()).strip()
    return text if text else None


def _int_elem(elem: ET.Element | None) -> int | None:
    if elem is None or not elem.text:
        return None
    try:
        return int(elem.text.strip())
    except ValueError:
        return None
