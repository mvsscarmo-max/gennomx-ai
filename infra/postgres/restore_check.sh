#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "usage: restore_check.sh /backups/gennomx-YYYYmmddTHHMMSSZ.dump" >&2
  exit 2
fi

dump_path="$1"
check_db="${RESTORE_CHECK_DB:-gennomx_restore_check}"

dropdb --if-exists "$check_db"
createdb "$check_db"
pg_restore --no-owner --no-privileges --dbname "$check_db" "$dump_path"
psql "$check_db" -v ON_ERROR_STOP=1 -c "select version_num from alembic_version;"
psql "$check_db" -v ON_ERROR_STOP=1 -c "select count(*) as data_sources from data_sources;"
dropdb "$check_db"

echo "restore_check=ok dump=$dump_path"