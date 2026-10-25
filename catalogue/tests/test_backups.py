"""Standalone unittest restore drills; also discovered by Django."""

from contextlib import closing
import importlib
from pathlib import Path
import sqlite3
import tempfile
import unittest


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = self.root / "live.sqlite3"
        with closing(sqlite3.connect(self.db)) as db:
            db.execute("CREATE TABLE sample (value TEXT)")
        self.media = self.root / "media"
        self.media.mkdir()
        (self.media / "photo.webp").write_bytes(b"photo")

    def backup(self, **kwargs):
        from catalogue.management.commands.backup_site import create_backup

        return create_backup(self.db, self.media, self.root / "backups", **kwargs)

    def test_requires_maintenance_confirmation(self):
        with self.assertRaises(ValueError):
            self.backup()

    def test_retention_only_removes_completed_snapshots(self):
        first = self.backup(writes_stopped=True, keep=1)
        unrelated = self.root / "backups" / "notes"
        unrelated.mkdir()
        second = self.backup(writes_stopped=True, keep=1)
        self.assertFalse(first.exists())
        self.assertTrue(second.exists())
        self.assertTrue(unrelated.exists())

    def test_rejects_media_symlink(self):
        (self.media / "outside").symlink_to(self.db)
        with self.assertRaises(ValueError):
            self.backup(writes_stopped=True)

    def test_rejects_backup_inside_media(self):
        from catalogue.management.commands.backup_site import create_backup

        with self.assertRaises(ValueError):
            create_backup(
                self.db, self.media, self.media / "backups", writes_stopped=True
            )

    def test_restore_rejects_traversal(self):
        import json
        from catalogue.management.commands.restore_site import restore_backup
        from catalogue.management.commands.backup_site import checksum

        snapshot = self.backup(writes_stopped=True)
        manifest = json.loads((snapshot / "manifest.json").read_text())
        manifest["files"]["../../escaped"] = checksum(self.media / "photo.webp")
        (snapshot / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaises(ValueError):
            restore_backup(snapshot, self.root / "restore")
        self.assertFalse((self.root / "restore").exists())

    def test_restore_refuses_overwrite_and_corruption(self):
        from catalogue.management.commands.restore_site import restore_backup

        snapshot = self.backup(writes_stopped=True)
        with self.assertRaises(FileExistsError):
            restore_backup(snapshot, self.media)
        (snapshot / "media/photo.webp").write_bytes(b"corrupt")
        with self.assertRaises(ValueError):
            restore_backup(snapshot, self.root / "restore")
        self.assertFalse((self.root / "restore").exists())

    def test_restore_rejects_symlink(self):
        from catalogue.management.commands.restore_site import restore_backup

        snapshot = self.backup(writes_stopped=True)
        (snapshot / "media/photo.webp").unlink()
        (snapshot / "media/photo.webp").symlink_to(self.media / "photo.webp")
        with self.assertRaises(ValueError):
            restore_backup(snapshot, self.root / "restore")

    def test_wal_database_and_media_round_trip(self):
        try:
            spec = importlib.util.find_spec("catalogue.management.commands.backup_site")
        except ModuleNotFoundError:
            spec = None
        self.assertIsNotNone(spec, "backup implementation must exist")
        backup = importlib.import_module("catalogue.management.commands.backup_site")
        restore = importlib.import_module("catalogue.management.commands.restore_site")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            media = root / "media"
            media.mkdir()
            (media / "photo.webp").write_bytes(b"image bytes")
            with closing(sqlite3.connect(root / "live.sqlite3")) as db:
                db.execute("PRAGMA journal_mode=WAL")
                db.execute("CREATE TABLE example (name TEXT)")
                db.execute("INSERT INTO example VALUES ('Ghee')")
                db.commit()
                snapshot = backup.create_backup(
                    root / "live.sqlite3", media, root / "backups", writes_stopped=True
                )
                target = root / "restored"
                restore.restore_backup(snapshot, target)
                with closing(sqlite3.connect(target / "db.sqlite3")) as restored:
                    self.assertEqual(
                        restored.execute("SELECT name FROM example").fetchone(),
                        ("Ghee",),
                    )
                self.assertEqual(
                    (target / "media/photo.webp").read_bytes(), b"image bytes"
                )


if __name__ == "__main__":
    unittest.main()
