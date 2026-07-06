"""Apply the generated Supabase role bootstrap SQL.

This script intentionally prompts for the administrative database password so
the password does not need to be written to any project file.
"""

from __future__ import annotations

import getpass
from pathlib import Path

import psycopg2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SQL_PATH = PROJECT_ROOT / "secrets" / "supabase_bootstrap_roles.generated.sql"


def main() -> None:
    password = getpass.getpass("Supabase DB password: ")
    dsn = (
        "host=db.qfanrziwepkqkgtvfrdt.supabase.co "
        "port=5432 "
        "dbname=postgres "
        "user=postgres "
        f"password={password} "
        "sslmode=require"
    )
    sql = SQL_PATH.read_text(encoding="utf-8")
    with psycopg2.connect(dsn, connect_timeout=15) as conn:
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute(sql)
    print("Supabase bootstrap applied.")


if __name__ == "__main__":
    main()
