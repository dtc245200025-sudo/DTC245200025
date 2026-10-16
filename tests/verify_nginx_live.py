"""Exercise group/DM WebSockets, polling and 10 MiB uploads through Nginx."""
import hashlib
import json
import os
from pathlib import Path
import queue
import secrets
import time

import requests
import socketio

from verify_live_chat import BASE, csrf
from verify_notifications_live import login


def wait(inbox, event_name, message_id):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        event, body = inbox.get(timeout=max(.1, deadline - time.monotonic()))
        if event == event_name and body.get("id", body.get("message_id")) == message_id:
            return body
    raise AssertionError("Expected proxy event not received")


def main():
    health = requests.get(BASE + "/healthz", timeout=10)
    assert health.status_code == 200 and health.json()["status"] == "ok"
    assert health.headers["Server"] == "nginx"
    for header in ("X-Frame-Options", "X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy"):
        assert health.headers[header]
    for path in ("/metrics", "/nginx_status"):
        assert requests.get(BASE + path, timeout=10).status_code == 404
    print("[OK] Nginx HTTP 200, 4 security headers, metrics/status khong cong khai")
    if os.environ.get("CHECK_RATE_LIMIT_ONLY") == "1":
        codes = [requests.post(BASE + "/login", data={}, timeout=10).status_code for _ in range(18)]
        assert 429 in codes and requests.get(BASE + "/login", timeout=10).status_code == 200
        print("NGINX4_RATE_LIMIT_OK: POST qua tan suat tra 429, GET form van 200")
        return
    values = dict(line.split(": ", 1) for line in Path(os.environ["DEMO_ACCESS_FILE"]).read_text(encoding="utf-8").splitlines() if ": " in line)
    clients = [login(values, letter) for letter in ("A", "B", "C")]
    sockets = []; inboxes = [queue.Queue() for _ in clients]; evidence = {}
    try:
        for client, inbox in zip(clients, inboxes):
            sock = socketio.Client(http_session=client, reconnection=False)
            for event in ("new_message", "direct_message", "message_notification"):
                sock.on(event, lambda data, name=event, target=inbox: target.put((name, data)))
            sock.connect(BASE, transports=["websocket"], wait_timeout=10)
            assert sock.transport() == "websocket"
            sockets.append(sock)
        for scope, path in (("room", values["Phong nhom"]), ("direct", values["Chat rieng"])):
            target_id = int(path.rsplit("/", 1)[1])
            field, join, event, send_event = ("room_id", "join", "new_message", "send_message") if scope == "room" else ("conversation_id", "direct_join", "direct_message", "direct_send")
            target = {field: target_id}
            for sock in sockets[:2]: assert sock.call(join, target, timeout=10)["ok"]
            assert not sockets[2].call(join, target, timeout=10)["ok"]
            for sender in (0, 1):
                body = {**target, "client_nonce": secrets.token_hex(16), "content": f"[GD4] {'A' if sender == 0 else 'B'} chat realtime qua Nginx 🌸"}
                sent = sockets[sender].call(send_event, body, timeout=10); assert sent["ok"]
                message_id = sent["message"]["id"]
                for inbox in inboxes[:2]: assert wait(inbox, event, message_id)["content"] == body["content"]
                other = 1 - sender
                assert wait(inboxes[other], "message_notification", message_id)["url"] == path
                receipt = {"scope": scope, "target_id": target_id, "message_ids": [message_id], "kind": "seen"}
                assert sockets[other].call("message_receipt", receipt, timeout=10)["ok"]
                assert sockets[sender].call(send_event, body, timeout=10)["message"]["id"] == message_id
            # This is the exact file boundary, not just a small sample upload.
            raw = b"N" * (10 * 1024 * 1024)
            upload = clients[0].post(BASE + f"/chat/{scope}/{target_id}/attachments", data={
                "content": "[GD4] Tệp đúng giới hạn 10 MiB qua Nginx", "client_nonce": secrets.token_hex(16),
                "csrf_token": csrf(clients[0], "/profile")}, files={"file": ("gd4-limit-10mib.bin", raw)}, timeout=60)
            assert upload.status_code == 201, upload.status_code
            message = upload.json()["message"]
            assert message["attachment"]["size"] == len(raw)
            wait(inboxes[1], "message_notification", message["id"])
            download = clients[1].get(BASE + message["attachment"]["download_url"], timeout=30)
            digest = hashlib.sha256(raw).hexdigest()
            assert download.status_code == 200 and hashlib.sha256(download.content).hexdigest() == digest
            assert clients[2].get(BASE + message["attachment"]["download_url"], timeout=10).status_code == 404
            large = clients[0].post(BASE + f"/chat/{scope}/{target_id}/attachments", data={
                "client_nonce": secrets.token_hex(16), "csrf_token": csrf(clients[0], "/profile")},
                files={"file": ("over-limit.bin", raw + b"x")}, timeout=60)
            assert large.status_code == 413
            evidence[scope] = {"download_url": message["attachment"]["download_url"], "sha256": digest}
            print(f"[OK] {scope}: WebSocket 2 chieu, thong bao, seen, chan nguoi ngoai; tep 10 MiB dung byte, 10 MiB+1 bi chan")
        poll = socketio.Client(http_session=clients[0], reconnection=False)
        try:
            poll.connect(BASE, transports=["polling"], wait_timeout=10)
            assert poll.transport() == "polling"
            target_id = int(values["Chat rieng"].rsplit("/", 1)[1])
            sent = poll.call("direct_send", {"conversation_id": target_id, "client_nonce": secrets.token_hex(16),
                "content": "[GD4] Socket.IO polling fallback qua Nginx"}, timeout=10)
            assert sent["ok"]
            assert wait(inboxes[1], "direct_message", sent["message"]["id"])
        finally:
            if poll.connected: poll.disconnect()
        assert inboxes[2].empty()
        print("[OK] Socket.IO HTTP polling fallback van gui/nhan duoc")
        oversized = requests.post(BASE + "/register", data=b"x" * (11 * 1024 * 1024 + 1), timeout=30)
        assert oversized.status_code == 413 and oversized.headers["Server"] == "nginx"
        print("[OK] Nginx chan request body vuot 11 MiB truoc khi toi Flask")
        Path(os.environ["NGINX_EVIDENCE"]).write_text(json.dumps(evidence), encoding="utf-8")
        if os.environ.get("CHECK_RATE_LIMIT") == "1":
            codes = [requests.post(BASE + "/login", data={}, timeout=10).status_code for _ in range(18)]
            assert 429 in codes and requests.get(BASE + "/login", timeout=10).status_code == 200
            print("[OK] POST /login vuot tan suat tra 429, GET form van 200")
        print("NGINX4_LIVE_CHECK_OK")
    finally:
        for sock in sockets:
            if sock.connected: sock.disconnect()
        for client in clients: client.close()


if __name__ == "__main__": main()
