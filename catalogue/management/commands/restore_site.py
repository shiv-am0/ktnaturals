"""Restore a snapshot to a NEW isolated directory; never touch the live site."""

from contextlib import closing
import json
from pathlib import Path
import shutil
import sqlite3
from django.core.management.base import BaseCommand, CommandError
from .backup_site import checksum


def restore_backup(snapshot, target):
    snapshot, target = Path(snapshot), Path(target)
    manifest = json.loads((snapshot / "manifest.json").read_text())
    if manifest.get("version") != 1 or not isinstance(manifest.get("files"), dict):
        raise ValueError("Unsupported manifest.")
    if "db.sqlite3" not in manifest["files"]:
        raise ValueError("Missing database.")
    for name, digest in manifest["files"].items():
        path = Path(name)
        if (
            path.is_absolute()
            or ".." in path.parts
            or "\\" in name
            or path.as_posix() != name
            or not (name == "db.sqlite3" or name.startswith("media/"))
        ):
            raise ValueError("Unsafe manifest path: " + name)
        source = snapshot / path
        if any(p.is_symlink() for p in [source, *source.parents]):
            raise ValueError("Symlinks are not allowed in snapshots.")
        if not source.is_file() or not source.resolve().is_relative_to(
            snapshot.resolve()
        ):
            raise ValueError("Invalid snapshot file: " + name)
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError("Invalid checksum.")
    target.mkdir(mode=0o700)
    try:
        for name, digest in manifest["files"].items():
            source = snapshot / name
            if checksum(source) != digest:
                raise ValueError("Checksum mismatch: " + name)
            output = target / name
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, output)
        with closing(sqlite3.connect(target / "db.sqlite3")) as db:
            if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                raise ValueError("SQLite integrity check failed")
        (target / "media").mkdir(exist_ok=True)
        return target
    except BaseException:
        shutil.rmtree(target)
        raise


class Command(BaseCommand):
    help = "Verify and restore a backup into a new directory (no overwrite)."

    def add_arguments(self, parser):
        parser.add_argument("snapshot")
        parser.add_argument("--target", required=True)

    def handle(self, *args, **options):
        try:
            result = restore_backup(options["snapshot"], options["target"])
        except (OSError, ValueError, KeyError, sqlite3.Error) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(str(result))
