#!/usr/bin/env bash
# Jaikalki HRMS — nightly MySQL backup
#
# Designed to run from cron inside or alongside the docker-compose stack.
# Backs up to a host directory, gzip-compresses, and prunes anything older
# than RETAIN_DAYS days.
#
# Usage:
#   ./backup_mysql.sh
#
# Env (override per environment):
#   MYSQL_HOST       (default: mysql)
#   MYSQL_PORT       (default: 3306)
#   MYSQL_USER       (default: root)
#   MYSQL_PASSWORD   (required)
#   MYSQL_DATABASE   (default: db_hrms_jaikalki)
#   BACKUP_DIR       (default: /var/backups/jaikalki-hrms)
#   RETAIN_DAYS      (default: 30)
#
# Recommended cron (runs at 02:30 every day, host time):
#   30 2 * * * /opt/jaikalki/hrms/scripts/ops/backup_mysql.sh >> \
#       /var/log/jaikalki-hrms-backup.log 2>&1

set -euo pipefail

MYSQL_HOST="${MYSQL_HOST:-mysql}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_USER="${MYSQL_USER:-root}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:?MYSQL_PASSWORD is required}"
MYSQL_DATABASE="${MYSQL_DATABASE:-db_hrms_jaikalki}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/jaikalki-hrms}"
RETAIN_DAYS="${RETAIN_DAYS:-30}"

mkdir -p "$BACKUP_DIR"

stamp="$(date +%Y%m%d_%H%M%S)"
out="$BACKUP_DIR/${MYSQL_DATABASE}_${stamp}.sql.gz"

echo "[$(date)] Backing up ${MYSQL_DATABASE} -> $out"

mysqldump \
  --host="$MYSQL_HOST" \
  --port="$MYSQL_PORT" \
  --user="$MYSQL_USER" \
  --password="$MYSQL_PASSWORD" \
  --single-transaction \
  --quick \
  --routines \
  --triggers \
  --events \
  --default-character-set=utf8mb4 \
  --no-tablespaces \
  "$MYSQL_DATABASE" | gzip -9 > "$out"

size="$(du -h "$out" | cut -f1)"
echo "[$(date)] Done — ${size}"

# Prune old backups
echo "[$(date)] Pruning > ${RETAIN_DAYS} days old…"
find "$BACKUP_DIR" -type f -name "${MYSQL_DATABASE}_*.sql.gz" \
  -mtime "+${RETAIN_DAYS}" -print -delete || true

echo "[$(date)] Backup complete."
