"""Read-only checks of saved friendships after restarting the app."""

import os
from pathlib import Path

import requests

from verify_live_chat import BASE, csrf


def main():
    values = dict(
        line.split(": ", 1)
        for line in Path(os.environ["DEMO_ACCESS_FILE"]).read_text(encoding="utf-8").splitlines()
        if ": " in line
    )
    for own, friend in (("A", "B"), ("B", "A")):
        with requests.Session() as client:
            result = client.post(BASE + "/login", data={
                "identifier": values[f"Tai khoan {own}"],
                "password": values["Mat khau chung"],
                "csrf_token": csrf(client, "/login"),
            }, allow_redirects=False, timeout=10)
            assert result.status_code == 302
            page = client.get(BASE + "/friends", timeout=10)
            page.raise_for_status()
            assert f'data-friend-user="{values[f"ID {friend}"]}"' in page.text
            requests_page = client.get(BASE + "/friends?view=requests", timeout=10)
            requests_page.raise_for_status()
            if own == "A":
                assert f'action="/friends/{values["ID C"]}/accept"' in requests_page.text
    print("[OK] Sau restart: A/B van la ban, loi moi C gui A van cho chap nhan")
    print("FRIENDS33B_PERSISTENCE_OK")


if __name__ == "__main__":
    main()
