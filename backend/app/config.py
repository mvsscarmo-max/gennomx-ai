from functools import lru_cache
from typing import Literal
from urllib.parse import urlsplit

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Environment ──────────────────────────────────────────────────────────
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_PROVIDER: Literal["vps_postgres"] = "vps_postgres"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/gennomx"
    WORKER_DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/gennomx"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/gennomx"
    AUTH_ADMIN_EMAIL: str = ""
    AUTH_ADMIN_PASSWORD: str = ""
    AUTH_ADMIN_PASSWORD_HASH: str = ""
    AUTH_JWT_SECRET: str = ""
    AUTH_JWT_ALGORITHM: str = "HS256"
    AUTH_JWT_ISSUER: str = "gennomx-ai"
    AUTH_JWT_AUDIENCE: str = "gennomx-dashboard"
    AUTH_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    AUTH_COOKIE_NAME: str = "gennomx_access_token"
    # Preparado para P-4. Este verifier e independente do JWT local AUTH_JWT_*.
    PLATFORM_AUTH_ENABLED: bool = False
    PLATFORM_AUTH_ISSUER: str = "gennomx-platform"
    PLATFORM_AUTH_AUDIENCE: str = "gennomx-admin"
    PLATFORM_AUTH_TENANT_ID: str = "gennomx-internal"
    PLATFORM_AUTH_PUBLIC_KEY: str = ""
    PLATFORM_AUTH_COOKIE_NAME: str = "gennomx_platform_admin"

    # ── Redis / Celery ────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # ── Storage ───────────────────────────────────────────────────────────────
    STORAGE_BACKEND: Literal["minio"] = "minio"
    MINIO_ENDPOINT_URL: str = "http://minio:9000"
    MINIO_ACCESS_KEY_ID: str = ""
    MINIO_SECRET_ACCESS_KEY: str = ""
    MINIO_REGION: str = "us-east-1"
    MINIO_BUCKET_RAW: str = "gennomx-ai-raw"
    MINIO_BUCKET_PROCESSED: str = "gennomx-ai-processed"
    MINIO_BUCKET_EVIDENCE: str = "gennomx-ai-evidence"
    MINIO_SECURE: bool = False

    # ── API Auth ──────────────────────────────────────────────────────────────
    API_SECRET_KEY: str = ""
    API_ALGORITHM: str = "HS256"
    API_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    API_INTERNAL_KEY: str = ""
    ROOT_PATH: str = ""
    # ── MCP ───────────────────────────────────────────────────────────────────
    MCP_TOKEN_CHATGPT: str = ""
    MCP_TOKEN_CLAUDE: str = ""
    MCP_TOKEN_PRIVATE_AGENT: str = ""
    MCP_RATE_LIMIT_PER_MINUTE: int = 60
    MCP_MAX_RESULTS_PER_TOOL: int = 100
    MCP_MAX_REQUEST_BYTES: int = 65536
    MCP_SCOPES_CHATGPT: str = (
        "search_drugs,find_trials,compare_assets,get_company_pipeline,get_trial_results,"
        "search_publications,get_regulatory_status,build_report_data_bundle,"
        "fetch_source_evidence"
    )
    MCP_SCOPES_CLAUDE: str = MCP_SCOPES_CHATGPT
    MCP_SCOPES_PRIVATE_AGENT: str = MCP_SCOPES_CHATGPT

    # ── LLM / OPENCODE (motor interno de IA auxiliar) ────────────────────────
    LLM_PROVIDER: Literal["opencode"] = "opencode"
    LLM_MODEL_PREMIUM: str = "deepseek-v4-pro"
    LLM_MODEL_ECONOMY: str = "deepseek-v4-pro"
    LLM_MAX_TOKENS: int = 4096
    LLM_TIMEOUT_SECONDS: int = 60
    LLM_TEMPERATURE: float = 0.0
    LLM_ENABLE_NETWORK_CALLS: bool = False
    OPENCODE_API_KEY: str = ""
    OPENCODE_BASE_URL: str = ""
    OPENCODE_MODEL_DEEPSEEK_V4_PRO: str = "deepseek-v4-pro"

    @property
    def llm_network_enabled(self) -> bool:
        return self.LLM_ENABLE_NETWORK_CALLS and self.ENVIRONMENT != "development"

    @property
    def root_path(self) -> str:
        return self.ROOT_PATH

    # ── Legacy LiteLLM (deprecated; kept for reference only) ─────────────────
    LITELLM_MODEL_PREMIUM: str = ""
    LITELLM_MODEL_ECONOMY: str = ""
    LITELLM_MAX_TOKENS: int = 4096
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # ── Connectors ────────────────────────────────────────────────────────────
    CLINICALTRIALS_API_BASE_URL: str = "https://clinicaltrials.gov/api/v2"
    CLINICALTRIALS_RATE_LIMIT_REQUESTS_PER_SECOND: float = 5.0
    CLINICALTRIALS_MAX_RETRIES: int = 3
    CLINICALTRIALS_INCREMENTAL_LOOKBACK_DAYS: int = 2
    CLINICALTRIALS_MAX_RECORDS_PER_RUN: int = 5000

    NCBI_API_KEY: str = ""
    NCBI_EMAIL: str = ""
    PUBMED_RATE_LIMIT_REQUESTS_PER_SECOND: float = 10.0
    PUBMED_API_BASE_URL: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    PUBMED_MAX_RETRIES: int = 3
    PUBMED_INCREMENTAL_LOOKBACK_DAYS: int = 2
    PUBMED_MAX_RECORDS_PER_RUN: int = 5000
    PUBMED_DEFAULT_QUERY: str = "clinical trial[pt]"
    PUBMED_INGEST_HOUR_UTC: int = 3

    OPENFDA_API_BASE_URL: str = "https://api.fda.gov"
    OPENFDA_API_KEY: str = ""
    OPENFDA_RATE_LIMIT_REQUESTS_PER_SECOND: float = 5.0
    OPENFDA_MAX_RETRIES: int = 3
    OPENFDA_MAX_RECORDS_PER_RUN: int = 2000
    OPENFDA_INGEST_HOUR_UTC: int = 3

    DAILYMED_API_BASE_URL: str = "https://dailymed.nlm.nih.gov/dailymed"
    DAILYMED_RATE_LIMIT_REQUESTS_PER_SECOND: float = 5.0
    DAILYMED_MAX_RETRIES: int = 3
    DAILYMED_MAX_RECORDS_PER_RUN: int = 2000
    DAILYMED_INGEST_HOUR_UTC: int = 3

    EMA_API_BASE_URL: str = "https://www.ema.europa.eu"
    EMA_MEDICINES_EXPORT_URL: str = (
        "https://www.ema.europa.eu/en/documents/report/medicines-output-medicines-report_en.xlsx"
    )
    EMA_MAX_RETRIES: int = 3
    EMA_MAX_RECORDS_PER_RUN: int = 2000
    EMA_INGEST_HOUR_UTC: int = 4

    OPEN_TARGETS_GRAPHQL_URL: str = "https://api.platform.opentargets.org/api/v4/graphql"
    OPEN_TARGETS_RATE_LIMIT_REQUESTS_PER_SECOND: float = 5.0
    OPEN_TARGETS_MAX_RETRIES: int = 3
    OPEN_TARGETS_MAX_RECORDS_PER_RUN: int = 500
    OPEN_TARGETS_INGEST_HOUR_UTC: int = 4
    OPEN_TARGETS_SEED_DISEASE_TERMS: str = (
        "non-small cell lung cancer,breast cancer,multiple myeloma,rheumatoid arthritis,"
        "type 2 diabetes,Alzheimer disease,melanoma,acute myeloid leukemia"
    )
    INGEST_ADMIN_MAX_RECORDS: int = 500

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: Literal["json", "text"] = "text"

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:3000"
    CORS_ALLOW_CREDENTIALS: bool = True
    API_ALLOWED_HOSTS: str = "admin.gennomx.com,mcp.gennomx.com"

    @field_validator("CORS_ORIGINS", "API_ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_csv_setting(cls, v: str) -> str:
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def api_allowed_hosts_list(self) -> list[str]:
        return [host.strip() for host in self.API_ALLOWED_HOSTS.split(",") if host.strip()]

    @model_validator(mode="after")
    def validate_secure_production_settings(self) -> "Settings":
        if not self.is_production:
            return self
        required = {
            "DATABASE_URL": self.DATABASE_URL,
            "DATABASE_URL_SYNC": self.DATABASE_URL_SYNC,
            "WORKER_DATABASE_URL": self.WORKER_DATABASE_URL,
            "REDIS_URL": self.REDIS_URL,
            "CELERY_BROKER_URL": self.CELERY_BROKER_URL,
            "CELERY_RESULT_BACKEND": self.CELERY_RESULT_BACKEND,
            "AUTH_ADMIN_EMAIL": self.AUTH_ADMIN_EMAIL,
            "AUTH_JWT_SECRET": self.AUTH_JWT_SECRET,
            "MINIO_ENDPOINT_URL": self.MINIO_ENDPOINT_URL,
            "MINIO_ACCESS_KEY_ID": self.MINIO_ACCESS_KEY_ID,
            "MINIO_SECRET_ACCESS_KEY": self.MINIO_SECRET_ACCESS_KEY,
            "API_INTERNAL_KEY": self.API_INTERNAL_KEY,
            "ROOT_PATH": self.ROOT_PATH,
            "MCP_TOKEN_CHATGPT": self.MCP_TOKEN_CHATGPT,
        }
        missing = [name for name, value in required.items() if not value]
        if not (self.AUTH_ADMIN_PASSWORD or self.AUTH_ADMIN_PASSWORD_HASH):
            missing.append("AUTH_ADMIN_PASSWORD_OR_HASH")
        insecure = [
            name
            for name, value in required.items()
            if value
            and any(marker in value.lower() for marker in ("change-this", "postgres:postgres"))
        ]
        if self.AUTH_ADMIN_PASSWORD and len(self.AUTH_ADMIN_PASSWORD) < 12:
            insecure.append("AUTH_ADMIN_PASSWORD")
        if missing or insecure:
            problems = [
                *(f"missing:{name}" for name in missing),
                *(f"insecure:{name}" for name in insecure),
            ]
            raise ValueError(f"Unsafe production configuration: {', '.join(problems)}")
        if "localhost" in self.CORS_ORIGINS or "*" in self.cors_origins_list:
            raise ValueError("Production CORS_ORIGINS must contain explicit non-local origins")
        if not self.api_allowed_hosts_list:
            raise ValueError("Production API_ALLOWED_HOSTS must contain at least one host")
        if any(host == "*" or "localhost" in host for host in self.api_allowed_hosts_list):
            raise ValueError("Production API_ALLOWED_HOSTS must contain explicit non-local hosts")
        if self.ROOT_PATH != "/api/ai":
            raise ValueError("Production ROOT_PATH must be /api/ai")
        infrastructure_urls = (
            self.DATABASE_URL,
            self.DATABASE_URL_SYNC,
            self.WORKER_DATABASE_URL,
            self.REDIS_URL,
            self.CELERY_BROKER_URL,
            self.CELERY_RESULT_BACKEND,
        )
        if any("localhost" in url for url in infrastructure_urls):
            raise ValueError("Production database, Redis and Celery URLs must not target localhost")
        for name, url in (
            ("DATABASE_URL", self.DATABASE_URL),
            ("DATABASE_URL_SYNC", self.DATABASE_URL_SYNC),
            ("WORKER_DATABASE_URL", self.WORKER_DATABASE_URL),
        ):
            if "ssl=require" not in url and "sslmode=require" not in url:
                raise ValueError(f"Production {name} must require TLS")
        expected_roles = {
            "DATABASE_URL": "gennomx_app",
            "WORKER_DATABASE_URL": "gennomx_worker",
            "DATABASE_URL_SYNC": "gennomx_migrator",
        }
        for name, expected_role in expected_roles.items():
            username = (urlsplit(getattr(self, name)).username or "").split(".", 1)[0]
            if username != expected_role:
                raise ValueError(f"Production {name} must use database role {expected_role}")
        database_urls = (
            self.DATABASE_URL,
            self.WORKER_DATABASE_URL,
            self.DATABASE_URL_SYNC,
        )
        if self.DATABASE_PROVIDER == "vps_postgres" and any(
            "supabase.co" in url or "pooler.supabase.com" in url for url in database_urls
        ):
            raise ValueError(
                "DATABASE_PROVIDER=vps_postgres requires DATABASE_URL, "
                "WORKER_DATABASE_URL and DATABASE_URL_SYNC to target the VPS PostgreSQL"
            )
        for name, url in (
            ("REDIS_URL", self.REDIS_URL),
            ("CELERY_BROKER_URL", self.CELERY_BROKER_URL),
            ("CELERY_RESULT_BACKEND", self.CELERY_RESULT_BACKEND),
        ):
            if not url.startswith("rediss://"):
                raise ValueError(f"Production {name} must use TLS (rediss://)")
        if not self.MINIO_ENDPOINT_URL.startswith(("http://", "https://")):
            raise ValueError("Production MINIO_ENDPOINT_URL must be a valid URL")
        if self.AUTH_JWT_ALGORITHM.upper() != "HS256":
            raise ValueError("Production AUTH_JWT_ALGORITHM must be HS256")
        if self.PLATFORM_AUTH_ENABLED:
            if not self.PLATFORM_AUTH_PUBLIC_KEY:
                raise ValueError("Platform Auth enabled but PLATFORM_AUTH_PUBLIC_KEY is missing")
            if (
                self.PLATFORM_AUTH_ISSUER != "gennomx-platform"
                or self.PLATFORM_AUTH_AUDIENCE != "gennomx-admin"
                or self.PLATFORM_AUTH_TENANT_ID != "gennomx-internal"
            ):
                raise ValueError("Platform Auth claims must match the platform contract")
        if self.LLM_ENABLE_NETWORK_CALLS:
            if not self.OPENCODE_API_KEY:
                raise ValueError("LLM network calls enabled but OPENCODE_API_KEY is missing")
            if not self.OPENCODE_BASE_URL:
                raise ValueError("LLM network calls enabled but OPENCODE_BASE_URL is missing")
            if not self.LLM_MODEL_PREMIUM:
                raise ValueError("LLM network calls enabled but LLM_MODEL_PREMIUM is missing")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
