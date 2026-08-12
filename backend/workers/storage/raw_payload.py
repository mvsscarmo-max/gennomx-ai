"""Immutable raw-payload persistence for ingestion audit and replay."""

import gzip
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from app.config import get_settings

from .minio_client import delete_object, ensure_buckets_exist, get_object, put_object

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
    if settings.STORAGE_BACKEND != "minio":
        raise RuntimeError("MinIO raw upload is the only enabled storage backend in this worker")
    if not (
        settings.MINIO_ENDPOINT_URL
        and settings.MINIO_ACCESS_KEY_ID
        and settings.MINIO_SECRET_ACCESS_KEY
    ):
        raise RuntimeError("MinIO raw storage credentials are not configured")

    raw_json = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    compressed = gzip.compress(raw_json, mtime=0)
    path = build_raw_object_path(source_slug, external_id, content_hash)
    await ensure_buckets_exist(
        [
            settings.MINIO_BUCKET_RAW,
            settings.MINIO_BUCKET_PROCESSED,
            settings.MINIO_BUCKET_EVIDENCE,
        ]
    )
    await put_object(
        bucket=settings.MINIO_BUCKET_RAW,
        key=path,
        body=compressed,
        content_type="application/gzip",
    )
    return StoredRawPayload(path=path, byte_count=len(compressed), content_hash=content_hash)


async def preflight_raw_storage() -> dict:
    """Verify the active raw-storage contract without retaining test data."""
    if settings.STORAGE_BACKEND != "minio":
        raise RuntimeError("No raw storage preflight is implemented for the configured backend")
    if not (
        settings.MINIO_ENDPOINT_URL
        and settings.MINIO_ACCESS_KEY_ID
        and settings.MINIO_SECRET_ACCESS_KEY
    ):
        raise RuntimeError("MinIO raw storage credentials are not configured")

    key = f"_healthcheck/{uuid4().hex}.txt"
    payload = b"gennomx-ai-storage-preflight"
    await ensure_buckets_exist([settings.MINIO_BUCKET_RAW])
    try:
        await put_object(
            bucket=settings.MINIO_BUCKET_RAW,
            key=key,
            body=payload,
            content_type="text/plain",
        )
        retrieved = await get_object(bucket=settings.MINIO_BUCKET_RAW, key=key)
        if retrieved != payload:
            raise RuntimeError("Raw storage preflight read-back did not match written content")
    finally:
        await delete_object(bucket=settings.MINIO_BUCKET_RAW, key=key)

    return {
        "provider": settings.STORAGE_BACKEND,
        "bucket": settings.MINIO_BUCKET_RAW,
        "status": "ok",
    }
