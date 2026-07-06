"""ClinicalTrials.gov API v2 connector."""

import asyncio
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from workers.base.connector import BaseConnector, ConnectorResult, HealthcheckResult
from workers.connectors.clinicaltrials.parser import ClinicalTrialsParser

logger = structlog.get_logger(__name__)
settings = get_settings()

CT_API_BASE = settings.CLINICALTRIALS_API_BASE_URL
PAGE_SIZE = 100
MAX_RETRIES = settings.CLINICALTRIALS_MAX_RETRIES
RATE_LIMIT_DELAY = 1.0 / settings.CLINICALTRIALS_RATE_LIMIT_REQUESTS_PER_SECOND


class ClinicalTrialsConnector(BaseConnector):
    SOURCE_SLUG = "clinicaltrials_gov"

    def __init__(self) -> None:
        super().__init__()
        self.parser = ClinicalTrialsParser()

    def validate_config(self) -> bool:
        return bool(CT_API_BASE)

    async def healthcheck(self) -> HealthcheckResult:
        """Lightweight connectivity probe against ClinicalTrials.gov API v2 (VLAEG phase L)."""
        result = HealthcheckResult(self.SOURCE_SLUG)

        if not self.validate_config():
            result.status = "config_error"
            result.detail = "CLINICALTRIALS_API_BASE_URL not configured"
            return result

        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(
                base_url=CT_API_BASE,
                timeout=10.0,
                headers={
                    "User-Agent": "GennomX-AI/0.1 (data@gennomx.ai)",
                    "Accept": "application/json",
                },
            ) as client:
                response = await client.get("/studies", params={"format": "json", "pageSize": 1})
                response.raise_for_status()
                data = response.json()
            result.latency_ms = (time.perf_counter() - started) * 1000.0
            if isinstance(data, dict) and "studies" in data:
                result.ok = True
                result.status = "ok"
                result.detail = "API v2 reachable; 1 study fetched"
            else:
                result.status = "error"
                result.detail = "Unexpected response shape (no 'studies' field)"
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
        conditions: list[str] | None = None,
        interventions: list[str] | None = None,
        max_records: int | None = None,
        updated_since: datetime | None = None,
        page_handler: Callable[[list[dict]], Awaitable[None]] | None = None,
        **kwargs,
    ) -> ConnectorResult:
        result = ConnectorResult(self.SOURCE_SLUG)
        self.logger.info("ct_connector_started", job_type=job_type)

        async with httpx.AsyncClient(
            base_url=CT_API_BASE,
            timeout=30.0,
            headers={
                "User-Agent": "GennomX-AI/0.1 (data@gennomx.ai)",
                "Accept": "application/json",
            },
        ) as client:
            try:
                if job_type == "incremental":
                    cursor = updated_since or datetime.now(UTC)
                    since = (
                        cursor - timedelta(days=settings.CLINICALTRIALS_INCREMENTAL_LOOKBACK_DAYS)
                    ).strftime("%Y-%m-%d")
                    incremental = f"AREA[LastUpdatePostDate]RANGE[{since}, MAX]"
                    query = f"({query}) AND {incremental}" if query else incremental
                    max_records = max_records or settings.CLINICALTRIALS_MAX_RECORDS_PER_RUN
                    result.metadata["incremental_since"] = since
                params = self._build_search_params(query, conditions, interventions)
                await self._paginate(client, params, max_records, result, page_handler)

            except Exception as e:
                result.add_error("connector_error", str(e))

        result.finish()
        self.logger.info(
            "ct_connector_finished",
            fetched=result.records_fetched,
            rejected=result.records_rejected,
            duration=result.duration_seconds,
        )
        return result

    def _build_search_params(
        self,
        query: str | None,
        conditions: list[str] | None,
        interventions: list[str] | None,
    ) -> dict:
        params: dict[str, Any] = {
            "format": "json",
            "pageSize": PAGE_SIZE,
            "fields": (
                "protocolSection.identificationModule,"
                "protocolSection.statusModule,"
                "protocolSection.sponsorCollaboratorsModule,"
                "protocolSection.descriptionModule,"
                "protocolSection.conditionsModule,"
                "protocolSection.designModule,"
                "protocolSection.armsInterventionsModule,"
                "protocolSection.eligibilityModule,"
                "protocolSection.contactsLocationsModule,"
                "protocolSection.outcomesModule,"
                "resultsSection"
            ),
        }
        if query:
            params["query.term"] = query
        if conditions:
            params["query.cond"] = " OR ".join(conditions)
        if interventions:
            params["query.intr"] = " OR ".join(interventions)
        return params

    async def _paginate(
        self,
        client: httpx.AsyncClient,
        params: dict,
        max_records: int | None,
        result: ConnectorResult,
        page_handler: Callable[[list[dict]], Awaitable[None]] | None = None,
    ) -> None:
        next_token: str | None = None
        page = 0

        while True:
            page += 1
            page_params = dict(params)
            if next_token:
                page_params["pageToken"] = next_token

            try:
                response = await self._fetch_page(client, page_params)
                data = response.json()
            except Exception as e:
                result.add_error("fetch_error", f"Page {page}: {e}")
                break

            page_studies = data.get("studies", [])
            remaining = max_records - result.records_fetched if max_records else None
            if remaining is not None:
                page_studies = page_studies[: max(remaining, 0)]
            parsed_payloads: list[dict] = []
            for raw in page_studies:
                try:
                    parsed_payloads.append(
                        {
                            "raw": raw,
                            "parsed": self.parser.parse_study(raw),
                            "hash": self.compute_hash(raw),
                        }
                    )
                except Exception as e:
                    result.records_rejected += 1
                    identification = raw.get("protocolSection", {}).get("identificationModule", {})
                    result.add_error("parse_error", str(e), {"nct_id": identification.get("nctId")})
            result.records_fetched += len(page_studies)
            if page_handler:
                await page_handler(parsed_payloads)
            else:
                result.raw_payloads.extend(parsed_payloads)
            self.logger.debug("ct_page_fetched", page=page, count=len(page_studies))

            next_token = data.get("nextPageToken")
            if not next_token:
                break
            if max_records and result.records_fetched >= max_records:
                result.metadata["next_page_token"] = next_token
                result.add_error(
                    "record_limit_reached",
                    f"Run stopped at configured limit of {max_records} records",
                )
                break

            await asyncio.sleep(RATE_LIMIT_DELAY)

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def _fetch_page(self, client: httpx.AsyncClient, params: dict) -> httpx.Response:
        response = await client.get("/studies", params=params)
        response.raise_for_status()
        return response
