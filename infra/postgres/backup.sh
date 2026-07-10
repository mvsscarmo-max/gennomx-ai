#!/bin/sh
set -eu

backup_dir="/backups"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
target="${backup_dir}/gennomx-${timestamp}.dump"

mkdir -p "$backup_dir"
pg_dump --format=custom --no-owner --no-privileges --file="$target"
sha256sum "$target" > "${target}.sha256"

find "$backup_dir" -name 'gennomx-*.dump' -type f -mtime "+${BACKUP_RETENTION_DAYS:-14}" -delete
find "$backup_dir" -name 'gennomx-*.dump.sha256' -type f -mtime "+${BACKUP_RETENTION_DAYS:-14}" -delete

echo "backup_created=$target"