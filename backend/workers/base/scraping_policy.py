"""Fail-closed web collection controls for future approved scrapers."""

import asyncio
import hashlib
import ipaddress
import socket
from contextlib import asynccontextmanager
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse, urlunparse

import httpx
from redis.asyncio import Redis
from sqlalchemy import text

from app.config import get_settings

settings = get_settings()


@dataclass(frozen=True)
class ScrapeResult:
    final_url: str
    status_code: int
    content: bytes
    content_type: str


def sanitize_html(raw_html: bytes) -> bytes:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(raw_html, "lxml")
    for tag in soup(["script", "iframe", "object", "embed", "style"]):
        tag.decompose()
    for tag in soup.find_all(True):
        for attribute in list(tag.attrs):
            value = tag.attrs.get(attribute)
            unsafe_event = attribute.casefold().startswith("on")
            unsafe_url = attribute.casefold() in {"href", "src", "action"} and str(
                value
            ).strip().lower().startswith(("javascript:", "data:text/html"))
            if unsafe_event or unsafe_url:
                del tag.attrs[attribute]
    return str(soup).encode("utf-8")


async def _public_addresses(hostname: str) -> list[str]:
    try:
        literal = ipaddress.ip_address(hostname)
        addresses = [literal]
    except ValueError:
        infos = await asyncio.to_thread(socket.getaddrinfo, hostname, 443, type=socket.SOCK_STREAM)
        addresses = list({ipaddress.ip_address(info[4][0]) for info in infos})
    if not addresses or any(not address.is_global for address in addresses):
        raise ValueError("scraper_ssrf_destination_blocked")
    return [str(address) for address in addresses]


async def validate_scrape_url(url: str, policy: dict) -> list[str]:
    """Validate the destination and return its resolved public IP addresses.

    Callers must connect to one of the returned addresses (with the original
    hostname pinned via the Host header / TLS SNI) instead of letting the
    HTTP client re-resolve the hostname — otherwise a short-TTL DNS answer
    could rebind to an internal address between validation and connection.
    """
    parsed = urlparse(url)
    scheme = parsed.scheme.casefold()
    host = (parsed.hostname or "").casefold().rstrip(".")
    allowed_schemes = set(policy["allowed_schemes"] or ["https"])
    allowed_hosts = {str(item).casefold().rstrip(".") for item in policy["allowed_hosts"] or []}
    allowed_hosts.add(str(policy["domain"]).casefold().rstrip("."))
    if (
        parsed.username
        or parsed.password
        or scheme not in allowed_schemes
        or host not in allowed_hosts
    ):
        raise ValueError("scraper_destination_not_allowlisted")
    if parsed.port not in (None, 443 if scheme == "https" else 80):
        raise ValueError("scraper_nonstandard_port_blocked")
    return await _public_addresses(host)


def _pin_request_to_address(url: str, address: str):
    """Rewrite `url` to target a validated IP while preserving the original
    hostname for the Host header and TLS SNI, so DNS is not consulted again
    between validation and connection (SSRF/DNS-rebinding mitigation)."""
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    port = parsed.port or (443 if parsed.scheme.casefold() == "https" else 80)
    netloc = f"[{address}]:{port}" if ":" in address else f"{address}:{port}"
    pinned_url = urlunparse(parsed._replace(netloc=netloc))
    return pinned_url, hostname


async def _read_limited(response: httpx.Response, max_bytes: int) -> bytes:
    content = bytearray()
    try:
        async for chunk in response.aiter_bytes():
            content.extend(chunk)
            if len(content) > max_bytes:
                raise ValueError("scraper_response_too_large")
        return bytes(content)
    finally:
        await response.aclose()


class ControlledScraper:
    def __init__(self, db) -> None:
        self.db = db

    async def _policy(self, domain: str) -> dict:
        policy = (
            (
                await self.db.execute(
                    text("""
                    SELECT id::text, domain, robots_policy, requests_per_minute,
                           max_concurrency, allowed_schemes, allowed_hosts,
                           kill_switch, active, consecutive_auth_failures
                    FROM scraper_domain_policies
                    WHERE domain = :domain
                """),
                    {"domain": domain.casefold().rstrip(".")},
                )
            )
            .mappings()
            .first()
        )
        if not policy or not policy["active"] or policy["kill_switch"]:
            raise PermissionError("scraper_domain_disabled")
        if policy["robots_policy"] not in {"allowed", "not_applicable"}:
            raise PermissionError("scraper_robots_policy_not_approved")
        return dict(policy)

    async def _distributed_rate_limit(self, policy: dict) -> None:
        redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        key = f"scraper:rate:{policy['id']}"
        try:
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, 60)
            if count > policy["requests_per_minute"]:
                raise RuntimeError("scraper_rate_limit_reached")
        finally:
            await redis.aclose()

    @asynccontextmanager
    async def _concurrency_slot(self, policy: dict):
        redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        key = f"scraper:concurrency:{policy['id']}"
        acquired = False
        try:
            count = await redis.incr(key)
            await redis.expire(key, 120)
            if count > policy["max_concurrency"]:
                await redis.decr(key)
                raise RuntimeError("scraper_concurrency_limit_reached")
            acquired = True
            yield
        finally:
            if acquired:
                await redis.decr(key)
            await redis.aclose()

    async def _event(self, policy_id: str, url: str, outcome: str, status: int | None) -> None:
        await self.db.execute(
            text("""
                INSERT INTO scraper_access_events (
                    id, domain_policy_id, url_hash, outcome, http_status, created_at
                ) VALUES (gen_random_uuid(), :policy_id, :url_hash, :outcome, :status, now())
            """),
            {
                "policy_id": policy_id,
                "url_hash": hashlib.sha256(url.encode()).hexdigest(),
                "outcome": outcome,
                "status": status,
            },
        )

    async def fetch(self, url: str, *, max_bytes: int = 10_000_000) -> ScrapeResult:
        initial = urlparse(url)
        policy = await self._policy((initial.hostname or "").casefold())
        current = url
        await self._distributed_rate_limit(policy)
        async with (
            self._concurrency_slot(policy),
            httpx.AsyncClient(
                timeout=httpx.Timeout(30),
                follow_redirects=False,
                headers={"User-Agent": "GennomXBot/1.0"},
            ) as client,
        ):
            for _redirect in range(6):
                addresses = await validate_scrape_url(current, policy)
                pinned_url, hostname = _pin_request_to_address(current, addresses[0])
                request = client.build_request(
                    "GET",
                    pinned_url,
                    headers={"Host": hostname},
                    extensions={"sni_hostname": hostname},
                )
                response = await client.send(request, stream=True)
                if response.status_code == 429:
                    retry_after = response.headers.get("retry-after", "1")
                    try:
                        delay = min(60, max(1, int(retry_after)))
                    except ValueError:
                        delay = 1
                    await asyncio.sleep(delay)
                if response.status_code in {301, 302, 303, 307, 308}:
                    location = response.headers.get("location")
                    await response.aclose()
                    if not location:
                        raise RuntimeError("scraper_redirect_without_location")
                    current = urljoin(current, location)
                    continue
                if response.status_code in {401, 403, 429}:
                    await response.aclose()
                    await self.db.execute(
                        text("""
                                UPDATE scraper_domain_policies
                                SET consecutive_auth_failures = consecutive_auth_failures + 1,
                                    kill_switch = CASE
                                      WHEN consecutive_auth_failures + 1 >= 3
                                      THEN true ELSE kill_switch END,
                                    updated_at = now()
                                WHERE id = :id
                            """),
                        {"id": policy["id"]},
                    )
                    await self._event(
                        policy["id"], current, "paused_by_source", response.status_code
                    )
                    raise PermissionError("scraper_source_refused_request")
                try:
                    response.raise_for_status()
                except Exception:
                    await response.aclose()
                    raise
                content = await _read_limited(response, max_bytes)
                content_type = response.headers.get("content-type", "application/octet-stream")
                if "html" in content_type.casefold():
                    content = sanitize_html(content)
                await self.db.execute(
                    text("""
                            UPDATE scraper_domain_policies
                            SET consecutive_auth_failures = 0, updated_at = now()
                            WHERE id = :id
                        """),
                    {"id": policy["id"]},
                )
                await self._event(policy["id"], current, "success", response.status_code)
                return ScrapeResult(current, response.status_code, content, content_type)
        await self._event(policy["id"], current, "redirect_limit", None)
        raise RuntimeError("scraper_redirect_limit_exceeded")
