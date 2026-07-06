"""Parse the EMA 'Medicines output' XLSX export to internal structures.

The export's exact column headers drift slightly between releases, so columns are
resolved by normalized substring match rather than a fixed position/name.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from datetime import date, datetime
from io import BytesIO


class ParsedEMARecord:
    def __init__(self) -> None:
        self.external_id: str | None = None
        self.asset_name: str | None = None
        self.asset_aliases: list[str] = []
        self.approval_status: str | None = None
        self.authorisation_date: date | None = None
        self.therapeutic_area: str | None = None
        self.product_number: str | None = None
        self.orphan: bool = False
        self.epar_url: str | None = None
        self.row_index: int | None = None


_STATUS_MAP = {
    "authorised": "approved",
    "withdrawn": "withdrawn",
    "refused": "rejected",
    "suspended": "withdrawn",
}


def _normalize_header(value) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


def _find_column(headers: list[str], *substrings: str) -> int | None:
    for index, header in enumerate(headers):
        if all(sub in header for sub in substrings):
            return index
    return None


class EMAParser:
    def parse_workbook(self, content: bytes) -> Iterator[ParsedEMARecord]:
        import openpyxl

        workbook = openpyxl.load_workbook(BytesIO(content), read_only=True, data_only=True)
        sheet = workbook.worksheets[0]
        rows = sheet.iter_rows(values_only=True)

        raw_headers = next(rows, None)
        if not raw_headers:
            return
        headers = [_normalize_header(h) for h in raw_headers]

        col_name = _find_column(headers, "medicine", "name") or _find_column(headers, "name")
        col_inn = _find_column(headers, "inn") or _find_column(headers, "common", "name")
        col_substance = _find_column(headers, "active", "substance")
        col_status = _find_column(headers, "authorisation", "status") or _find_column(
            headers, "medicine", "status"
        )
        col_date = _find_column(headers, "authorisation", "date") or _find_column(
            headers, "opinion", "date"
        )
        col_area = _find_column(headers, "therapeutic", "area")
        col_product_no = _find_column(headers, "product", "number") or _find_column(
            headers, "procedure", "number"
        )
        col_orphan = _find_column(headers, "orphan")
        col_url = _find_column(headers, "url") or _find_column(headers, "epar")

        for row_index, row in enumerate(rows, start=2):
            if col_name is None or col_name >= len(row) or not row[col_name]:
                continue
            parsed = ParsedEMARecord()
            parsed.row_index = row_index
            parsed.asset_name = str(row[col_name]).strip().title()

            for col in (col_inn, col_substance):
                if col is not None and col < len(row) and row[col]:
                    alias = str(row[col]).strip().title()
                    if alias.casefold() != parsed.asset_name.casefold() and alias not in (
                        parsed.asset_aliases
                    ):
                        parsed.asset_aliases.append(alias)

            if col_status is not None and col_status < len(row) and row[col_status]:
                status_raw = str(row[col_status]).strip().lower()
                parsed.approval_status = _STATUS_MAP.get(status_raw, "pending")

            if col_date is not None and col_date < len(row) and row[col_date]:
                parsed.authorisation_date = _coerce_date(row[col_date])

            if col_area is not None and col_area < len(row) and row[col_area]:
                parsed.therapeutic_area = str(row[col_area]).strip()

            if col_product_no is not None and col_product_no < len(row) and row[col_product_no]:
                parsed.product_number = str(row[col_product_no]).strip()

            if col_orphan is not None and col_orphan < len(row) and row[col_orphan]:
                parsed.orphan = str(row[col_orphan]).strip().lower() in {"yes", "y", "true", "1"}

            if col_url is not None and col_url < len(row) and row[col_url]:
                parsed.epar_url = str(row[col_url]).strip()

            parsed.external_id = parsed.product_number or (
                f"{parsed.asset_name}:{parsed.row_index}"
            )
            yield parsed

        workbook.close()


def _coerce_date(value) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d %B %Y"):
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                continue
    return None
