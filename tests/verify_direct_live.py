"""Actual PostgreSQL/WebSocket check of private chat, retries and typing."""

from concurrent.futures import ThreadPoolExecutor
import os
import queue
import re
import secrets
import time

import socketio

from verify_live_chat import BASE, account, csrf
from verify_friends_live import post, drain


def wait_event(inbox, predicate):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        event = inbox.get(timeout=max(.1, deadline - time.monotonic()))
        if predicate(event):
            return event
    raise AssertionError("Expected realtime event not received")


def main():
    tag = secrets.token_hex(3)
    names = [f"direct34_{letter}_{tag}" for letter in ("a", "b", "c")]
    password = secrets.token_urlsafe(24)
    clients = [account(name, password) for name in names]
    alice, bob, carol = clients
    ids = [int(re.search(r'data-presence-user="(\d+)"', client.get(BASE + "/profile", timeout=10).text).group(1)) for client in clients]
    a_id, b_id, c_id = ids
    for client, label in zip(clients, ("Linh", "Minh Anh", "Người kiểm thử")):
        assert post(client, "/profile", {"display_name": label, "bio": "", "profile_public": "on"}).status_code == 302
    assert post(alice, f"/friends/{b_id}/request").status_code == 302
    assert post(bob, f"/friends/{a_id}/accept").status_code == 302
    tokens = [csrf(client, "/profile") for client in (alice, bob)]
    def open_chat(item):
        client, other_id, token = item
        return client.post(BASE + f"/direct/start/{other_id}", data={"csrf_token": token}, allow_redirects=False, timeout=15)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(open_chat, ((alice, b_id, tokens[0]), (bob, a_id, tokens[1]))))
    assert all(result.status_code == 302 for result in results)
    paths = [result.headers["Location"] for result in results]
    assert paths[0] == paths[1]
    path = paths[0]
    conversation_id = int(path.rsplit("/", 1)[1])
    assert carol.get(BASE + path, timeout=10).status_code == 404
    assert carol.get(BASE + path + "/history", timeout=10).status_code == 404
    assert post(carol, f"/direct/start/{a_id}").status_code == 403
    print("[OK] Hai phia tao dong thoi chi mot cuoc tro chuyen; nguoi thu ba bi chan HTTP")

    sockets = []
    inboxes = [queue.Queue() for _ in clients]
    try:
        for client, inbox in zip(clients, inboxes):
            sock = socketio.Client(http_session=client, reconnection=False)
            for event_name in ("direct_message", "direct_changed", "typing"):
                sock.on(event_name, lambda data, kind=event_name, output=inbox: output.put((kind, data)))
            sock.connect(BASE, transports=["websocket"], wait_timeout=10)
            sockets.append(sock)
        for sock in sockets[:2]:
            assert sock.call("direct_join", {"conversation_id": conversation_id}, timeout=10)["ok"]
        assert not sockets[2].call("direct_join", {"conversation_id": conversation_id}, timeout=10)["ok"]
        typing = {"scope": "direct", "target_id": conversation_id, "typing": True}
        assert sockets[0].call("typing", typing, timeout=10)["ok"]
        event = wait_event(inboxes[1], lambda event: event[0] == "typing" and event[1]["typing"])
        assert event[1]["user_id"] == a_id and "content" not in event[1]
        assert sockets[0].call("typing", {**typing, "typing": False}, timeout=10)["ok"]
        wait_event(inboxes[1], lambda event: event[0] == "typing" and not event[1]["typing"])
        print("[OK] Dang nhap bat/tat qua WebSocket that; khong truyen noi dung ban nhap")

        for index, (sock, sender) in enumerate(zip(sockets[:2], ("A", "B"))):
            body = {"conversation_id": conversation_id, "content": f"[GD3.4a {tag}] {sender} gui tin rieng realtime", "client_nonce": secrets.token_hex(16)}
            result = sock.call("direct_send", body, timeout=10)
            assert result["ok"]
            message_id = result["message"]["id"]
            for inbox in inboxes[:2]:
                wait_event(inbox, lambda event: event[0] == "direct_message" and event[1]["id"] == message_id)
            assert sock.call("direct_send", body, timeout=10) == result
        history = alice.get(BASE + path + "/history", timeout=10).json()
        assert len(history["messages"]) == 2 and history["can_send"]
        assert not sockets[2].call("direct_send", {**body, "client_nonce": secrets.token_hex(16)}, timeout=10)["ok"]
        assert not sockets[2].call("typing", typing, timeout=10)["ok"]
        assert "gui tin rieng realtime" not in carol.get(BASE + "/direct/panel", timeout=10).text
        try:
            inboxes[2].get(timeout=.5)
            raise AssertionError("Unrelated user received private events")
        except queue.Empty:
            pass
        print("[OK] Hai chieu chi hai tai khoan nhan; gui lai cung ma khong tao tin trung")

        sockets[1].disconnect()
        offline_body = {"conversation_id": conversation_id, "content": f"[GD3.4a {tag}] Tin luu khi B offline", "client_nonce": secrets.token_hex(16)}
        assert sockets[0].call("direct_send", offline_body, timeout=10)["ok"]
        assert len(bob.get(BASE + path + "/history", timeout=10).json()["messages"]) == 3
        sockets[1].connect(BASE, transports=["websocket"], wait_timeout=10)
        assert sockets[1].call("direct_join", {"conversation_id": conversation_id}, timeout=10)["ok"]
        print("[OK] Tin khi B offline luu PostgreSQL; dang nhap/ket noi lai xem duoc lich su")

        room_result = post(alice, "/rooms/create", {"name": f"GD3.4a Typing {tag}", "max_members": "10"})
        assert room_result.status_code == 302
        room_path = room_result.headers["Location"]
        room_id = int(room_path.rsplit("/", 1)[1])
        assert post(bob, room_path + "/join").status_code == 302
        for sock in sockets[:2]:
            assert sock.call("join", {"room_id": room_id}, timeout=10)["ok"]
        drain(inboxes[1])
        assert sockets[0].call("typing", {"scope": "room", "target_id": room_id, "typing": True}, timeout=10)["ok"]
        wait_event(inboxes[1], lambda event: event[0] == "typing" and event[1]["scope"] == "room" and event[1]["typing"])
        assert sockets[0].call("typing", {"scope": "room", "target_id": room_id, "typing": False}, timeout=10)["ok"]
        assert not sockets[2].call("typing", {"scope": "room", "target_id": room_id, "typing": True}, timeout=10)["ok"]
        print("[OK] Dang nhap trong phong nhom dung quyen, tach khoi chat rieng")

        evidence_path = os.environ.get("DEMO_ACCESS_FILE")
        if evidence_path:
            descriptor = os.open(evidence_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write("GD3.4a - Chi xem rieng tren VM, khong chup mat khau.\n")
                for letter, name in zip(("A", "B", "C"), names):
                    stream.write(f"Tai khoan {letter}: {name}\n")
                stream.write(f"Mat khau chung: {password}\nChat rieng: {path}\nPhong nhom: {room_path}\n")
                stream.write("A va B da la ban, co lich su chat rieng. C khong duoc truy cap chat rieng A/B.\n")
            print("[OK] Luu tai khoan minh chung rieng tren VM, quyen 600")
        print("DIRECT34A_LIVE_CHECK_OK")
    finally:
        for sock in sockets:
            if sock.connected: sock.disconnect()
        for client in clients: client.close()


if __name__ == "__main__":
    main()
