"""Real HTTP/WebSocket notification check using existing synthetic demo users."""
import json
import os
from pathlib import Path
import queue
import secrets
import time

import requests
import socketio

from verify_live_chat import BASE, csrf


def login(values, letter):
    client = requests.Session()
    for attempt in range(8):
        result = client.post(BASE + "/login", data={"identifier": values[f"Tai khoan {letter}"],
            "password": values["Mat khau chung"], "csrf_token": csrf(client, "/login")}, allow_redirects=False, timeout=10)
        if result.status_code == 302:
            return client
        if result.status_code != 429 or attempt == 7:
            raise AssertionError(f"Demo login failed: HTTP {result.status_code}")
        # Respect the proxy's real rate limit when suites share a test IP.
        print("[WAIT] Nginx login rate limit; retrying in 7 seconds", flush=True)
        time.sleep(7)
    raise AssertionError("Demo login retry budget exhausted")


def main():
    values = dict(line.split(": ", 1) for line in Path(os.environ["DEMO_ACCESS_FILE"]).read_text(encoding="utf-8").splitlines() if ": " in line)
    clients = [login(values, letter) for letter in ("A", "B", "C")]
    evidence_path = Path(os.environ.get("NOTIFICATION_EVIDENCE", "/tmp/notification-evidence.json"))
    if os.environ.get("PERSISTENCE_ONLY") == "1":
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        state = clients[1].get(BASE + "/notifications/state", timeout=10).json()
        for scope, item in evidence.items():
            assert state["rooms" if scope == "room" else "directs"][str(item["target_id"])] >= 1
            details = clients[1].get(BASE + f'/chat/{scope}/{item["target_id"]}/messages/{item["message_id"]}/details', timeout=10).json()
            assert details["receipts"][0]["seen_at"] is None
        print("NOTIFICATIONS_PERSISTENCE_OK: tin chua doc van con sau tao lai app")
        return
    sockets = []; inboxes = [queue.Queue() for _ in clients]; envelopes = [queue.Queue() for _ in clients]
    try:
        for client, inbox, envelope in zip(clients, inboxes, envelopes):
            sock = socketio.Client(http_session=client, reconnection=False)
            sock.on("message_notification", inbox.put)
            sock.on("new_message", envelope.put)
            sock.on("direct_message", envelope.put)
            sock.connect(BASE, transports=["websocket"], wait_timeout=10)
            sockets.append(sock)
        evidence = {}
        for scope, path in (("room", values["Phong nhom"]), ("direct", values["Chat rieng"])):
            target_id = int(path.rsplit("/", 1)[1])
            field, event, key = ("room_id", "send_message", "rooms") if scope == "room" else ("conversation_id", "direct_send", "directs")
            initial = clients[1].get(BASE + "/notifications/state", timeout=10).json()[key].get(str(target_id), 0)
            body = {field: target_id, "content": "Kiểm thử thông báo LinhChat 🌸", "client_nonce": secrets.token_hex(16)}
            result = sockets[0].call(event, body, timeout=10); assert result["ok"]
            message_id = result["message"]["id"]
            notice = inboxes[1].get(timeout=10)
            assert notice["scope"] == scope and notice["message_id"] == message_id and notice["url"] == path
            delivered = envelopes[1].get(timeout=10)
            assert delivered["id"] == message_id and delivered["content"] == body["content"]
            # Neither recipient joins the Socket.IO chat room: home-page delivery still works.
            assert clients[1].get(BASE + "/notifications/state", timeout=10).json()[key][str(target_id)] == initial + 1
            assert sockets[0].call(event, body, timeout=10)["message"]["id"] == message_id
            assert inboxes[0].empty() and inboxes[2].empty()
            assert envelopes[1].empty() and envelopes[2].empty()
            try:
                inboxes[1].get(timeout=.5)
                raise AssertionError("Duplicate notification")
            except queue.Empty: pass
            receipt = {"scope": scope, "target_id": target_id, "message_ids": [message_id], "kind": "delivered"}
            assert sockets[1].call("message_receipt", receipt, timeout=10)["ok"]
            assert clients[1].get(BASE + "/notifications/state", timeout=10).json()[key][str(target_id)] == initial + 1
            assert sockets[1].call("message_receipt", {**receipt, "kind": "seen"}, timeout=10)["ok"]
            assert clients[1].get(BASE + "/notifications/state", timeout=10).json()[key].get(str(target_id), 0) == initial
            sockets[1].disconnect()
            offline = sockets[0].call(event, {**body, "client_nonce": secrets.token_hex(16), "content": "Tin chưa đọc khi người nhận ngoại tuyến"}, timeout=10)
            assert offline["ok"]
            sockets[1].connect(BASE, transports=["websocket"], wait_timeout=10)
            assert clients[1].get(BASE + "/notifications/state", timeout=10).json()[key][str(target_id)] == initial + 1
            assert inboxes[1].empty()  # Reconnect restores badges without replaying popups.
            evidence[scope] = {"target_id": target_id, "message_id": offline["message"]["id"]}
            assert clients[2].get(BASE + "/notifications/state", timeout=10).json()["total"] == 0
            print(f"[OK] {scope}: thong bao ngoai trang chat, dung nguoi, chong trung, doc/nhan, offline/reconnect")
        evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
        print("NOTIFICATIONS_LIVE_OK")
    finally:
        for sock in sockets:
            if sock.connected: sock.disconnect()
        for client in clients: client.close()


if __name__ == "__main__": main()
