#!/bin/bash
# Automated database backup script for PostgreSQL (Supabase / Local)
# Intended to be run via cron on the VPS:
# 0 2 * * * /path/to/scripts/backup_db.sh

# Variables (Set these or pass them via ENV)
DB_USER=${DB_USER:-"postgres"}
DB_HOST=${DB_HOST:-"localhost"}
DB_PORT=${DB_PORT:-"5432"}
DB_NAME=${DB_NAME:-"pathlab"}
BACKUP_DIR=${BACKUP_DIR:-"/var/backups/pathlab"}
DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${DATE}.sql.gz"
RETENTION_DAYS=7

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

echo "Starting database backup to $BACKUP_FILE..."

# Run pg_dump and compress on the fly
# PGPASSWORD must be set in the environment or ~/.pgpass file
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" | gzip > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "Backup completed successfully."
else
    echo "Backup failed!"
    exit 1
fi

# Clean up older backups
echo "Removing backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -type f -name "${DB_NAME}_*.sql.gz" -mtime +$RETENTION_DAYS -exec rm -f {} \;

echo "Backup process finished."
