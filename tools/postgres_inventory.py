"""Collect a safe PostgreSQL inventory for migration planning.

The script never prints connection strings or secrets. Pass the database URL
through an environment variable and redirect stdout to a private artifact when
the output contains operational metadata.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import psycopg2
import psycopg2.extras

CRITICAL_TABLES = (
    "alembic_version",
    "data_sources",
    "drug_assets",
    "companies",
    "clinical_trials",
    "clinical_trial_assets",
    "indications",
    "targets",
    "endpoints",
    "trial_results",
    "adverse_events",
    "regulatory_approvals",
    "publications",
    "source_documents",
    "evidence_snippets",
    "field_assertions",
    "data_conflicts",
    "manual_corrections",
    "ingestion_jobs",
    "mcp_query_logs",
    "security_events",
    "llm_call_logs",
)


def json_default(value: Any) -> str:
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return str(value)


def fetch_all(cursor, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    cursor.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


def fetch_scalar(cursor, query: str, params: tuple[Any, ...] = ()) -> Any:
    cursor.execute(query, params)
    row = cursor.fetchone()
    return None if row is None else row[0]


def collect_inventory(database_url: str) -> dict[str, Any]:
    with psycopg2.connect(database_url, connect_timeout=20) as conn:
        conn.set_session(readonly=True, autocommit=True)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            inventory: dict[str, Any] = {
                "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                "current_database": fetch_scalar(cursor, "select current_database()"),
                "current_user": fetch_scalar(cursor, "select current_user"),
                "postgres_version": fetch_scalar(cursor, "select version()"),
                "database_size": fetch_scalar(
                    cursor, "select pg_size_pretty(pg_database_size(current_database()))"
                ),
                "alembic_version": None,
                "extensions": fetch_all(
                    cursor,
                    """
                    select extname, extversion
                    from pg_extension
                    order by extname
                    """,
                ),
                "schemas": fetch_all(
                    cursor,
                    """
                    select schema_name
                    from information_schema.schemata
                    where schema_name not like 'pg_%'
                    order by schema_name
                    """,
                ),
                "tables": fetch_all(
                    cursor,
                    """
                    select schemaname, tablename, tableowner
                    from pg_tables
                    where schemaname not in ('pg_catalog', 'information_schema')
                    order by schemaname, tablename
                    """,
                ),
                "indexes": fetch_all(
                    cursor,
                    """
                    select schemaname, tablename, indexname, indexdef
                    from pg_indexes
                    where schemaname not in ('pg_catalog', 'information_schema')
                    order by schemaname, tablename, indexname
                    """,
                ),
                "sequences": fetch_all(
                    cursor,
                    """
                    select sequence_schema, sequence_name, data_type, start_value, minimum_value,
                           maximum_value, increment
                    from information_schema.sequences
                    where sequence_schema not in ('pg_catalog', 'information_schema')
                    order by sequence_schema, sequence_name
                    """,
                ),
                "rls_policies": fetch_all(
                    cursor,
                    """
                    select schemaname, tablename, policyname, permissive, roles, cmd, qual,
                           with_check
                    from pg_policies
                    where schemaname not in ('pg_catalog', 'information_schema')
                    order by schemaname, tablename, policyname
                    """,
                ),
                "grants": fetch_all(
                    cursor,
                    """
                    select table_schema, table_name, grantee, privilege_type
                    from information_schema.role_table_grants
                    where table_schema not in ('pg_catalog', 'information_schema')
                    order by table_schema, table_name, grantee, privilege_type
                    """,
                ),
                "roles": fetch_all(
                    cursor,
                    """
                    select rolname, rolsuper, rolbypassrls, rolcreatedb, rolcreaterole,
                           rolcanlogin
                    from pg_roles
                    where rolname like 'gennomx_%'
                    order by rolname
                    """,
                ),
                "critical_counts": {},
                "supabase_specific_objects": {},
            }
            if fetch_scalar(cursor, "select to_regclass('public.alembic_version')"):
                inventory["alembic_version"] = fetch_scalar(
                    cursor, "select version_num from public.alembic_version"
                )
            for table in CRITICAL_TABLES:
                if fetch_scalar(cursor, "select to_regclass(%s)", (f"public.{table}",)):
                    inventory["critical_counts"][table] = fetch_scalar(
                        cursor, f'select count(*) from public."{table}"'
                    )
            inventory["supabase_specific_objects"] = {
                "schemas": fetch_all(
                    cursor,
                    """
                    select schema_name
                    from information_schema.schemata
                    where schema_name in ('auth', 'storage', 'graphql_public', 'realtime',
                                          'supabase_functions', 'vault')
                    order by schema_name
                    """,
                ),
                "roles": fetch_all(
                    cursor,
                    """
                    select rolname, rolcanlogin, rolsuper, rolbypassrls
                    from pg_roles
                    where rolname in ('anon', 'authenticated', 'service_role', 'supabase_admin',
                                      'supabase_auth_admin', 'supabase_storage_admin')
                    order by rolname
                    """,
                ),
            }
            return inventory


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--url-env",
        default="DATABASE_URL_SYNC",
        help="Environment variable containing the PostgreSQL URL.",
    )
    args = parser.parse_args()
    database_url = os.environ.get(args.url_env)
    if not database_url:
        raise SystemExit(f"Missing environment variable: {args.url_env}")
    print(json.dumps(collect_inventory(database_url), indent=2, default=json_default))


if __name__ == "__main__":
    main()
