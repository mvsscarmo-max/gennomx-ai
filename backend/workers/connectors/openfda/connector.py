"""openFDA Drugs@FDA (drugsfda) connector."""

import asyncio
import time
from collections.abc import Awaitable, Callable

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from workers.base.connector import BaseConnector, ConnectorResult, HealthcheckResult
from workers.connectors.openfda.parser import OpenFDAParser

logger = structlog.get_logger(__name__)
settings = get_settings()

OPENFDA_API_BASE = settings.OPENFDA_API_BASE_URL
OPENFDA_MAX_RETRIES = settings.OPENFDA_MAX_RETRIES
OPENFDA_RATE_LIMIT_DELAY = 1.0 / settings.OPENFDA_RATE_LIMIT_REQUESTS_PER_SECOND
OPENFDA_BATCH_SIZE = 100
OPENFDA_MAX_SKIP_LIMIT = 25000  # openFDA hard cap on skip + limit


class OpenFDAConnector(BaseConnector):
    SOURCE_SLUG = "openfda"

    def __init__(self) -> None:
        super().__init__()
        self.parser = OpenFDAParser()

    def validate_config(self) -> bool:
        return bool(OPENFDA_API_BASE)

    async def healthcheck(self) -> HealthcheckResult:
        result = HealthcheckResult(self.SOURCE_SLUG)
        if not self.validate_config():
            result.status = "config_error"
            result.detail = "OPENFDA_API_BASE_URL not configured"
            return result

        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(base_url=OPENFDA_API_BASE, timeout=10.0) as client:
                response = await client.get(
                    "/drug/drugsfda.json", params=self._base_params(limit=1)
                )
                response.raise_for_status()
                data = response.json()
            result.latency_ms = (time.perf_counter() - started) * 1000.0
            if isinstance(data, dict) and "results" in data:
                result.ok = True
                result.status = "ok"
                total = data.get("meta", {}).get("results", {}).get("total")
                result.detail = f"drugsfda reachable (total records: {total})"
            else:
                result.status = "error"
                result.detail = "Unexpected response shape (no 'results')"
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
        self.logger.info("openfda_connector_started", job_type=job_type)

        limit = max_records or settings.OPENFDA_MAX_RECORDS_PER_RUN
        if job_type == "incremental":
            result.metadata["note"] = (
                "openFDA drugsfda has no reliable delta filter; incremental runs are "
                "bounded by OPENFDA_MAX_RECORDS_PER_RUN and rely on idempotent upserts."
            )

        skip = 0
        async with httpx.AsyncClient(base_url=OPENFDA_API_BASE, timeout=30.0) as client:
            try:
                while skip < limit and skip < OPENFDA_MAX_SKIP_LIMIT:
                    batch_size = min(OPENFDA_BATCH_SIZE, limit - skip)
                    response = await self._fetch(client, skip, batch_size)
                    data = response.json()
                    records = data.get("results", [])
                    if not records:
                        break

                    parsed_payloads: list[dict] = []
                    for record in records:
                        try:
                            parsed = self.parser.parse_record(record)
                            if not parsed.asset_name or not parsed.application_number:
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
                    if page_handler and parsed_payloads:
                        await page_handler(parsed_payloads)
                    elif not page_handler:
                        result.raw_payloads.extend(parsed_payloads)

                    skip += len(records)
                    if len(records) < batch_size:
                        break
                    await asyncio.sleep(OPENFDA_RATE_LIMIT_DELAY)

            except Exception as e:
                result.add_error("connector_error", str(e))

        result.finish()
        self.logger.info(
            "openfda_connector_finished",
            fetched=result.records_fetched,
            rejected=result.records_rejected,
            duration=result.duration_seconds,
        )
        return result

    @retry(
        stop=stop_after_attempt(OPENFDA_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def _fetch(self, client: httpx.AsyncClient, skip: int, limit: int) -> httpx.Response:
        params = self._base_params(limit=limit)
        params["skip"] = str(skip)
        response = await client.get("/drug/drugsfda.json", params=params)
        response.raise_for_status()
        return response

    @staticmethod
    def _base_params(limit: int) -> dict[str, str]:
        params: dict[str, str] = {"limit": str(limit)}
        if settings.OPENFDA_API_KEY:
            params["api_key"] = settings.OPENFDA_API_KEY
        return params
