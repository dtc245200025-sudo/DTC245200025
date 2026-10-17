"""Generate real chat/upload activity and observe Prometheus changes, no secrets printed."""
from io import BytesIO
import json
import os
from pathlib import Path
import secrets
import time

import socketio

from verify_live_chat import BASE, csrf
from verify_notifications_live import login
from verify_monitoring import query


def wait_for(predicate, description):
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if predicate(): return
        time.sleep(3)
    raise AssertionError(description)


def total(expression):
    rows = query(expression)
    return float(rows[0]["value"][1]) if rows else 0


def main():
    values = dict(line.split(": ", 1) for line in Path(os.environ["DEMO_ACCESS_FILE"]).read_text(encoding="utf-8").splitlines() if ": " in line)
    clients = [login(values, letter) for letter in ("A", "B")]
    before_messages = total("sum(chat_messages_total) + sum(chat_direct_messages_total)")
    before_uploads = total("sum(chat_uploads_total)")
    before_http = total("sum(chat_http_requests_total)")
    sockets = []
    try:
        for client in clients:
            sock = socketio.Client(http_session=client, reconnection=False)
            sock.connect(BASE, transports=["websocket"], wait_timeout=10)
            sockets.append(sock)
        for scope, path in (("room", values["Phong nhom"]), ("direct", values["Chat rieng"])):
            target_id = int(path.rsplit("/", 1)[1])
            for sender in (0, 1):
                result = sockets[sender].call("send_message" if scope == "room" else "direct_send", {
                    "room_id" if scope == "room" else "conversation_id": target_id,
                    "client_nonce": secrets.token_hex(16), "content": f"[GD5] Kiểm thử metrics {scope} qua Nginx"}, timeout=10)
                assert result["ok"]
                assert sockets[1 - sender].call("message_receipt", {"scope": scope, "target_id": target_id,
                    "message_ids": [result["message"]["id"]], "kind": "seen"}, timeout=10)["ok"]
            uploaded = clients[0].post(BASE + f"/chat/{scope}/{target_id}/attachments", data={"csrf_token": csrf(clients[0], "/profile"),
                "content": "[GD5] Tệp kiểm thử bộ đếm upload", "client_nonce": secrets.token_hex(16)},
                files={"file": ("gd5-metrics.txt", BytesIO(b"LinhChat monitoring evidence\n"))}, timeout=15)
            assert uploaded.status_code == 201
        for _ in range(20):
            assert clients[0].get(BASE + "/healthz", timeout=10).status_code == 200
        wait_for(lambda: total("chat_socket_connections") >= 2, "Socket gauge did not reflect real connections")
        wait_for(lambda: total("sum(chat_messages_total) + sum(chat_direct_messages_total)") >= before_messages + 6, "Messages did not increase after actual chat")
        wait_for(lambda: total("sum(chat_uploads_total)") >= before_uploads + 2, "Uploads did not increase after actual files")
        wait_for(lambda: total("sum(chat_http_requests_total)") >= before_http + 20, "HTTP count did not increase")
        assert total("chat_upload_bytes_total") >= 2 * len(b"LinhChat monitoring evidence\n")
        assert total('chat_receipt_updates_total{kind="seen"}') >= 4
        print("MONITORING_ACTIVITY_OK: WebSocket that, 6 tin/2 tep, receipt va HTTP tang trong Prometheus")
    finally:
        for sock in sockets:
            if sock.connected: sock.disconnect()
        for client in clients: client.close()


if __name__ == "__main__": main()
