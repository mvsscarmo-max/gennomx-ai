"""Open Targets Platform GraphQL connector.

Populates the ``targets`` catalog with biological-target / disease-association records.
Discovery is seeded by a configurable list of disease terms (``OPEN_TARGETS_SEED_DISEASE_TERMS``)
rather than by a full crawl, since Open Targets does not expose a stable full-export or
delta-since endpoint suitable for incremental polling.
"""

import asyncio
import time
from collections.abc import Awaitable, Callable

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from workers.base.connector import BaseConnector, ConnectorResult, HealthcheckResult
from workers.connectors.opentargets.parser import OpenTargetsParser

logger = structlog.get_logger(__name__)
settings = get_settings()

OPEN_TARGETS_URL = settings.OPEN_TARGETS_GRAPHQL_URL
OPEN_TARGETS_MAX_RETRIES = settings.OPEN_TARGETS_MAX_RETRIES
OPEN_TARGETS_RATE_LIMIT_DELAY = 1.0 / settings.OPEN_TARGETS_RATE_LIMIT_REQUESTS_PER_SECOND
ASSOCIATED_TARGETS_PAGE_SIZE = 25

SEARCH_QUERY = """
query SearchDisease($q: String!) {
  search(queryString: $q, entityNames: ["disease"], page: {index: 0, size: 1}) {
    hits { id name entity }
  }
}
"""

DISEASE_TARGETS_QUERY = """
query DiseaseTargets($efoId: String!, $size: Int!) {
  disease(efoId: $efoId) {
    id
    name
    associatedTargets(page: {index: 0, size: $size}) {
      count
      rows {
        score
        target {
          id
          approvedSymbol
          approvedName
          biotype
          synonyms { label }
          proteinIds { id source }
        }
      }
    }
  }
}
"""

HEALTHCHECK_QUERY = "query Health { meta { apiVersion { x y z } } }"


class OpenTargetsConnector(BaseConnector):
    SOURCE_SLUG = "open_targets"

    def __init__(self) -> None:
        super().__init__()
        self.parser = OpenTargetsParser()

    def validate_config(self) -> bool:
        return bool(OPEN_TARGETS_URL)

    async def healthcheck(self) -> HealthcheckResult:
        result = HealthcheckResult(self.SOURCE_SLUG)
        if not self.validate_config():
            result.status = "config_error"
            result.detail = "OPEN_TARGETS_GRAPHQL_URL not configured"
            return result

        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(OPEN_TARGETS_URL, json={"query": HEALTHCHECK_QUERY})
                response.raise_for_status()
                data = response.json()
            result.latency_ms = (time.perf_counter() - started) * 1000.0
            if isinstance(data, dict) and "data" in data and not data.get("errors"):
                result.ok = True
                result.status = "ok"
                version = data.get("data", {}).get("meta", {}).get("apiVersion", {})
                result.detail = f"GraphQL reachable (apiVersion: {version})"
            else:
                result.status = "error"
                result.detail = f"GraphQL errors: {data.get('errors')}"
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
        seed_terms: list[str] | None = None,
        page_handler: Callable[[list[dict]], Awaitable[None]] | None = None,
        **kwargs,
    ) -> ConnectorResult:
        result = ConnectorResult(self.SOURCE_SLUG)
        self.logger.info("opentargets_connector_started", job_type=job_type)

        limit = max_records or settings.OPEN_TARGETS_MAX_RECORDS_PER_RUN
        terms = seed_terms or [
            t.strip() for t in settings.OPEN_TARGETS_SEED_DISEASE_TERMS.split(",") if t.strip()
        ]
        result.metadata["seed_terms"] = terms
        seen_target_ids: set[str] = set()

        async with httpx.AsyncClient(timeout=30.0) as client:
            for term in terms:
                if result.records_fetched >= limit:
                    break
                try:
                    efo_id, disease_name = await self._resolve_disease(client, term)
                    if not efo_id:
                        result.metadata.setdefault("unresolved_terms", []).append(term)
                        continue

                    page_size = min(ASSOCIATED_TARGETS_PAGE_SIZE, limit - result.records_fetched)
                    rows = await self._fetch_associated_targets(client, efo_id, page_size)

                    parsed_payloads: list[dict] = []
                    for row in rows:
                        target_id = (row.get("target") or {}).get("id")
                        if not target_id or target_id in seen_target_ids:
                            continue
                        seen_target_ids.add(target_id)
                        try:
                            parsed = self.parser.parse_associated_target_row(row, disease_name)
                            if not parsed.symbol or not parsed.external_id:
                                result.records_rejected += 1
                                continue
                            payload = {
                                "raw": row,
                                "parsed": parsed,
                                "hash": self.compute_hash(row),
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

                    await asyncio.sleep(OPEN_TARGETS_RATE_LIMIT_DELAY)

                except Exception as e:
                    result.add_error("connector_error", f"term={term}: {e}")

        result.finish()
        self.logger.info(
            "opentargets_connector_finished",
            fetched=result.records_fetched,
            rejected=result.records_rejected,
            duration=result.duration_seconds,
        )
        return result

    async def _resolve_disease(
        self, client: httpx.AsyncClient, term: str
    ) -> tuple[str | None, str | None]:
        response = await self._post(client, SEARCH_QUERY, {"q": term})
        hits = response.get("data", {}).get("search", {}).get("hits", [])
        if not hits:
            return None, None
        hit = hits[0]
        return hit.get("id"), hit.get("name")

    async def _fetch_associated_targets(
        self, client: httpx.AsyncClient, efo_id: str, size: int
    ) -> list[dict]:
        response = await self._post(client, DISEASE_TARGETS_QUERY, {"efoId": efo_id, "size": size})
        disease = response.get("data", {}).get("disease") or {}
        return disease.get("associatedTargets", {}).get("rows", [])

    @retry(
        stop=stop_after_attempt(OPEN_TARGETS_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def _post(self, client: httpx.AsyncClient, query: str, variables: dict) -> dict:
        response = await client.post(
            OPEN_TARGETS_URL, json={"query": query, "variables": variables}
        )
        response.raise_for_status()
        data = response.json()
        if data.get("errors"):
            raise RuntimeError(f"GraphQL errors: {data['errors']}")
        return data
