"""Verify persistent history using the private demo account file after app restart."""

import os
from pathlib import Path

import requests

from verify_live_chat import BASE, csrf


values = dict(
    line.split(": ", 1)
    for line in Path(os.environ["DEMO_ACCESS_FILE"]).read_text(encoding="utf-8").splitlines()
    if ": " in line
)
for field in ("Tai khoan A", "Tai khoan B"):
    with requests.Session() as client:
        response = client.post(BASE + "/login", data={
            "username": values[field],
            "password": values["Mat khau chung cua hai tai khoan demo"],
            "csrf_token": csrf(client, "/login"),
        }, allow_redirects=False, timeout=10)
        assert response.status_code == 302, "Login after restart failed"
        history = client.get(BASE + values["Duong dan phong"], timeout=10)
        history.raise_for_status()
        assert "Alice gui tin realtime" in history.text
        assert "Bob tra loi realtime" in history.text
print("[OK] Hai user dang nhap lai sau khi restart app")
print("[OK] Lich su tin nhan PostgreSQL van con")
print("PERSISTENCE_AFTER_RESTART_OK")
