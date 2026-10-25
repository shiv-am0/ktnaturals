"""Consistent SQLite/media snapshots. All application writers MUST be stopped."""

from contextlib import closing
from datetime import datetime, timezone
import re
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import uuid

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


def checksum(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def create_backup(database, media, destination, *, writes_stopped=False, keep=7):
    database, media, destination = map(Path, (database, media, destination))
    if not writes_stopped:
        raise ValueError(
            "Stop all application/media writers and confirm --writes-stopped."
        )
    if keep < 1:
        raise ValueError("Retention must be at least one snapshot.")
    if destination.resolve().is_relative_to(media.resolve()):
        raise ValueError("Backup destination cannot be inside media.")
    if not database.is_file() or not media.is_dir():
        raise ValueError("Database file and media directory must exist.")
    for path in [media, *media.rglob("*")]:
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError("Media must contain only ordinary files/directories.")
    destination.mkdir(parents=True, exist_ok=True)
    name = (
        "snapshot-"
        + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ-")
        + uuid.uuid4().hex[:8]
    )
    stage = destination / ("." + name)
    final = destination / name
    stage.mkdir(mode=0o700)
    try:
        with closing(
            sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
        ) as source:
            with closing(sqlite3.connect(stage / "db.sqlite3")) as target:
                source.backup(target)
        shutil.copytree(media, stage / "media")
        files = {
            p.relative_to(stage).as_posix(): checksum(p)
            for p in stage.rglob("*")
            if p.is_file()
        }
        (stage / "manifest.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "files": files,
                },
                indent=2,
            )
            + "\n"
        )
        stage.rename(final)
        completed = sorted(
            p
            for p in destination.iterdir()
            if re.fullmatch(r"snapshot-\d{8}T\d{12}Z-[0-9a-f]{8}", p.name)
            and p.is_dir()
            and not p.is_symlink()
            and (p / "manifest.json").is_file()
        )
        for old in completed[:-keep]:
            shutil.rmtree(old)
        return final
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise


class Command(BaseCommand):
    help = "Back up SQLite and media; stop all writers before using --writes-stopped."

    def add_arguments(self, parser):
        parser.add_argument("--destination", required=True)
        parser.add_argument("--keep", type=int, default=7)
        parser.add_argument("--writes-stopped", action="store_true")

    def handle(self, *args, **options):
        try:
            result = create_backup(
                settings.DATABASES["default"]["NAME"],
                settings.MEDIA_ROOT,
                options["destination"],
                writes_stopped=options["writes_stopped"],
                keep=options["keep"],
            )
        except (OSError, ValueError, sqlite3.Error) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(str(result))
