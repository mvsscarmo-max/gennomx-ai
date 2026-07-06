from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import text

from app.config import get_settings
from app.core.exceptions import GennomXError
from app.core.logging import configure_logging
from app.database import AsyncSessionLocal
from app.database_security import assert_database_role
from app.middleware.logging import RequestLoggingMiddleware

settings = get_settings()
configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("gennomx_api_starting", environment=settings.ENVIRONMENT)
    if settings.is_production:
        async with AsyncSessionLocal() as session:
            await assert_database_role(session, "gennomx_app")
    yield
    logger.info("gennomx_api_stopping")


app = FastAPI(
    title="GennomX AI — API",
    description=(
        "Infraestrutura proprietária de dados biomédicos e competitivos. "
        "Acesso via MCP para modelos host externos."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(RequestLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-MCP-Token"],
)

if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.api_allowed_hosts_list,
    )

# ── Error handling ───────────────────────────────────────────────────────────────
_GENNOMX_ERROR_STATUS = {
    "NOT_FOUND": status.HTTP_404_NOT_FOUND,
    "VALIDATION_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
    "AUTHENTICATION_ERROR": status.HTTP_401_UNAUTHORIZED,
    "AUTHORIZATION_ERROR": status.HTTP_403_FORBIDDEN,
    "INGESTION_ERROR": status.HTTP_502_BAD_GATEWAY,
    "MCP_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
}


@app.exception_handler(GennomXError)
async def gennomx_error_handler(request: Request, exc: GennomXError) -> JSONResponse:
    """Translate domain errors raised by services (NotFoundError, ValidationError,
    AuthorizationError, ...) into structured HTTP responses instead of an
    unhandled-exception 500."""
    status_code = _GENNOMX_ERROR_STATUS.get(exc.code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "error": {"code": exc.code, "message": exc.message}},
    )


# ── Routers ───────────────────────────────────────────────────────────────────
from app.api.v1.router import api_router  # noqa: E402
from app.mcp.server import mcp_router  # noqa: E402

app.include_router(api_router, prefix="/api/v1")
app.include_router(mcp_router, prefix="/api")


# ── Health ─────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["system"])
async def health_check() -> dict:
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": "0.1.0",
    }


@app.get("/ready", tags=["system"])
async def readiness_check(response: Response) -> dict:
    checks = {
        "database": await _check_database(),
        "redis": await _check_redis(),
    }
    ready = all(value == "ok" for value in checks.values())
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    body: dict = {"status": "ready" if ready else "not_ready"}
    if not settings.is_production:
        # Component-level detail helps local/staging debugging but is not
        # exposed externally in production to avoid revealing infra topology.
        body["checks"] = checks
    return body


async def _check_database() -> str:
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "unavailable"


async def _check_redis() -> str:
    client = Redis.from_url(
        settings.REDIS_URL, socket_connect_timeout=2, socket_timeout=2, decode_responses=True
    )
    try:
        return "ok" if await client.ping() else "unavailable"
    except Exception:
        return "unavailable"
    finally:
        await client.aclose()
