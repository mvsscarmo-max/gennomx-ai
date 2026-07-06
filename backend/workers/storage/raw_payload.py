"""Immutable raw-payload persistence for ingestion audit and replay."""

import gzip
import json
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

from app.config import get_settings

settings = get_settings()


@dataclass(frozen=True)
class StoredRawPayload:
    path: str
    byte_count: int
    content_hash: str


def build_raw_object_path(source_slug: str, external_id: str, content_hash: str) -> str:
    """Build an immutable, partitioned object key without user-controlled separators."""
    safe_id = "".join(c for c in external_id if c.isalnum() or c in {"-", "_"})
    if not safe_id:
        raise ValueError("Raw payload external_id has no safe characters")
    now = datetime.now(UTC)
    return f"{source_slug}/{now:%Y/%m/%d}/{safe_id}/{content_hash}.json.gz"


async def store_raw_payload(
    *, source_slug: str, external_id: str, payload: dict, content_hash: str
) -> StoredRawPayload:
    """Store a canonical gzip JSON payload and return its immutable object path."""
    if settings.STORAGE_BACKEND != "supabase":
        raise RuntimeError(
            "S3 raw upload requires a dedicated signed client and is not enabled in this worker"
        )
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("Supabase raw storage credentials are not configured")

    raw_json = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    compressed = gzip.compress(raw_json, mtime=0)
    path = build_raw_object_path(source_slug, external_id, content_hash)
    bucket = settings.SUPABASE_STORAGE_BUCKET_RAW
    url = f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/{bucket}/{path}"
    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
        "Content-Type": "application/gzip",
        "x-upsert": "false",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, content=compressed, headers=headers)
        duplicate = response.status_code in {400, 409} and "duplicate" in response.text.lower()
        # Hash-addressed duplicates are idempotent; any other storage error is fatal.
        if not duplicate:
            response.raise_for_status()
    return StoredRawPayload(path=path, byte_count=len(compressed), content_hash=content_hash)
