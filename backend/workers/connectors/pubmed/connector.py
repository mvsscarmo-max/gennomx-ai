"""PubMed E-utilities connector."""

import asyncio
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from xml.etree import ElementTree as ET

import httpx
import structlog
from defusedxml.ElementTree import fromstring as defused_fromstring
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from workers.base.connector import BaseConnector, ConnectorResult, HealthcheckResult
from workers.connectors.pubmed.parser import PubMedParser

logger = structlog.get_logger(__name__)
settings = get_settings()

PUBMED_API_BASE = settings.PUBMED_API_BASE_URL
PUBMED_MAX_RETRIES = settings.PUBMED_MAX_RETRIES
PUBMED_RATE_LIMIT_DELAY = 1.0 / settings.PUBMED_RATE_LIMIT_REQUESTS_PER_SECOND
PUBMED_BATCH_SIZE = 100


class PubMedConnector(BaseConnector):
    SOURCE_SLUG = "pubmed"

    def __init__(self) -> None:
        super().__init__()
        self.parser = PubMedParser()

    def validate_config(self) -> bool:
        return bool(PUBMED_API_BASE)

    async def healthcheck(self) -> HealthcheckResult:
        result = HealthcheckResult(self.SOURCE_SLUG)
        if not self.validate_config():
            result.status = "config_error"
            result.detail = "PUBMED_API_BASE_URL not configured"
            return result

        started = time.perf_counter()
        params = self._base_params()
        params.update({"db": "pubmed", "retmode": "json"})
        try:
            async with httpx.AsyncClient(base_url=PUBMED_API_BASE, timeout=10.0) as client:
                response = await client.get("/einfo.fcgi", params=params)
                response.raise_for_status()
                data = response.json()
            result.latency_ms = (time.perf_counter() - started) * 1000.0
            if isinstance(data, dict) and "einforesult" in data:
                result.ok = True
                result.status = "ok"
                desc = data.get("einforesult", {}).get("dbinfo", {}).get("description", "unknown")
                result.detail = f"E-utilities reachable (PubMed db: {desc})"
            else:
                result.status = "error"
                result.detail = "Unexpected response shape (no 'einforesult')"
        except httpx.TimeoutException as e:
            result.latency_ms = (time.perf_counter() - started) * 1000.0
            result.status = "unreachable"
            result.detail = f"timeout: {e}"
        except httpx.HTTPError as e:
            result.latency_ms = (time.perf_counter() - started) * 1000.0
            result.status = "unreachable"
            result.detail = str(e)
        except Exception as e:
            result.status = "error"
            result.detail = str(e)
        return result

    async def run(
        self,
        job_type: str = "incremental",
        query: str | None = None,
        max_records: int | None = None,
        updated_since: datetime | None = None,
        page_handler: Callable[[list[dict]], Awaitable[None]] | None = None,
        **kwargs,
    ) -> ConnectorResult:
        result = ConnectorResult(self.SOURCE_SLUG)
        self.logger.info("pubmed_connector_started", job_type=job_type)

        params_base = self._base_params()
        async with httpx.AsyncClient(base_url=PUBMED_API_BASE, timeout=30.0) as client:
            try:
                final_query = query or settings.PUBMED_DEFAULT_QUERY
                if job_type == "incremental":
                    cursor = updated_since or datetime.now(UTC)
                    since = (
                        cursor - timedelta(days=settings.PUBMED_INCREMENTAL_LOOKBACK_DAYS)
                    ).strftime("%Y/%m/%d")
                    date_filter = f'("{since}"[EDAT] : "3000"[EDAT])'
                    final_query = f"({final_query}) AND {date_filter}"
                    max_records = max_records or settings.PUBMED_MAX_RECORDS_PER_RUN
                    result.metadata["incremental_since"] = since

                webenv, query_key, total_count = await self._esearch(
                    client, params_base, final_query
                )
                if webenv is None or query_key is None or total_count == 0:
                    result.metadata["esearch_count"] = 0
                    result.finish()
                    return result

                result.metadata["esearch_count"] = total_count
                await self._paginate_efetch(
                    client,
                    params_base,
                    webenv,
                    query_key,
                    total_count,
                    max_records,
                    result,
                    page_handler,
                )

            except Exception as e:
                result.add_error("connector_error", str(e))

        result.finish()
        self.logger.info(
            "pubmed_connector_finished",
            fetched=result.records_fetched,
            rejected=result.records_rejected,
            duration=result.duration_seconds,
        )
        return result

    async def _esearch(
        self, client: httpx.AsyncClient, base_params: dict, query: str
    ) -> tuple[str | None, str | None, int]:
        params = dict(base_params)
        params["db"] = "pubmed"
        params["term"] = query
        params["usehistory"] = "y"
        params["retmode"] = "json"
        params["retmax"] = "0"

        response = await self._fetch(client, "/esearch.fcgi", params)
        data = response.json()
        result = data.get("esearchresult", {})
        webenv = result.get("webenv")
        query_key = result.get("querykey")
        total = int(result.get("count", 0))
        return webenv, query_key, total

    async def _paginate_efetch(
        self,
        client: httpx.AsyncClient,
        base_params: dict,
        webenv: str,
        query_key: str,
        total_count: int,
        max_records: int | None,
        result: ConnectorResult,
        page_handler: Callable[[list[dict]], Awaitable[None]] | None = None,
    ) -> None:
        limit = min(total_count, max_records) if max_records else total_count
        retstart = 0

        while retstart < limit:
            batch_size = min(PUBMED_BATCH_SIZE, limit - retstart)
            params = dict(base_params)
            params["db"] = "pubmed"
            params["WebEnv"] = webenv
            params["query_key"] = query_key
            params["retstart"] = str(retstart)
            params["retmax"] = str(batch_size)
            params["retmode"] = "xml"

            try:
                response = await self._fetch(client, "/efetch.fcgi", params)
                xml_text = response.text
            except Exception as e:
                result.add_error("fetch_error", f"EFetch retstart={retstart}: {e}")
                break

            parsed_payloads: list[dict] = []
            try:
                root = defused_fromstring(xml_text)
                articles = root.findall(".//PubmedArticle")
                for article_elem in articles:
                    try:
                        parsed = self.parser.parse_article(article_elem)
                        article_xml = ET.tostring(article_elem, encoding="unicode")
                        payload = {
                            "raw": {"xml": article_xml},
                            "parsed": parsed,
                            "hash": self.compute_hash(article_xml),
                        }
                        parsed_payloads.append(payload)
                    except Exception as e:
                        result.records_rejected += 1
                        result.add_error("parse_error", str(e))
            except ET.ParseError as e:
                result.add_error("parse_error", f"XML parse error: {e}")
                break

            result.records_fetched += len(parsed_payloads)
            self.logger.debug("pubmed_page_fetched", retstart=retstart, count=len(parsed_payloads))

            if page_handler and parsed_payloads:
                await page_handler(parsed_payloads)
            elif not page_handler:
                result.raw_payloads.extend(parsed_payloads)

            retstart += batch_size

            if max_records and result.records_fetched >= max_records:
                result.metadata["next_retstart"] = retstart
                result.add_error(
                    "record_limit_reached",
                    f"Run stopped at configured limit of {max_records} records",
                )
                break

            await asyncio.sleep(PUBMED_RATE_LIMIT_DELAY)

    @retry(
        stop=stop_after_attempt(PUBMED_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def _fetch(self, client: httpx.AsyncClient, path: str, params: dict) -> httpx.Response:
        response = await client.get(path, params=params)
        response.raise_for_status()
        return response

    @staticmethod
    def _base_params() -> dict[str, str]:
        params: dict[str, str] = {"tool": "gennomx"}
        if settings.NCBI_EMAIL:
            params["email"] = settings.NCBI_EMAIL
        if settings.NCBI_API_KEY:
            params["api_key"] = settings.NCBI_API_KEY
        return params
