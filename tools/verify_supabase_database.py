"""Verify Supabase migration state and least-privilege roles."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import psycopg2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ENV = PROJECT_ROOT / "backend" / ".env"


def read_env() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in BACKEND_ENV.read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def sync_url(url: str) -> str:
    parts = urlsplit(url)
    scheme = "postgresql" if parts.scheme == "postgresql+asyncpg" else parts.scheme
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    if "ssl" in query and "sslmode" not in query:
        query["sslmode"] = query.pop("ssl")
    return urlunsplit((scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def verify_connection(label: str, url: str) -> None:
    with psycopg2.connect(sync_url(url), connect_timeout=15) as conn, conn.cursor() as cursor:
        cursor.execute(
            """
                SELECT current_user, rolsuper, rolbypassrls
                FROM pg_roles WHERE rolname = current_user
                """
        )
        user, is_superuser, bypasses_rls = cursor.fetchone()
        cursor.execute("SELECT version_num FROM alembic_version")
        version = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM data_sources")
        data_sources = cursor.fetchone()[0]
    print(
        f"{label}: user={user}, superuser={is_superuser}, "
        f"bypassrls={bypasses_rls}, alembic={version}, data_sources={data_sources}"
    )


def main() -> None:
    env = read_env()
    verify_connection("app", env["DATABASE_URL"])
    verify_connection("worker", env["WORKER_DATABASE_URL"])
    verify_connection("migrator", env["DATABASE_URL_SYNC"])


if __name__ == "__main__":
    main()
