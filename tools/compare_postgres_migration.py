"""Compare source and target PostgreSQL databases after a migration restore."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from typing import Any

import psycopg2

DEFAULT_TABLES = (
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


def fetch_one(database_url: str, query: str, params: tuple[Any, ...] = ()) -> Any:
    with psycopg2.connect(database_url, connect_timeout=20) as conn:
        conn.set_session(readonly=True, autocommit=True)
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
            return None if row is None else row[0]


def table_exists(database_url: str, table: str) -> bool:
    return bool(fetch_one(database_url, "select to_regclass(%s)", (f"public.{table}",)))


def table_count(database_url: str, table: str) -> int | None:
    if not table_exists(database_url, table):
        return None
    return int(fetch_one(database_url, f'select count(*) from public."{table}"'))


def table_checksum(database_url: str, table: str, sample_limit: int) -> str | None:
    if not table_exists(database_url, table):
        return None
    return fetch_one(
        database_url,
        f"""
        with rows as (
          select md5(row_to_json(t)::text) as row_hash
          from public."{table}" t
          order by md5(row_to_json(t)::text)
          limit %s
        )
        select coalesce(md5(string_agg(row_hash, '' order by row_hash)), 'empty')
        from rows
        """,
        (sample_limit,),
    )


def compare(source_url: str, target_url: str, tables: tuple[str, ...], sample_limit: int) -> dict:
    result = {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "sample_limit": sample_limit,
        "tables": {},
        "ok": True,
    }
    for table in tables:
        source_count = table_count(source_url, table)
        target_count = table_count(target_url, table)
        source_checksum = table_checksum(source_url, table, sample_limit)
        target_checksum = table_checksum(target_url, table, sample_limit)
        table_result = {
            "source_count": source_count,
            "target_count": target_count,
            "counts_match": source_count == target_count,
            "source_sample_checksum": source_checksum,
            "target_sample_checksum": target_checksum,
            "sample_checksums_match": source_checksum == target_checksum,
        }
        result["tables"][table] = table_result
        if not table_result["counts_match"] or not table_result["sample_checksums_match"]:
            result["ok"] = False
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-env", default="SUPABASE_DIRECT_URL")
    parser.add_argument("--target-env", default="VPS_DATABASE_URL_SYNC")
    parser.add_argument("--sample-limit", type=int, default=1000)
    parser.add_argument("--tables", default=",".join(DEFAULT_TABLES))
    args = parser.parse_args()
    source_url = os.environ.get(args.source_env)
    target_url = os.environ.get(args.target_env)
    if not source_url:
        raise SystemExit(f"Missing environment variable: {args.source_env}")
    if not target_url:
        raise SystemExit(f"Missing environment variable: {args.target_env}")
    tables = tuple(table.strip() for table in args.tables.split(",") if table.strip())
    result = compare(source_url, target_url, tables, args.sample_limit)
    print(json.dumps(result, indent=2))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
