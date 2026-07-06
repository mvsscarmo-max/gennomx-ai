"""GennomX MCP Server — read-only, authenticated, rate-limited."""

from __future__ import annotations

import hashlib
import json
import secrets
import time
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.mcp import tools

logger = structlog.get_logger(__name__)
settings = get_settings()

mcp_router = APIRouter(prefix="/mcp", tags=["mcp"])

# Simple in-memory rate limiter: {token: [(timestamp, count)]}
_rate_buckets: dict[str, list[float]] = defaultdict(list)

# Pre-auth limiter keyed by client IP, deliberately stricter than the
# per-token limit since it must absorb unauthenticated traffic before any
# token/role is known.
_ip_rate_buckets: dict[str, list[float]] = defaultdict(list)
_IP_PRE_AUTH_LIMIT = 30
_IP_PRE_AUTH_WINDOW = 60.0
_IP_BUCKET_SWEEP_INTERVAL = 300.0
_last_ip_bucket_sweep = 0.0


def _sweep_stale_ip_buckets(now: float) -> None:
    """Drop fully-expired IP buckets so one-shot/spoofed source IPs don't
    accumulate in memory forever (each only ever filtered when *that* IP
    makes a follow-up request)."""
    global _last_ip_bucket_sweep
    if now - _last_ip_bucket_sweep < _IP_BUCKET_SWEEP_INTERVAL:
        return
    _last_ip_bucket_sweep = now
    stale = [
        ip
        for ip, timestamps in _ip_rate_buckets.items()
        if not any(now - t < _IP_PRE_AUTH_WINDOW for t in timestamps)
    ]
    for ip in stale:
        del _ip_rate_buckets[ip]


def _check_rate_limit(token: str) -> None:
    current_settings = get_settings()
    now = time.time()
    window = 60.0
    limit = current_settings.MCP_RATE_LIMIT_PER_MINUTE

    bucket = _rate_buckets[token]
    # Remove timestamps outside the window
    fresh = [t for t in bucket if now - t < window]
    if fresh:
        _rate_buckets[token] = fresh
    else:
        del _rate_buckets[token]

    if len(_rate_buckets.get(token, [])) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "RATE_LIMITED", "message": f"Rate limit: {limit} calls/minute"},
        )
    _rate_buckets[token].append(now)


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _check_ip_rate_limit_memory(ip: str) -> None:
    now = time.time()
    _sweep_stale_ip_buckets(now)
    bucket = _ip_rate_buckets[ip]
    fresh = [t for t in bucket if now - t < _IP_PRE_AUTH_WINDOW]
    if fresh:
        _ip_rate_buckets[ip] = fresh
    else:
        del _ip_rate_buckets[ip]

    if len(_ip_rate_buckets.get(ip, [])) >= _IP_PRE_AUTH_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "RATE_LIMITED", "message": "Too many requests from this client"},
        )
    _ip_rate_buckets[ip].append(now)


async def _check_pre_auth_rate_limit(request: Request) -> None:
    """Throttle by client IP before any token is parsed or validated.

    This must run ahead of authentication so unauthenticated/invalid-token
    traffic — the cheapest attack path — cannot bypass rate limiting and
    flood the audit log / connection pool.
    """
    ip = _client_ip(request)
    current_settings = get_settings()
    if current_settings.is_development:
        _check_ip_rate_limit_memory(ip)
        return

    from redis.asyncio import Redis

    key = f"gennomx:mcp:preauth:{ip}:{int(time.time() // 60)}"
    redis = Redis.from_url(current_settings.REDIS_URL, decode_responses=True)
    try:
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, 120)
        if count > _IP_PRE_AUTH_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"code": "RATE_LIMITED", "message": "Too many requests from this client"},
            )
    finally:
        await redis.aclose()


def _authenticate_mcp(x_mcp_token: str | None) -> str:
    current_settings = get_settings()
    if not x_mcp_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "MCP_AUTH_REQUIRED", "message": "X-MCP-Token header required"},
        )
    configured_tokens = (
        (current_settings.MCP_TOKEN_CHATGPT, "chatgpt"),
        (current_settings.MCP_TOKEN_CLAUDE, "claude"),
        (current_settings.MCP_TOKEN_PRIVATE_AGENT, "private_agent"),
    )
    client = next(
        (
            name
            for token, name in configured_tokens
            if token and secrets.compare_digest(token, x_mcp_token)
        ),
        None,
    )
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_MCP_TOKEN", "message": "Invalid MCP token"},
        )
    return client


def _authorize_tool(client: str, tool_name: str) -> None:
    current_settings = get_settings()
    configured = {
        "chatgpt": current_settings.MCP_SCOPES_CHATGPT,
        "claude": current_settings.MCP_SCOPES_CLAUDE,
        "private_agent": current_settings.MCP_SCOPES_PRIVATE_AGENT,
    }
    scopes = {scope.strip() for scope in configured.get(client, "").split(",") if scope.strip()}
    if tool_name not in scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "TOOL_SCOPE_DENIED",
                "message": "Client is not authorized for this tool",
            },
        )


async def _check_distributed_rate_limit(token: str) -> None:
    current_settings = get_settings()
    if current_settings.is_development:
        _check_rate_limit(token)
        return
    from redis.asyncio import Redis

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    key = f"gennomx:mcp:rate:{token_hash}:{int(time.time() // 60)}"
    redis = Redis.from_url(current_settings.REDIS_URL, decode_responses=True)
    try:
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, 120)
        if count > current_settings.MCP_RATE_LIMIT_PER_MINUTE:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"code": "RATE_LIMITED", "message": "MCP rate limit exceeded"},
            )
    finally:
        await redis.aclose()


@mcp_router.post("/call")
async def mcp_call(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_mcp_token: str | None = Header(default=None, alias="X-MCP-Token"),
) -> dict:
    """
    Single MCP endpoint that dispatches to tool implementations.

    Request body:
      { "tool": "search_drugs", "arguments": { ... } }

    Returns structured data with sources, evidence, and metadata.
    """
    start_ts = time.perf_counter()
    client = "unknown"
    tool_name = "unknown"
    arguments: dict[str, Any] = {}
    input_hash = hashlib.sha256(b"unparsed").hexdigest()

    try:
        await _check_pre_auth_rate_limit(request)
        client = _authenticate_mcp(x_mcp_token)
        await _check_distributed_rate_limit(x_mcp_token or "")

        content_length = request.headers.get("content-length")
        try:
            declared_length = int(content_length) if content_length else 0
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_CONTENT_LENGTH", "message": "Invalid Content-Length"},
            ) from exc
        if declared_length > settings.MCP_MAX_REQUEST_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={"code": "REQUEST_TOO_LARGE", "message": "MCP request exceeds size limit"},
            )
        raw_body = await request.body()
        if len(raw_body) > settings.MCP_MAX_REQUEST_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={"code": "REQUEST_TOO_LARGE", "message": "MCP request exceeds size limit"},
            )
        try:
            body = json.loads(raw_body)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_JSON", "message": "Request body must be valid JSON"},
            ) from exc
        if not isinstance(body, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_BODY", "message": "request body must be an object"},
            )
        tool_name = body.get("tool", "") or "unknown"
        arguments = body.get("arguments", {})
        if not isinstance(arguments, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_ARGUMENTS", "message": "arguments must be an object"},
            )

        if tool_name == "unknown":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "MISSING_TOOL", "message": "tool field required"},
            )

        _authorize_tool(client, tool_name)

        # Blocklist: prevent direct data access tools from being called as tools
        blocked_tools = {"admin", "execute_sql", "delete", "update", "insert"}
        if tool_name.lower() in blocked_tools:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "TOOL_BLOCKED", "message": f"Tool '{tool_name}' is not available"},
            )

        input_hash = hashlib.sha256(
            json.dumps({"tool": tool_name, "arguments": arguments}, sort_keys=True).encode()
        ).hexdigest()

        log_entry = {
            "tool": tool_name,
            "client": client,
            "input_hash": input_hash,
            "ts": datetime.now(UTC).isoformat(),
        }

        result = await _dispatch_tool(tool_name, arguments, db)
        accessed_entities, accessed_types = _extract_accessed_entities(result.get("data"))
        latency_ms = round((time.perf_counter() - start_ts) * 1000, 2)
        result_count = result.get("count", 0)

        logger.info(
            "mcp_call_success", **log_entry, latency_ms=latency_ms, result_count=result_count
        )
        await _persist_mcp_log(
            db=db,
            tool_name=tool_name,
            client=client,
            input_hash=input_hash,
            arguments=arguments,
            result_count=result_count,
            latency_ms=latency_ms,
            status_value="success",
            source_entities_accessed=accessed_entities,
            entity_types_accessed=accessed_types,
        )
        await db.commit()

        return {
            "tool": tool_name,
            "status": "success",
            "data": result.get("data"),
            "count": result_count,
            "meta": {
                "latency_ms": latency_ms,
                "timestamp": log_entry["ts"],
                "source": "gennomx_ai",
                "limitations": result.get("limitations", []),
                "gaps": result.get("gaps", []),
            },
        }

    except HTTPException as e:
        latency_ms = round((time.perf_counter() - start_ts) * 1000, 2)
        if e.status_code == status.HTTP_401_UNAUTHORIZED:
            # Unauthenticated requests are the cheapest attack path — never
            # spend a DB write/commit on them, only a structured log line.
            logger.warning(
                "mcp_call_unauthenticated",
                client=client,
                latency_ms=latency_ms,
                error_message=str(e.detail),
            )
        else:
            await _persist_mcp_log(
                db=db,
                tool_name=tool_name,
                client=client,
                input_hash=input_hash,
                arguments=arguments,
                result_count=0,
                latency_ms=latency_ms,
                status_value="blocked" if e.status_code in (403, 404) else "error",
                error_type=str(e.status_code),
                error_message=str(e.detail),
            )
            await db.commit()
        raise
    except Exception as e:
        latency_ms = round((time.perf_counter() - start_ts) * 1000, 2)
        logger.error(
            "mcp_call_error",
            tool=tool_name,
            client=client,
            input_hash=input_hash,
            error=str(e),
            latency_ms=latency_ms,
        )
        await _persist_mcp_log(
            db=db,
            tool_name=tool_name,
            client=client,
            input_hash=input_hash,
            arguments=arguments,
            result_count=0,
            latency_ms=latency_ms,
            status_value="error",
            error_type=type(e).__name__,
            error_message=str(e),
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "TOOL_ERROR", "message": "Tool execution failed", "tool": tool_name},
        ) from e


async def _dispatch_tool(tool_name: str, arguments: dict, db: AsyncSession) -> dict:
    """Route tool_name to the appropriate implementation."""
    tool_map = {
        "search_drugs": tools.search_drugs,
        "find_trials": tools.find_trials,
        "get_trial_results": tools.get_trial_results,
        "get_company_pipeline": tools.get_company_pipeline,
        "get_regulatory_status": tools.get_regulatory_status,
        "fetch_source_evidence": tools.fetch_source_evidence,
        "build_report_data_bundle": tools.build_report_data_bundle,
        "compare_assets": tools.compare_assets,
        "search_publications": tools.search_publications,
    }

    handler = tool_map.get(tool_name)
    if not handler:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "UNKNOWN_TOOL",
                "message": f"Tool '{tool_name}' not found",
                "available_tools": list(tool_map.keys()),
            },
        )

    return await handler(arguments, db=db)


async def _persist_mcp_log(
    *,
    db: AsyncSession,
    tool_name: str,
    client: str,
    input_hash: str,
    arguments: dict,
    result_count: int,
    latency_ms: float,
    status_value: str,
    error_type: str | None = None,
    error_message: str | None = None,
    source_entities_accessed: list[dict[str, str]] | None = None,
    entity_types_accessed: list[str] | None = None,
) -> None:
    """Persist MCP audit log without exposing raw token values."""
    await db.execute(
        text("""
            INSERT INTO mcp_query_logs (
                timestamp, tool_name, requesting_client, input_hash,
                normalized_arguments, result_count, latency_ms, status,
                error_type, error_message, source_entities_accessed,
                entity_types_accessed, created_at, updated_at
            )
            VALUES (
                now(), :tool_name, :client, :input_hash,
                CAST(:arguments AS jsonb), :result_count, :latency_ms, :status,
                :error_type, :error_message, CAST(:source_entities AS jsonb),
                :entity_types, now(), now()
            )
        """),
        {
            "tool_name": tool_name,
            "client": client,
            "input_hash": input_hash,
            "arguments": json.dumps(arguments, sort_keys=True),
            "result_count": result_count,
            "latency_ms": latency_ms,
            "status": status_value,
            "error_type": error_type,
            "error_message": error_message,
            "source_entities": json.dumps(source_entities_accessed or []),
            "entity_types": entity_types_accessed or [],
        },
    )


def _extract_accessed_entities(data: Any) -> tuple[list[dict[str, str]], list[str]]:
    """Extract a bounded audit index without persisting complete tool responses."""
    entities: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def visit(value: Any, parent: str = "entity") -> None:
        if len(entities) >= 100:
            return
        if isinstance(value, dict):
            entity_id = value.get("id") or value.get("nct_id") or value.get("pmid")
            if entity_id is not None:
                key = (parent, str(entity_id))
                if key not in seen:
                    seen.add(key)
                    entities.append({"type": parent, "id": str(entity_id)[:200]})
            for key, child in value.items():
                visit(child, str(key).rstrip("s")[:100])
        elif isinstance(value, list):
            for child in value[:100]:
                visit(child, parent)

    visit(data)
    return entities, sorted({entity["type"] for entity in entities})
