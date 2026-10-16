"""Read-only checks of the saved GD3.2 demo after an app restart."""

import os
import re

import requests

from verify_live_chat import BASE, csrf


def main():
    with open(os.environ["DEMO_ACCESS_FILE"], encoding="utf-8") as stream:
        evidence = stream.read()
    user = re.search(r"Tai khoan A \(chu phong\): (.+)", evidence).group(1)
    password = re.search(r"Mat khau chung: (.+)", evidence).group(1)
    paths = re.findall(r"(?:Public da day|Private mat khau|Private cho duyet|Private link moi): (/rooms/[^\n]+)", evidence)
    assert len(paths) == 4
    with requests.Session() as client:
        result = client.post(BASE + "/login", data={"identifier": user, "password": password, "csrf_token": csrf(client, "/login")},
                             allow_redirects=False, timeout=10)
        assert result.status_code == 302
        pages = [client.get(BASE + path, timeout=10) for path in paths]
        assert all(page.status_code == 200 for page in pages)
        assert "2/2" in pages[0].text
        assert "Private history" in pages[1].text
        assert "Phê duyệt" in pages[2].text
        assert "Tạo link mới và vô hiệu link cũ" in pages[3].text
    print("[OK] Sau restart: Public day, lich su Private, yeu cau cho duyet va hash link moi van duoc luu")
    print("ROOMS32_PERSISTENCE_OK")


if __name__ == "__main__":
    main()
