"""Helpers for PostgreSQL/Supabase SQLAlchemy connection URLs."""

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def coerce_database_url(url: str, *, async_driver: bool) -> str:
    """Return a SQLAlchemy URL compatible with the selected PostgreSQL driver.

    Supabase examples commonly use psycopg-style URLs with ``sslmode=require``.
    The application runtime uses asyncpg, while Alembic uses psycopg2. Keeping
    this conversion in one place avoids environment-specific URL footguns.
    """
    if not url:
        return url

    parts = urlsplit(url)
    scheme = parts.scheme
    query = dict(parse_qsl(parts.query, keep_blank_values=True))

    if async_driver:
        if scheme == "postgresql":
            scheme = "postgresql+asyncpg"
        if "sslmode" in query and "ssl" not in query:
            query["ssl"] = query.pop("sslmode")
    else:
        if scheme == "postgresql+asyncpg":
            scheme = "postgresql"
        if "ssl" in query and "sslmode" not in query:
            query["sslmode"] = query.pop("ssl")

    return urlunsplit((scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
