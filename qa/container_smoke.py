"""Exercise production image locally, with an isolated disposable Docker volume.
No Compose services/public ports, domain registration or external storage is used.
Run after docker build -t ktnaturals:local-verification .
"""

import json
import secrets
import subprocess
import time
import urllib.request
import uuid
from pathlib import Path


def docker(*args):
    result = subprocess.run(
        ["docker", *args], text=True, capture_output=True, check=True
    )
    return result.stdout.strip()


def main():
    image = "ktnaturals:local-verification"
    name = "ktnaturals-qa-" + uuid.uuid4().hex[:10]
    volume = name + "-data"
    env = {
        "DJANGO_DEBUG": "false",
        "DJANGO_SECRET_KEY": secrets.token_urlsafe(60),
        "DJANGO_ALLOWED_HOSTS": "127.0.0.1,localhost",
        "SITE_URL": "https://ktnaturals.invalid",
        "DATABASE_PATH": "/state/data/db.sqlite3",
        "MEDIA_ROOT": "/state/media",
        "STATIC_ROOT": "/state/staticfiles",
    }
    flags = [item for key, value in env.items() for item in ("-e", key + "=" + value)]
    shared = [*flags, "-v", volume + ":/state"]
    results = {}
    docker("volume", "create", volume)
    try:
        docker(
            "run",
            "--rm",
            "--user",
            "0",
            "-v",
            volume + ":/state",
            image,
            "python",
            "-c",
            "import os; from pathlib import Path; [(p.mkdir(exist_ok=True), os.chown(p,10001,10001)) for p in [Path('/state'),Path('/state/data'),Path('/state/media'),Path('/state/staticfiles')]]",
        )
        results["migrate"] = docker(
            "run", "--rm", *shared, image, "python", "manage.py", "migrate", "--noinput"
        )
        results["collectstatic"] = docker(
            "run",
            "--rm",
            *shared,
            image,
            "python",
            "manage.py",
            "collectstatic",
            "--noinput",
        )
        docker(
            "run",
            "--rm",
            *shared,
            image,
            "python",
            "manage.py",
            "shell",
            "-c",
            "from catalogue.models import Category; from PIL import Image; Category.objects.create(name='QA persistent category',slug='qa-persistent'); Image.new('RGB',(20,20),'green').save('/state/media/qa.png')",
        )
        docker(
            "run",
            "-d",
            "--name",
            name,
            "--read-only",
            "--tmpfs",
            "/tmp",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges:true",
            "-p",
            "127.0.0.1::8000",
            *shared,
            image,
        )
        port = json.loads(docker("inspect", name))[0]["NetworkSettings"]["Ports"][
            "8000/tcp"
        ][0]["HostPort"]
        url = "http://127.0.0.1:" + port
        for attempt in range(30):
            try:
                request = urllib.request.Request(
                    url, headers={"X-Forwarded-Proto": "https"}
                )
                with urllib.request.urlopen(request, timeout=2) as response:
                    assert response.status == 200
                    assert "KT Naturals" in response.read().decode()
                break
            except (OSError, AssertionError):
                if attempt == 29:
                    raise
                time.sleep(0.25)
        results["gunicorn_home_status"] = 200
        docker("restart", name)
        result = docker(
            "exec",
            name,
            "python",
            "manage.py",
            "shell",
            "-c",
            "from catalogue.models import Category; assert Category.objects.filter(slug='qa-persistent').exists(); print('Persistence verified')",
        )
        assert "Persistence verified" in result
        results["restart_persistence"] = True
        docker("stop", name)
        snapshot = docker(
            "run",
            "--rm",
            *shared,
            image,
            "python",
            "manage.py",
            "backup_site",
            "--destination",
            "/state/backups",
            "--writes-stopped",
        ).splitlines()[-1]
        docker(
            "run",
            "--rm",
            *shared,
            image,
            "python",
            "manage.py",
            "restore_site",
            snapshot,
            "--target",
            "/state/restored",
        )
        checked = docker(
            "run",
            "--rm",
            *shared,
            image,
            "python",
            "-c",
            "import sqlite3,hashlib; from pathlib import Path; db=sqlite3.connect('/state/restored/db.sqlite3'); assert db.execute(\"select count(*) from catalogue_category where slug='qa-persistent'\").fetchone()[0]==1; assert Path('/state/media/qa.png').read_bytes()==Path('/state/restored/media/qa.png').read_bytes(); print('Restored database and image verified')",
        )
        assert "Restored database and image verified" in checked
        results["container_backup_restore"] = True
        target = Path("qa/evidence/container.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(results, indent=2))
        print(json.dumps(results, indent=2))
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
        docker("volume", "rm", volume)


if __name__ == "__main__":
    main()
