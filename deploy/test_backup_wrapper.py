"""Wrapper control-flow tests with fake Docker/rclone (no real deployment)."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


class WrapperTests(unittest.TestCase):
    def run_wrapper(self, failure=""):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            binary = root / "bin"
            binary.mkdir()
            log = root / "calls"
            fake = """#!/bin/bash
printf '%s %s\\n' "$(basename "$0")" "$*" >> "$CALL_LOG"
if [[ -n "$FAIL_MATCH" && "$*" == *"$FAIL_MATCH"* ]]; then exit 42; fi
"""
            for name in ["docker", "rclone"]:
                exe = binary / name
                exe.write_text(fake)
                exe.chmod(0o755)
            env = {
                **os.environ,
                "PATH": str(binary) + ":" + os.environ["PATH"],
                "BACKUP_DEST": str(root),
                "OFFSERVER_DEST": "test:remote",
                "CALL_LOG": str(log),
                "FAIL_MATCH": failure,
            }
            result = subprocess.run(
                ["bash", str(Path(__file__).with_name("backup.sh"))],
                env=env,
                capture_output=True,
                text=True,
            )
            return result.returncode, log.read_text().splitlines()

    def test_stop_failure_still_restarts(self):
        code, calls = self.run_wrapper("stop -t")
        self.assertEqual(code, 42)
        self.assertEqual(calls[-1], "docker compose start app")
        self.assertEqual(len(calls), 2)

    def test_backup_failure_restarts_without_transfer(self):
        code, calls = self.run_wrapper("backup_site")
        self.assertEqual(code, 42)
        self.assertEqual(calls[-1], "docker compose start app")
        self.assertFalse(any(call.startswith("rclone") for call in calls))

    def test_success_restarts_before_copy_and_checks_remote(self):
        code, calls = self.run_wrapper()
        self.assertEqual(code, 0)
        self.assertEqual(calls[2], "docker compose start app")
        self.assertTrue(calls[3].startswith("rclone copy "))
        self.assertTrue(calls[4].startswith("rclone check "))

    def test_transfer_filters_only_backup_root_hidden_entries(self):
        code, calls = self.run_wrapper()
        self.assertEqual(code, 0)
        for call in calls[3:]:
            self.assertIn("--exclude /.backup.lock", call)
            self.assertIn("--exclude /.snapshot-*/**", call)
            self.assertNotIn("--exclude .*", call)


if __name__ == "__main__":
    unittest.main()
