"""Read-only verification of large files saved through the proxy."""
import hashlib
import json
import os
from pathlib import Path

from verify_live_chat import BASE
from verify_notifications_live import login


def main():
    values = dict(line.split(": ", 1) for line in Path(os.environ["DEMO_ACCESS_FILE"]).read_text(encoding="utf-8").splitlines() if ": " in line)
    evidence = json.loads(Path(os.environ["NGINX_EVIDENCE"]).read_text(encoding="utf-8"))
    for letter in ("A", "B", "C"):
        with login(values, letter) as client:
            for item in evidence.values():
                response = client.get(BASE + item["download_url"], timeout=30)
                if letter == "C": assert response.status_code == 404
                else: assert response.status_code == 200 and hashlib.sha256(response.content).hexdigest() == item["sha256"]
    print("NGINX4_PERSISTENCE_OK: tep 10 MiB qua proxy con nguyen sau recreate; C van bi chan")


if __name__ == "__main__": main()
