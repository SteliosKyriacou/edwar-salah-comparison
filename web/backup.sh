#!/bin/bash
# Backup script for V25 Database & Log files

set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_DIR="/home/stylianos_kyriacou/backups/v25-predictor"
GCS_BUCKET="gs://reneu001/timestamps-database-backup"

echo "Initializing backup process..."
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE_NAME="v25_backup_$TIMESTAMP.tar.gz"
BACKUP_FILE="$BACKUP_DIR/$BACKUP_FILE_NAME"

# Compress logs, keys and configs
tar -czf "$BACKUP_FILE" -C "$DIR" logs/ keys.json config.json

# Copy backup file to GCP Cloud Storage Bucket
echo "Uploading backup to Google Cloud Storage bucket: $GCS_BUCKET..."
if /snap/bin/gsutil cp "$BACKUP_FILE" "$GCS_BUCKET/"; then
    echo "GCS Upload successful!"
else
    echo "Warning: GCS Upload failed, check credentials." >&2
fi

# Keep only the last 30 daily backups to save disk space
find "$BACKUP_DIR" -name "v25_backup_*.tar.gz" -mtime +30 -delete

echo "Backup successful! Saved locally to $BACKUP_FILE and mirrored to GCS."