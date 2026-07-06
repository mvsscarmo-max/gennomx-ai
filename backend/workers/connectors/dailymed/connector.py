"""DailyMed Structured Product Labeling (SPL) list connector."""

import asyncio
import time
from collections.abc import Awaitable, Callable

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from workers.base.connector import BaseConnector, ConnectorResult, HealthcheckResult
from workers.connectors.dailymed.parser import DailyMedParser

logger = structlog.get_logger(__name__)
settings = get_settings()

DAILYMED_API_BASE = settings.DAILYMED_API_BASE_URL
DAILYMED_MAX_RETRIES = settings.DAILYMED_MAX_RETRIES
DAILYMED_RATE_LIMIT_DELAY = 1.0 / settings.DAILYMED_RATE_LIMIT_REQUESTS_PER_SECOND
DAILYMED_PAGE_SIZE = 100


class DailyMedConnector(BaseConnector):
    SOURCE_SLUG = "dailymed"

    def __init__(self) -> None:
        super().__init__()
        self.parser = DailyMedParser()

    def validate_config(self) -> bool:
        return bool(DAILYMED_API_BASE)

    async def healthcheck(self) -> HealthcheckResult:
        result = HealthcheckResult(self.SOURCE_SLUG)
        if not self.validate_config():
            result.status = "config_error"
            result.detail = "DAILYMED_API_BASE_URL not configured"
            return result

        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(base_url=DAILYMED_API_BASE, timeout=10.0) as client:
                response = await client.get(
                    "/services/v2/spls.json", params={"page": "1", "pagesize": "1"}
                )
                response.raise_for_status()
                data = response.json()
            result.latency_ms = (time.perf_counter() - started) * 1000.0
            if isinstance(data, dict) and "data" in data:
                result.ok = True
                result.status = "ok"
                total = data.get("metadata", {}).get("total_elements")
                result.detail = f"spls.json reachable (total labels: {total})"
            else:
                result.status = "error"
                result.detail = "Unexpected response shape (no 'data')"
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
        max_records: int | None = None,
        page_handler: Callable[[list[dict]], Awaitable[None]] | None = None,
        **kwargs,
    ) -> ConnectorResult:
        result = ConnectorResult(self.SOURCE_SLUG)
        self.logger.info("dailymed_connector_started", job_type=job_type)

        limit = max_records or settings.DAILYMED_MAX_RECORDS_PER_RUN
        if job_type == "incremental":
            result.metadata["note"] = (
                "DailyMed spls.json has no reliable delta filter; incremental runs are "
                "bounded by DAILYMED_MAX_RECORDS_PER_RUN and rely on idempotent upserts."
            )

        page = 1
        fetched_total = 0
        async with httpx.AsyncClient(base_url=DAILYMED_API_BASE, timeout=30.0) as client:
            try:
                while fetched_total < limit:
                    page_size = min(DAILYMED_PAGE_SIZE, limit - fetched_total)
                    response = await self._fetch(client, page, page_size)
                    data = response.json()
                    records = data.get("data", [])
                    if not records:
                        break

                    parsed_payloads: list[dict] = []
                    for record in records:
                        try:
                            parsed = self.parser.parse_record(record)
                            if not parsed.asset_name or not parsed.external_id:
                                result.records_rejected += 1
                                continue
                            payload = {
                                "raw": record,
                                "parsed": parsed,
                                "hash": self.compute_hash(record),
                            }
                            parsed_payloads.append(payload)
                        except Exception as e:
                            result.records_rejected += 1
                            result.add_error("parse_error", str(e))

                    result.records_fetched += len(parsed_payloads)
                    fetched_total += len(records)
                    if page_handler and parsed_payloads:
                        await page_handler(parsed_payloads)
                    elif not page_handler:
                        result.raw_payloads.extend(parsed_payloads)

                    metadata = data.get("metadata", {})
                    if not metadata.get("next_page_url") or len(records) < page_size:
                        break
                    page += 1
                    await asyncio.sleep(DAILYMED_RATE_LIMIT_DELAY)

            except Exception as e:
                result.add_error("connector_error", str(e))

        result.finish()
        self.logger.info(
            "dailymed_connector_finished",
            fetched=result.records_fetched,
            rejected=result.records_rejected,
            duration=result.duration_seconds,
        )
        return result

    @retry(
        stop=stop_after_attempt(DAILYMED_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def _fetch(self, client: httpx.AsyncClient, page: int, page_size: int) -> httpx.Response:
        response = await client.get(
            "/services/v2/spls.json",
            params={"page": str(page), "pagesize": str(page_size)},
        )
        response.raise_for_status()
        return response
