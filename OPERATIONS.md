# KT Naturals operations

## Scope and prerequisites

One Linux server, local persistent SQLite, one Gunicorn worker with two threads, Caddy HTTPS. No Redis, task queue, managed database or PostgreSQL service. SQLite has no licence/subscription fee; the VPS/local disk, domain registration, optional off-server storage/egress and any paid email service cost separately. Obtain current provider quotes; this is not a promise of free hosting.

Docker Engine + Compose plugin are required on the production host. Keep the repository on local disk, **not NFS/network storage**. Run from the repository root. The application container runs as UID/GID **10001**, read-only root filesystem, all Linux capabilities dropped. Only data/media/static mounts and temporary storage are writable. Gunicorn has no host-exposed port; do not expose it separately because Django trusts Caddy's forwarded HTTPS header. Caddy alone exposes TCP 80/443 and UDP 443, and retains its certificate state in named volumes. Caddy's standard image runs as root; its media/static mounts are read-only. Never mount the Docker socket into either container.

## Local development

Follow README.md for full development and owner instructions. Minimal setup:

```sh
uv venv --python 3.13
uv pip install -r requirements.txt
cp .env.example .env
# Edit .env: DJANGO_DEBUG=true, local SITE_URL/allowed hosts.
mkdir -p data media staticfiles
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver 127.0.0.1:8000
```

Create the owner interactively; never put passwords in source, command history or environment files. `manage.py changepassword USERNAME` resets a password. Demo data is opt-in/local-only; see README. No production sample-data command is part of startup.

## Production preparation (operator executes only after authorization)

Nothing here has been deployed publicly, no host scheduler was enabled, and no paid resources were created by the build. Obtain the real domain, owner data/photos, reviewed policy text and authorization first.

1. Provision/update Linux and Docker. Create a dedicated deployment operator; Docker-group membership is effectively root privilege. Protect SSH with keys. Arrange disk-space monitoring and failure alerts.
2. Clone to `/opt/ktnaturals` (or change the paths in the systemd service). Point the real domain's A record at the server and only add AAAA if IPv6 works. Permit inbound 80/443; restrict SSH. Review host firewall configuration yourself.
3. Create `.env` privately (`chmod 600 .env`). Set the following values; replace placeholders, do not use them as credentials:

```dotenv
DOMAIN=your-real-domain.example
ACME_EMAIL=your-real-owner-email@example.com
DJANGO_SECRET_KEY=replace-with-a-long-random-secret
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=your-real-domain.example
SITE_URL=https://your-real-domain.example
```

Generate the secret locally with `.venv/bin/python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`, store it securely, and paste into `.env` quoted if needed. Compose injects DEBUG=false and derives the allowed host and SITE_URL from DOMAIN. DOMAIN is **one hostname**, no scheme/path. Default direct-Python locations are `data/db.sqlite3`, `media/`, `staticfiles/`; Compose fixes these inside `/app`. Secrets and runtime data are excluded from the Docker build context.

4. Prepare bind mounts. Run these only on the intended new deployment directories, not unrelated existing paths:

```sh
sudo install -d -o 10001 -g 10001 -m 0750 data
sudo install -d -o 10001 -g 10001 -m 0755 media staticfiles
# Dedicated backup store: UID 10001 must write it; operator must read/lock it.
# Replace DEPLOY_GROUP with the deployment operator's primary group.
sudo install -d -o 10001 -g DEPLOY_GROUP -m 0770 /var/backups/ktnaturals
```

Snapshots themselves are mode 0700, owned by UID 10001. Run the backup operator as UID 10001 (recommended: create `ktnaturals` with that UID on a fresh host), or explicitly grant that operator backup access using host ACLs. Do not make backups world-readable: they include password hashes, contact details and session data. The supplied service assumes that user is named `ktnaturals`.

5. Build, migrate and collect static explicitly (startup never silently migrates):

```sh
docker compose config --quiet
docker compose build --pull
docker compose run --rm --no-deps app python manage.py migrate
docker compose run --rm --no-deps app python manage.py collectstatic --noinput
docker compose run --rm --no-deps app python manage.py check --deploy
docker compose run --rm --no-deps app python manage.py createsuperuser
docker compose up -d
docker compose ps
docker compose logs --tail=100 app caddy
```

Caddy obtains public HTTPS only once DNS/firewall and domain ownership are correct. Check redirects, real HTTPS certificate, home/product/owner pages, uploaded images, CSS, staff-only access and upload limits. Check actual forms through HTTPS, not only a health endpoint. Caddy serves only jpg/jpeg/png/webp under `/media/`, never uploaded HTML/SVG; no directory browsing or executable handlers are enabled. Owner uploads must still be validated/re-encoded by Django. Static files are trusted build artifacts. Media URLs are public; don't upload private documents.

## Consistent backups, scheduling and retention

**A persistent disk/volume is not a backup.** A database-only snapshot is not sufficient either.

`backup_site` uses Python's supported SQLite `Connection.backup()` API against a read-only source connection; this includes committed WAL content without naively copying a live db/WAL/shm trio. It copies all media, writes SHA-256 checksums and a versioned manifest, and publishes the snapshot by renaming a staging directory. Only completed, tool-named snapshots are eligible for local retention. Default retention is seven snapshots, not seven calendar days. Backups contain extra unreferenced media too, deliberately.

**Media consistency requires maintenance downtime.** SQLite's API alone cannot make database rows and filesystem changes atomic together. Before the snapshot starts, stop every Gunicorn/app process and all import/upload/cleanup/admin-shell jobs touching the database or media. Keep them stopped through completion. `--writes-stopped` is an explicit operator assertion, not a magic lock or maintenance switch. Do not use it while `runserver`, another container, or a media cleanup process runs. Do not manually delete/replace images during the window. The supplied wrapper stops the sole Compose app (75-second graceful timeout) and restarts it on backup failure as well as success; Caddy continues to serve static/media but dynamic routes temporarily return 502. Schedule in a quiet window and tell the owner. Off-server transfer happens after restarting the app.

For local development, stop `runserver` and other writers, then:

```sh
.venv/bin/python manage.py backup_site --destination ./backups --keep 7 --writes-stopped
.venv/bin/python manage.py restore_site ./backups/snapshot-EXACT-NAME --target ./restore-drill
.venv/bin/python -m unittest catalogue.tests.test_backups -v
```

Use the actual snapshot path printed by the backup command. The restore target **must not exist**. The command verifies checksums, permitted relative paths, rejects symlinks, runs SQLite `integrity_check`, and cleans an incomplete restore target on failure. It never overwrites the live database. Snapshots are directories, not archives, so there is no tar/zip extraction step. Treat backup directories as immutable and trusted operator-controlled inputs; checksums detect corruption, **not malicious changes to both payload and manifest**. They are not signatures. Download untrusted copies only to a restricted staging location and don't let another process modify them during restore.

Production wrapper:

1. Install `rclone` and configure an **off-server** remote as the deployment operator (`rclone config`). Prefer rclone crypt with separately safeguarded encryption keys and a dedicated remote prefix. A remote pointing to this same VPS is not off-server backup. No credentials belong in this repository.
2. Copy `deploy/backup.env.example` to a private operator-controlled environment file and set absolute BACKUP_DEST, BACKUP_KEEP and OFFSERVER_DEST. The local backup directory must already exist. The remote must have enough capacity and read/write/list permissions.
3. Test manually as the operator:

```sh
set -a
. /etc/ktnaturals-backup.env
set +a
bash deploy/backup.sh
```

The wrapper uses `flock` to prevent overlapping wrapper runs; don't bypass it with concurrent direct commands. It copies (never sync-deletes) snapshots using rclone and verifies the remote with `rclone check --one-way --download`. A transfer/check error exits nonzero. Configure independent off-server retention/versioning, for example 30 daily copies, and protect against deletion with provider retention/object lock where available. No remote deletion policy is enabled automatically. Monitor storage use; local rotation does not rotate remote copies.

4. Review paths/user/timezone and manually install the provided scheduler examples, **only after a successful local + off-server restore drill**:

```sh
sudo install -m 0644 deploy/ktnaturals-backup.service deploy/ktnaturals-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ktnaturals-backup.timer
systemctl list-timers ktnaturals-backup.timer
journalctl -u ktnaturals-backup.service
```

The timer is 03:00 **server timezone**, plus up to ten minutes jitter. Configure monitoring to alert on a failed unit, missing fresh snapshots and failed remote checks; supplying a timer is not failure alerting. With daily successful backups the recovery-point target is up to one day; measure actual recovery time during drills. Before migrations/large edits take an extra backup. Back up `.env`, encryption keys and domain/DNS recovery information separately in a secure password manager, not public media.

## Restore drill and disaster recovery

At least monthly and after backup changes:

1. Download one complete off-server snapshot to a new private local staging directory (`rclone copy REMOTE:snapshot-path LOCAL-STAGING`); select a known completed snapshot.
2. Run `manage.py restore_site LOCAL-STAGING --target NEW-DIRECTORY`. Never use the production data directory as target. In Docker, mount the snapshot read-only and a new empty parent directory writable by UID 10001:

```sh
docker compose run --rm --no-deps \
  -v /absolute/snapshot:/snapshot:ro -v /absolute/drill-parent:/restore \
  app python manage.py restore_site /snapshot --target /restore/drill
```

3. Check restored database content/product counts and photos, then exercise a **separate local-only** app using `DATABASE_PATH=/absolute/drill/db.sqlite3 MEDIA_ROOT=/absolute/drill/media DJANGO_DEBUG=true SITE_URL=http://127.0.0.1:8001 .venv/bin/python manage.py runserver 127.0.0.1:8001`. Use the matching application release; review required migrations before applying them to the restored copy. Do not send real enquiries during the drill. Record date, snapshot, recovered image/content checks and elapsed recovery time. Automated tests cover a WAL-mode database plus exact image bytes and unsafe/corrupt restores without core-model dependencies.
4. Actual recovery is a deliberate maintenance change: stop app/all writers, retain the previous **whole** data directory (including any WAL/shm sidecars) and media directory under new rollback names, install the verified restored db in a **new empty data directory** and its paired media directory, assign ownership to UID 10001, ensure media dirs/files are readable by Caddy (0755/0644), then start the matching release. Never place a restored db beside stale `-wal`/`-shm` files. Do not merge a restored database with unrelated newer media. Roll back using the matched old pair if needed. Re-run production checks and owner acceptance after recovery.

## Updates and later PostgreSQL migration

Take and verify a paired snapshot; stop the app; pull reviewed code; build; run migrations and collectstatic with one-off containers; `docker compose up -d --build`. Avoid concurrent migrations. Preserve release identifiers with your operations log; DB schema rollback is not guaranteed by code rollback. Do not run `docker compose down -v` casually: it deletes Caddy certificate state (bind-mounted data survives, but that still isn't backup).

Review Python/Django/Gunicorn/Caddy security updates regularly and rebuild images. Exact dependency pins aid reproducibility; pin container digests when promoting a tested release and refresh deliberately. Monitor local disk/inodes, SQLite busy errors and write latency.

Move to PostgreSQL when concurrent write pressure, orders/workflows or multiple app servers justify it—not just because the catalogue exists. Plan a separate project: provision/budget PostgreSQL; add a supported driver and environment-based DATABASES configuration; run migrations on an empty DB; during a write freeze export application/auth data with Django's portable serialization or a tested migration utility (handle content types/permissions and natural keys carefully); import, reset sequences, validate decimal prices, relationships, slugs, counts, auth, photos and enquiries; switch configuration and keep the frozen SQLite+media snapshot for rollback. Media still needs its own backup. Repeat tests against PostgreSQL, adopt PostgreSQL-native backup/PITR and execute a restore drill before accepting the migration. The present backup commands are intentionally SQLite-only, not PostgreSQL backup tools.

## Verification performed during the build

- `.venv/bin/python -m unittest catalogue.tests.test_backups deploy.test_backup_wrapper -v`: 12 passed (8 real temporary SQLite/media tests and 4 wrapper control-flow tests using fake Docker/rclone commands). A separate real-rclone local-to-local test confirms hidden media files transfer while root lock/staging files are excluded.
- `DJANGO_DEBUG=true .venv/bin/python manage.py test catalogue.tests.test_backups -v 1`: 8 passed; Django system checks clean.
- `docker build -t ktnaturals:local-verify .`: built successfully using Python 3.13 and the pinned requirements available at build time. Rebuild after subsequent source changes.
- Compose configuration validation with non-secret example environment values and `bash -n deploy/backup.sh`: passed.
- `caddy validate` in `caddy:2.10-alpine`: valid configuration; Caddyfile formatted and redundant forwarded-header override removed.

The wrapper tests do not prove real remote credentials or a public deployment works. Public deployment and production credentials were not exercised.

## External steps not verified by local tests

Real domain/DNS, public ACME certificate issuance, host firewall, operator UID/permissions on the target server, scheduler activation, off-server credentials/transfer, remote retention/encryption recovery and alert delivery require owner/operator setup and verification. No local success should be interpreted as having tested those external systems.
