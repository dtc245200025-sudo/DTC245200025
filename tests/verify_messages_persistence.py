import hashlib
import os
from pathlib import Path

import requests

from verify_live_chat import BASE, csrf
from verify_notifications_live import login


def main():
    values=dict(line.split(": ",1) for line in Path(os.environ["DEMO_ACCESS_FILE"]).read_text(encoding="utf-8").splitlines() if ": " in line)
    for letter in ("A","B","C"):
        with login(values, letter) as client:
            for scope,key in (("room","Phong nhom"),("direct","Chat rieng")):
                target_id=int(values[key].rsplit("/",1)[1]); history=client.get(BASE+f"/chat/{scope}/{target_id}/history",timeout=10)
                downloaded=client.get(BASE+values[f"File {scope}"],timeout=10)
                if letter=="C":
                    assert history.status_code==404 and downloaded.status_code==404
                else:
                    assert history.status_code==200 and any("Xin chào 😊" in item["content"] for item in history.json()["messages"])
                    assert any(item["receipt_summary"]["seen"] for item in history.json()["messages"])
                    assert downloaded.status_code==200 and hashlib.sha256(downloaded.content).hexdigest()==values[f"SHA {scope}"]
    print("[OK] Sau restart: tin/emoji, trang thai nhan-xem va tep nguyen ven; C van bi chan")
    print("MESSAGES34B_PERSISTENCE_OK")


if __name__=="__main__": main()
