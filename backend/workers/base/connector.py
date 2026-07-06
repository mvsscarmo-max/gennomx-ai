"""Base connector contract. All data source connectors must inherit from this."""

import hashlib
import json
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

import httpx
import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class ConnectorResult:
    """Standardized result from a connector run."""

    def __init__(self, source_slug: str) -> None:
        self.source_slug = source_slug
        self.started_at: datetime = datetime.now(UTC)
        self.finished_at: datetime | None = None
        self.records_fetched: int = 0
        self.records_inserted: int = 0
        self.records_updated: int = 0
        self.records_rejected: int = 0
        self.records_skipped: int = 0
        self.raw_payloads: list[dict] = []
        self.errors: list[dict] = []
        self.metadata: dict = {}

    def finish(self) -> None:
        self.finished_at = datetime.now(UTC)

    @property
    def duration_seconds(self) -> float | None:
        if self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, error_type: str, message: str, detail: dict | None = None) -> None:
        self.errors.append({"type": error_type, "message": message, "detail": detail or {}})
        logger.error(
            "connector_error", source=self.source_slug, error_type=error_type, message=message
        )

    def to_job_dict(self) -> dict:
        return {
            "records_fetched": self.records_fetched,
            "records_inserted": self.records_inserted,
            "records_updated": self.records_updated,
            "records_rejected": self.records_rejected,
            "records_skipped": self.records_skipped,
            "duration_seconds": self.duration_seconds,
            "error_summary": "; ".join(e["message"] for e in self.errors) if self.errors else None,
            "error_type": self.errors[0]["type"] if self.errors else None,
            "error_detail": {"errors": self.errors} if self.errors else None,
            "metadata": self.metadata,
        }


class HealthcheckResult:
    """Standardized result from a connector connectivity handshake (VLAEG phase L)."""

    def __init__(self, source_slug: str) -> None:
        self.source_slug = source_slug
        self.checked_at: datetime = datetime.now(UTC)
        self.ok: bool = False
        self.status: str = "unknown"  # "ok" | "config_error" | "unreachable" | "error"
        self.latency_ms: float | None = None
        self.detail: str | None = None

    def to_dict(self) -> dict:
        return {
            "source_slug": self.source_slug,
            "checked_at": self.checked_at.isoformat(),
            "ok": self.ok,
            "status": self.status,
            "latency_ms": round(self.latency_ms, 1) if self.latency_ms is not None else None,
            "detail": self.detail,
        }


class BaseConnector(ABC):
    """Abstract base class for all GennomX data source connectors."""

    SOURCE_SLUG: str = ""

    def __init__(self) -> None:
        self.logger = structlog.get_logger(self.__class__.__name__)

    @abstractmethod
    async def run(self, job_type: str = "incremental", **kwargs) -> ConnectorResult:
        """Execute the connector and return a ConnectorResult."""
        ...

    @abstractmethod
    def validate_config(self) -> bool:
        """Validate that required config/credentials are present."""
        ...

    async def healthcheck(self) -> HealthcheckResult:
        """Validate connectivity before running the connector (VLAEG phase L — Link).

        Default implementation only validates configuration/credentials. Connectors that
        reach an external API should override this to perform a lightweight read probe with
        a short timeout and explicit error handling.
        """
        result = HealthcheckResult(self.SOURCE_SLUG)
        try:
            if self.validate_config():
                result.ok = True
                result.status = "ok"
                result.detail = "config valid (no network probe implemented)"
            else:
                result.status = "config_error"
                result.detail = "validate_config() returned False"
        except Exception as e:
            result.status = "error"
            result.detail = str(e)
        return result

    async def _make_request(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        **kwargs,
    ) -> httpx.Response:
        response = await client.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    @staticmethod
    def compute_hash(payload: Any) -> str:
        """Compute SHA-256 hash of a payload for deduplication and integrity."""
        if isinstance(payload, dict | list):
            serialized = json.dumps(payload, sort_keys=True, default=str)
        else:
            serialized = str(payload)
        return hashlib.sha256(serialized.encode()).hexdigest()
