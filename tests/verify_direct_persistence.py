"""Read-only checks of the saved direct-chat demo after restarting the app."""

import os
from pathlib import Path

import requests

from verify_live_chat import BASE, csrf


def main():
    values = dict(line.split(": ", 1) for line in Path(os.environ["DEMO_ACCESS_FILE"]).read_text(encoding="utf-8").splitlines() if ": " in line)
    for letter in ("A", "B", "C"):
        with requests.Session() as client:
            result = client.post(BASE + "/login", data={"identifier": values[f"Tai khoan {letter}"], "password": values["Mat khau chung"], "csrf_token": csrf(client, "/login")}, allow_redirects=False, timeout=10)
            assert result.status_code == 302
            result = client.get(BASE + values["Chat rieng"] + "/history", timeout=10)
            if letter == "C":
                assert result.status_code == 404
            else:
                assert result.status_code == 200
                contents = [item["content"] for item in result.json()["messages"]]
                for marker in ("A gui tin rieng realtime", "B gui tin rieng realtime", "Tin luu khi B offline"):
                    assert any(marker in content for content in contents)
    print("[OK] Sau restart: A/B con lich su chat rieng, C van khong duoc truy cap")
    print("DIRECT34A_PERSISTENCE_OK")


if __name__ == "__main__": main()
