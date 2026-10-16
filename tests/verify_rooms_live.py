"""Exercise actual PostgreSQL capacity locking and HTTP/WebSocket room access."""

from concurrent.futures import ThreadPoolExecutor
import os
import queue
import re
import secrets

import socketio

from verify_live_chat import BASE, account, csrf


def post(client, path, data=None, source="/rooms/create"):
    return client.post(BASE + path, data={**(data or {}), "csrf_token": csrf(client, source)},
                       allow_redirects=False, timeout=15)


def create(client, name, mode):
    result = post(client, "/rooms/create", {"name": name, "visibility": "public" if mode == "open" else "private",
                                            "join_mode": mode, "max_members": "2", "room_password": "room-test-32-only"})
    assert result.status_code == 302
    match = re.search(r"/rooms/(\d+)", result.headers["Location"])
    assert match
    return int(match.group(1))


def invitation(client, room_id):
    result = post(client, f"/rooms/{room_id}/invitation")
    assert result.status_code == 200
    return re.search(r'id="invitation-url"[^>]+value="([^"]+)"', result.text).group(1).split("#", 1)[1]


def main():
    tag = secrets.token_hex(3)
    password = secrets.token_urlsafe(24)
    names = [f"rooms32_{label}_{tag}" for label in ("a", "b", "c")]
    clients = [account(name, password) for name in names]
    alice, bob, carol = clients
    sockets = []
    public_id = create(alice, f"GD3.2 Public 2 nguoi {tag}", "open")
    try:
        assert 'id="messages"' not in bob.get(BASE + f"/rooms/{public_id}", timeout=10).text
        tokens = [csrf(client, "/rooms/create") for client in (bob, carol)]
        def race(item):
            client, token = item
            return client.post(BASE + f"/rooms/{public_id}/join", data={"csrf_token": token}, allow_redirects=False, timeout=15).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(race, zip((bob, carol), tokens)))
        assert sorted(results) == [302, 409], "Capacity race admitted too many members"
        print("[OK] PostgreSQL: hai nguoi cung tranh cho cuoi, chi mot nguoi vao duoc; Public khong vuot 2 nguoi")

        password_id = create(alice, f"GD3.2 Private mat khau {tag}", "password")
        a_socket = socketio.Client(http_session=alice, reconnection=False)
        b_socket = socketio.Client(http_session=bob, reconnection=False)
        for sock in (a_socket, b_socket):
            sockets.append(sock)
            sock.connect(BASE, transports=["websocket"], wait_timeout=10)
        inbox = queue.Queue()
        b_socket.on("new_message", inbox.put)
        assert a_socket.call("join", {"room_id": password_id})["ok"]
        marker = f"Private history {tag}"
        assert a_socket.call("send_message", {"room_id": password_id, "content": marker})["ok"]
        gate = bob.get(BASE + f"/rooms/{password_id}", timeout=10)
        assert gate.status_code == 403 and marker not in gate.text
        assert not b_socket.call("join", {"room_id": password_id})["ok"]
        assert not b_socket.call("send_message", {"room_id": password_id, "content": "blocked"})["ok"]
        assert post(bob, f"/rooms/{password_id}/join", {"room_password": "wrong"}).status_code == 403
        assert post(bob, f"/rooms/{password_id}/join", {"room_password": "room-test-32-only"}).status_code == 302
        assert marker in bob.get(BASE + f"/rooms/{password_id}", timeout=10).text
        assert b_socket.call("join", {"room_id": password_id})["ok"]
        assert a_socket.call("send_message", {"room_id": password_id, "content": "authorized only"})["ok"]
        assert inbox.get(timeout=5)["content"] == "authorized only"
        assert post(bob, f"/rooms/{password_id}/leave").status_code == 302
        assert not b_socket.call("join", {"room_id": password_id})["ok"]
        assert not b_socket.call("send_message", {"room_id": password_id, "content": "blocked again"})["ok"]
        assert a_socket.call("send_message", {"room_id": password_id, "content": "after leave"})["ok"]
        try:
            inbox.get(timeout=.7)
            raise AssertionError("Former member received a private message")
        except queue.Empty:
            pass
        print("[OK] Private mat khau: chan HTTP/Socket/history khi chua co quyen; roi phong khong con nhan tin")

        approval_id = create(alice, f"GD3.2 Private phe duyet {tag}", "approval")
        approval_events, pending_events = queue.Queue(), queue.Queue()
        b_socket.on("room_request_result", approval_events.put)
        a_socket.on("room_request_pending", pending_events.put)
        assert post(bob, f"/rooms/{approval_id}/join").status_code == 302
        assert pending_events.get(timeout=5)["room_id"] == approval_id
        assert not b_socket.call("join", {"room_id": approval_id})["ok"]
        manage_path = f"/rooms/{approval_id}/manage"
        management = alice.get(BASE + manage_path, timeout=10)
        decision = re.search(r'action="([^\"]+/approve)"', management.text).group(1)
        assert post(carol, decision).status_code == 403
        assert post(alice, decision).status_code == 302
        assert approval_events.get(timeout=5) == {"room_id": approval_id, "approved": True}
        assert b_socket.call("join", {"room_id": approval_id})["ok"]
        # Leave one pending request for the user's screenshot on the owner page.
        assert post(carol, f"/rooms/{approval_id}/join").status_code == 302
        print("[OK] Private phe duyet: chi chu phong duoc duyet; WebSocket thong bao quyen truy cap theo thoi gian thuc")

        invite_id = create(alice, f"GD3.2 Private link moi {tag}", "invite")
        old_token = invitation(alice, invite_id)
        assert f"GD3.2 Private link moi {tag}" not in bob.get(BASE + "/rooms/search", timeout=10).text
        assert bob.get(BASE + f"/rooms/{invite_id}", timeout=10).status_code == 404
        assert post(bob, "/rooms/invite", {"invite_token": old_token}, "/rooms/invite").status_code == 302
        new_token = invitation(alice, invite_id)
        assert post(carol, "/rooms/invite", {"invite_token": old_token}, "/rooms/invite").status_code == 403
        assert post(carol, "/rooms/invite", {"invite_token": new_token}, "/rooms/invite").status_code == 302
        assert 'id="messages"' in bob.get(BASE + f"/rooms/{invite_id}", timeout=10).text
        print("[OK] Private link moi: an tim kiem, link gia/da thay bi tu choi; thanh vien cu van giu quyen")

        evidence_file = os.environ.get("DEMO_ACCESS_FILE")
        if evidence_file:
            descriptor = os.open(evidence_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write("GD3.2 - Chi xem tren VM, khong chup mat khau/link moi.\n")
                stream.write("\n".join(f"Tai khoan {label}: {name}" for label, name in zip(("A (chu phong)", "B", "C (dang cho duyet)"), names)))
                stream.write(f"\nMat khau chung: {password}\n")
                stream.write(f"Public da day: /rooms/{public_id}\nPrivate mat khau: /rooms/{password_id}\n")
                stream.write(f"Mat khau phong thu: room-test-32-only\nPrivate cho duyet: /rooms/{approval_id}/manage\nPrivate link moi: /rooms/{invite_id}/manage\n")
            print("[OK] Luu tai khoan minh chung rieng tren VM, quyen 600; khong in mat khau/link moi")
        print("ROOMS32_LIVE_CHECK_OK")
    finally:
        for sock in sockets:
            if sock.connected:
                sock.disconnect()
        for client in clients:
            client.close()


if __name__ == "__main__":
    main()
