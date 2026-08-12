"""Minimal S3-compatible client for MinIO uploads without external SDKs."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from urllib.parse import quote, urlparse

import httpx

from app.config import get_settings

settings = get_settings()


@dataclass(frozen=True)
class MinioObjectRef:
    bucket: str
    key: str


_bucket_lock = asyncio.Lock()
_ensured_buckets: set[str] = set()


def _hash_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sign(key: bytes, message: str) -> bytes:
    return hmac.new(key, message.encode("utf-8"), hashlib.sha256).digest()


@lru_cache(maxsize=32)
def _signing_key(secret_key: str, date_stamp: str, region: str, service: str = "s3") -> bytes:
    k_date = _sign(f"AWS4{secret_key}".encode(), date_stamp)
    k_region = hmac.new(k_date, region.encode("utf-8"), hashlib.sha256).digest()
    k_service = hmac.new(k_region, service.encode("utf-8"), hashlib.sha256).digest()
    return hmac.new(k_service, b"aws4_request", hashlib.sha256).digest()


def _canonical_uri(path: str) -> str:
    normalized = path if path.startswith("/") else f"/{path}"
    return quote(normalized, safe="/-_.~")


def _canonical_headers(headers: dict[str, str]) -> tuple[str, str]:
    canonical_pairs = [f"{key.lower()}:{value.strip()}\n" for key, value in sorted(headers.items())]
    signed_headers = ";".join(key.lower() for key in sorted(headers))
    return "".join(canonical_pairs), signed_headers


async def _signed_request(
    method: str,
    path: str,
    *,
    body: bytes = b"",
    content_type: str | None = None,
) -> httpx.Response:
    parsed = urlparse(settings.MINIO_ENDPOINT_URL.rstrip("/"))
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("MINIO_ENDPOINT_URL must be an absolute URL")

    now = datetime.now(UTC)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")
    payload_hash = _hash_sha256(body)

    headers = {
        "host": parsed.netloc,
        "x-amz-content-sha256": payload_hash,
        "x-amz-date": amz_date,
    }
    if content_type:
        headers["content-type"] = content_type

    canonical_headers, signed_headers = _canonical_headers(headers)
    canonical_request = "\n".join(
        [
            method.upper(),
            _canonical_uri(path),
            "",
            canonical_headers,
            signed_headers,
            payload_hash,
        ]
    )
    credential_scope = f"{date_stamp}/{settings.MINIO_REGION}/s3/aws4_request"
    string_to_sign = "\n".join(
        [
            "AWS4-HMAC-SHA256",
            amz_date,
            credential_scope,
            hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
        ]
    )
    signing_key = _signing_key(settings.MINIO_SECRET_ACCESS_KEY, date_stamp, settings.MINIO_REGION)
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    headers["Authorization"] = (
        "AWS4-HMAC-SHA256 "
        f"Credential={settings.MINIO_ACCESS_KEY_ID}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    async with httpx.AsyncClient(
        base_url=f"{parsed.scheme}://{parsed.netloc}",
        timeout=30.0,
        verify=settings.MINIO_SECURE,
    ) as client:
        return await client.request(
            method.upper(), _canonical_uri(path), content=body, headers=headers
        )


async def ensure_bucket(bucket: str) -> None:
    if bucket in _ensured_buckets:
        return
    async with _bucket_lock:
        if bucket in _ensured_buckets:
            return
        response = await _signed_request("PUT", f"/{bucket}")
        if response.status_code not in {200, 204, 409}:
            response.raise_for_status()
        _ensured_buckets.add(bucket)


async def ensure_buckets_exist(buckets: list[str]) -> None:
    for bucket in buckets:
        await ensure_bucket(bucket)


async def put_object(*, bucket: str, key: str, body: bytes, content_type: str) -> MinioObjectRef:
    await ensure_bucket(bucket)
    response = await _signed_request(
        "PUT",
        f"/{bucket}/{key}",
        body=body,
        content_type=content_type,
    )
    if response.status_code not in {200, 201, 204}:
        response.raise_for_status()
    return MinioObjectRef(bucket=bucket, key=key)


async def get_object(*, bucket: str, key: str) -> bytes:
    response = await _signed_request("GET", f"/{bucket}/{key}")
    response.raise_for_status()
    return response.content


async def delete_object(*, bucket: str, key: str) -> None:
    response = await _signed_request("DELETE", f"/{bucket}/{key}")
    if response.status_code not in {200, 202, 204, 404}:
        response.raise_for_status()
