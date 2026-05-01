#!/usr/bin/env bash
# Jaikalki HRMS — restore a gzipped MySQL dump produced by backup_mysql.sh.
#
# WARNING: This DROPS and recreates the target database. Run with care.
#
# Usage:
#   ./restore_mysql.sh /path/to/db_hrms_jaikalki_20260501_023000.sql.gz
#
# Env (override per environment):
#   MYSQL_HOST       (default: mysql)
#   MYSQL_PORT       (default: 3306)
#   MYSQL_USER       (default: root)
#   MYSQL_PASSWORD   (required)
#   MYSQL_DATABASE   (default: db_hrms_jaikalki)

set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 <backup-file.sql.gz>" >&2
  exit 2
fi

DUMP="$1"
if [ ! -f "$DUMP" ]; then
  echo "Backup file not found: $DUMP" >&2
  exit 1
fi

MYSQL_HOST="${MYSQL_HOST:-mysql}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_USER="${MYSQL_USER:-root}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:?MYSQL_PASSWORD is required}"
MYSQL_DATABASE="${MYSQL_DATABASE:-db_hrms_jaikalki}"

read -r -p "This will DROP and recreate '${MYSQL_DATABASE}' on ${MYSQL_HOST}. Continue? [y/N] " ok
case "$ok" in
  y|Y|yes|YES) ;;
  *) echo "Aborted."; exit 1 ;;
esac

echo "[$(date)] Recreating database…"
mysql \
  --host="$MYSQL_HOST" \
  --port="$MYSQL_PORT" \
  --user="$MYSQL_USER" \
  --password="$MYSQL_PASSWORD" \
  --execute="DROP DATABASE IF EXISTS \`${MYSQL_DATABASE}\`;
             CREATE DATABASE \`${MYSQL_DATABASE}\`
               CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

echo "[$(date)] Restoring from ${DUMP}…"
gunzip -c "$DUMP" | mysql \
  --host="$MYSQL_HOST" \
  --port="$MYSQL_PORT" \
  --user="$MYSQL_USER" \
  --password="$MYSQL_PASSWORD" \
  --default-character-set=utf8mb4 \
  "$MYSQL_DATABASE"

echo "[$(date)] Restore complete."
