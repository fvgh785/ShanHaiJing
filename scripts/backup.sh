#!/bin/bash
#
# backup.sh - SQLite Database Backup Script for ShanHaiJing
#
# This script runs inside the Flask container (or on the host with access
# to the Docker volume) to create timestamped SQLite backups and enforce
# a 30-day retention policy.
#
# Usage:
#   In container:  docker compose exec flask /bin/bash /app/scripts/backup.sh
#   On host:       bash scripts/backup.sh
#   Cron (host):   0 3 * * * cd /path/to/ShanHaiJing && bash scripts/backup.sh >> logs/backup.log 2>&1
#
# Cron on Alibaba Cloud Linux 3 (RHEL-based):
#   crontab -e
#   0 3 * * * cd /opt/ShanHaiJing && bash scripts/backup.sh >> logs/backup.log 2>&1

set -euo pipefail

# ============================================================
# Configuration
# ============================================================

# Try common paths for the database file
# Priority: Docker volume mount, then local relative path
if [ -f "/app/instance/app.db" ]; then
    DB_PATH="/app/instance/app.db"
    BACKUP_DIR="/app/backups"
elif [ -f "./backend/instance/app.db" ]; then
    DB_PATH="./backend/instance/app.db"
    BACKUP_DIR="./backend/backups"
else
    # Fallback: search for the database file
    DB_PATH=$(find . -name "app.db" -not -path "*/node_modules/*" -print -quit 2>/dev/null || true)
    if [ -z "$DB_PATH" ]; then
        echo "[ERROR] Cannot find app.db. Please set DB_PATH manually."
        exit 1
    fi
    BACKUP_DIR="$(dirname "$DB_PATH")/../backups"
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.db"
RETENTION_DAYS=30
LOG_FILE="${BACKUP_DIR}/../logs/backup.log"

# Ensure directories exist
mkdir -p "$BACKUP_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

# ============================================================
# Logging helper
# ============================================================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# ============================================================
# Pre-flight checks
# ============================================================

log "========== Starting backup =========="

if [ ! -f "$DB_PATH" ]; then
    log "[ERROR] Database file not found at: $DB_PATH"
    exit 1
fi

# Check if sqlite3 is available
if ! command -v sqlite3 &> /dev/null; then
    log "[ERROR] sqlite3 command not found. Please install sqlite3."
    exit 1
fi

# Check disk space (require at least 50MB free)
REQUIRED_SPACE_KB=51200
AVAILABLE_SPACE_KB=$(df "$BACKUP_DIR" 2>/dev/null | awk 'NR==2 {print $4}' || echo 0)
if [ "$AVAILABLE_SPACE_KB" -lt "$REQUIRED_SPACE_KB" ] 2>/dev/null; then
    log "[WARN] Low disk space: ${AVAILABLE_SPACE_KB}KB available, ${REQUIRED_SPACE_KB}KB required"
fi

# ============================================================
# Backup
# ============================================================

DB_SIZE_BEFORE=$(stat -c%s "$DB_PATH" 2>/dev/null || stat -f%z "$DB_PATH" 2>/dev/null || echo "unknown")

log "Source DB: $DB_PATH ($DB_SIZE_BEFORE bytes)"
log "Backup file: $BACKUP_FILE"

# Perform the backup using sqlite3 .backup command
# This is safe for WAL-mode databases and creates a consistent snapshot
if sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"; then
    BACKUP_SIZE=$(stat -c%s "$BACKUP_FILE" 2>/dev/null || stat -f%z "$BACKUP_FILE" 2>/dev/null || echo "unknown")
    log "[OK] Backup created successfully: $BACKUP_FILE ($BACKUP_SIZE bytes)"
else
    log "[ERROR] Backup failed!"
    # Clean up partial backup file
    rm -f "$BACKUP_FILE"
    exit 1
fi

# Verify backup integrity
log "Verifying backup integrity..."
VERIFY_RESULT=$(sqlite3 "$BACKUP_FILE" "PRAGMA integrity_check;" 2>&1)
if [ "$VERIFY_RESULT" = "ok" ]; then
    log "[OK] Backup integrity check passed"
else
    log "[ERROR] Backup integrity check failed: $VERIFY_RESULT"
    # Keep the backup file for debugging but mark it
    mv "$BACKUP_FILE" "${BACKUP_FILE}.corrupt"
    exit 1
fi

# Record WAL checkpoint info (helps verify backup completeness)
WAL_CHECKPOINT=$(sqlite3 "$DB_PATH" "PRAGMA wal_checkpoint(TRUNCATE);" 2>&1 || echo "wal_checkpoint unavailable")
log "WAL checkpoint: $WAL_CHECKPOINT"

# ============================================================
# Retention: delete backups older than RETENTION_DAYS
# ============================================================

log "Cleaning up backups older than ${RETENTION_DAYS} days..."

DELETED_COUNT=0
for f in "$BACKUP_DIR"/backup_*.db; do
    [ -f "$f" ] || continue
    # Skip corrupted backups (clean them up separately)
    case "$f" in
        *.corrupt) continue ;;
    esac

    # Use find to check file age and delete
    FILE_AGE_DAYS=$(find "$f" -mtime +${RETENTION_DAYS} 2>/dev/null | wc -l)
    if [ "$FILE_AGE_DAYS" -gt 0 ] 2>/dev/null; then
        rm -f "$f"
        DELETED_COUNT=$((DELETED_COUNT + 1))
        log "[CLEAN] Removed expired backup: $(basename "$f")"
    fi
done

# Also clean up any corrupted backups older than 7 days
for f in "$BACKUP_DIR"/backup_*.db.corrupt; do
    [ -f "$f" ] || continue
    if find "$f" -mtime +7 2>/dev/null | grep -q .; then
        rm -f "$f"
        log "[CLEAN] Removed old corrupted backup: $(basename "$f")"
    fi
done

# ============================================================
# Summary
# ============================================================

CURRENT_BACKUPS=$(find "$BACKUP_DIR" -name "backup_*.db" ! -name "*.corrupt" 2>/dev/null | wc -l)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1 || echo "unknown")

log "=========================================="
log "Backup complete"
log "  DB path:     $DB_PATH"
log "  DB size:     $DB_SIZE_BEFORE bytes"
log "  Backup file: $BACKUP_FILE"
log "  Backup size: ${BACKUP_SIZE:-unknown} bytes"
log "  Retention:   ${RETENTION_DAYS} days ($DELETED_COUNT deleted this run)"
log "  Stored:      ${CURRENT_BACKUPS} backups"
log "  Total usage: ${TOTAL_SIZE}"
log "=========================================="

exit 0
