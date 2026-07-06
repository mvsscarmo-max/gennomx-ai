"""EMA connector — downloads the official 'Medicines output' XLSX export.

This is an "official export" per AGENTS.md §10 ingestion precedence (tier 2, below a
direct API), not HTML scraping: the URL is a fixed, official EMA document endpoint.
"""

import time

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from workers.base.connector import BaseConnector, ConnectorResult, HealthcheckResult
from workers.connectors.ema.parser import EMAParser

logger = structlog.get_logger(__name__)
settings = get_settings()

EMA_EXPORT_URL = settings.EMA_MEDICINES_EXPORT_URL
EMA_MAX_RETRIES = settings.EMA_MAX_RETRIES
EMA_MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024  # 100 MB safety cap


class EMAConnector(BaseConnector):
    SOURCE_SLUG = "ema"

    def __init__(self) -> None:
        super().__init__()
        self.parser = EMAParser()

    def validate_config(self) -> bool:
        return bool(EMA_EXPORT_URL)

    async def healthcheck(self) -> HealthcheckResult:
        result = HealthcheckResult(self.SOURCE_SLUG)
        if not self.validate_config():
            result.status = "config_error"
            result.detail = "EMA_MEDICINES_EXPORT_URL not configured"
            return result

        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.head(EMA_EXPORT_URL)
                if response.status_code >= 400 or response.status_code == 405:
                    response = await client.get(EMA_EXPORT_URL, headers={"Range": "bytes=0-0"})
                response.raise_for_status()
            result.latency_ms = (time.perf_counter() - started) * 1000.0
            result.ok = True
            result.status = "ok"
            content_length = response.headers.get("content-length")
            result.detail = f"export reachable (content-length: {content_length or 'unknown'})"
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
        **kwargs,
    ) -> ConnectorResult:
        result = ConnectorResult(self.SOURCE_SLUG)
        self.logger.info("ema_connector_started", job_type=job_type)

        limit = max_records or settings.EMA_MAX_RECORDS_PER_RUN
        if job_type == "incremental":
            result.metadata["note"] = (
                "EMA official export has no delta filter; every run re-downloads the "
                "full snapshot and relies on idempotent upserts, bounded by "
                "EMA_MAX_RECORDS_PER_RUN."
            )

        try:
            content = await self._download(EMA_EXPORT_URL)
        except Exception as e:
            result.add_error("connector_error", str(e))
            result.finish()
            return result

        try:
            for record in self.parser.parse_workbook(content):
                if result.records_fetched >= limit:
                    break
                if not record.asset_name:
                    result.records_rejected += 1
                    continue
                row_bytes = repr(
                    (record.asset_name, record.approval_status, record.authorisation_date)
                ).encode()
                payload = {
                    "raw": {
                        "asset_name": record.asset_name,
                        "aliases": record.asset_aliases,
                        "status": record.approval_status,
                        "authorisation_date": (
                            record.authorisation_date.isoformat()
                            if record.authorisation_date
                            else None
                        ),
                        "therapeutic_area": record.therapeutic_area,
                        "product_number": record.product_number,
                        "orphan": record.orphan,
                        "epar_url": record.epar_url,
                    },
                    "parsed": record,
                    "hash": self.compute_hash(row_bytes.decode(errors="ignore")),
                }
                result.raw_payloads.append(payload)
                result.records_fetched += 1
        except Exception as e:
            result.add_error("parse_error", str(e))

        result.finish()
        self.logger.info(
            "ema_connector_finished",
            fetched=result.records_fetched,
            rejected=result.records_rejected,
            duration=result.duration_seconds,
        )
        return result

    @retry(
        stop=stop_after_attempt(EMA_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def _download(self, url: str) -> bytes:
        async with (
            httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client,
            client.stream("GET", url) as response,
        ):
            response.raise_for_status()
            content_length = response.headers.get("content-length")
            if content_length and int(content_length) > EMA_MAX_DOWNLOAD_BYTES:
                raise ValueError(f"EMA export exceeds size cap: {content_length} bytes")
            chunks = bytearray()
            async for chunk in response.aiter_bytes():
                chunks.extend(chunk)
                if len(chunks) > EMA_MAX_DOWNLOAD_BYTES:
                    raise ValueError("EMA export exceeded size cap during download")
            return bytes(chunks)
