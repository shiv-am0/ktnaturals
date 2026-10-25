#!/usr/bin/env bash
# Run as the deployment operator; all other DB/media writers must be disabled.
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
: "${BACKUP_DEST:?Set BACKUP_DEST to an absolute, dedicated local backup directory}"
: "${OFFSERVER_DEST:?Set OFFSERVER_DEST to an rclone remote:path on another server}"
[[ "$BACKUP_DEST" = /* ]] || { printf '%s\n' 'BACKUP_DEST must be absolute' >&2; exit 1; }
command -v rclone >/dev/null
# Host lock prevents overlapping scheduled/manual runs of this wrapper.
exec 9>"$BACKUP_DEST/.backup.lock"
flock -n 9 || exit 1
umask 077
restart() { docker compose start app; }
# Install cleanup before stop: even a partially failed stop must recover service.
trap restart EXIT
docker compose stop -t 75 app
# No entrypoint migration and no other app process: media stays frozen throughout.
docker compose run --rm --no-deps -T \
    -v "$BACKUP_DEST:/backups" app \
    python manage.py backup_site --destination /backups --keep "${BACKUP_KEEP:-7}" --writes-stopped
docker compose start app
trap - EXIT
# Exclude only root lock and unfinished staging snapshots; hidden media inside
# completed snapshots must be transferred and checked against the manifest.
rclone copy "$BACKUP_DEST" "$OFFSERVER_DEST" \
    --exclude '/.backup.lock' --exclude '/.snapshot-*/**' --exclude '/.snapshot-*' --checksum
rclone check "$BACKUP_DEST" "$OFFSERVER_DEST" \
    --exclude '/.backup.lock' --exclude '/.snapshot-*/**' --exclude '/.snapshot-*' --one-way --download
