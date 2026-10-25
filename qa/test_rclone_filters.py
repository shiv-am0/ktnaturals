"""Optional real-rclone local-to-local transfer regression (Docker needed)."""

import os
from pathlib import Path
import subprocess
import tempfile


def main():
    with tempfile.TemporaryDirectory() as root:
        base = Path(root)
        source = base / "source"
        remote = base / "remote"
        for directory in (
            source / "snapshot-1" / "media",
            source / ".snapshot-incomplete" / "media",
            remote,
        ):
            directory.mkdir(parents=True)
        (source / ".backup.lock").write_text("lock")
        (source / "snapshot-1" / "db.sqlite3").write_text("db")
        (source / "snapshot-1" / "media" / ".hidden.webp").write_bytes(b"image")
        (source / ".snapshot-incomplete" / "media" / "incomplete.webp").write_bytes(
            b"partial"
        )
        flags = [
            "--exclude",
            "/.backup.lock",
            "--exclude",
            "/.snapshot-*/**",
            "--exclude",
            "/.snapshot-*",
        ]
        command = [
            "docker",
            "run",
            "--rm",
            "--user",
            f"{os.getuid()}:{os.getgid()}",
            "-v",
            f"{base}:/data",
            "rclone/rclone:1.70",
        ]
        subprocess.run(
            [*command, "copy", "/data/source", "/data/remote", *flags], check=True
        )
        assert (remote / "snapshot-1" / "db.sqlite3").read_text() == "db"
        assert (
            remote / "snapshot-1" / "media" / ".hidden.webp"
        ).read_bytes() == b"image"
        assert not (remote / ".backup.lock").exists()
        assert not (remote / ".snapshot-incomplete").exists()
        subprocess.run(
            [
                *command,
                "check",
                "/data/source",
                "/data/remote",
                *flags,
                "--one-way",
                "--download",
            ],
            check=True,
        )
        print(
            "Real rclone copied and verified hidden media; skipped only root lock and incomplete snapshot."
        )


if __name__ == "__main__":
    main()
