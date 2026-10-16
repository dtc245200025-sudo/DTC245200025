"""HTTP + real WebSocket checks against the running app; no passwords printed."""

import os
import queue
import re
import secrets

import requests
import socketio


BASE = os.environ.get("BASE_URL", "http://app:5000").rstrip("/")


def csrf(client, path):
    response = client.get(BASE + path, timeout=10)
    response.raise_for_status()
    return re.search(r'name="csrf_token" value="([^"]+)"', response.text).group(1)


def account(username, password):
    client = requests.Session()
    token = csrf(client, "/register")
    response = client.post(BASE + "/register", data={
        "username": username, "email": f"{username}@example.com", "password": password, "csrf_token": token,
    }, allow_redirects=False, timeout=10)
    assert response.status_code == 302, "Register failed"
    token = csrf(client, "/login")
    response = client.post(BASE + "/login", data={
        "username": username, "password": password, "csrf_token": token,
    }, allow_redirects=False, timeout=10)
    assert response.status_code == 302, "Login failed"
    return client


def main():
    suffix = secrets.token_hex(4)
    password = secrets.token_urlsafe(24)
    alice = account(f"probe_alice_{suffix}", password)
    bob = account(f"probe_bob_{suffix}", password)
    print("[OK] Dang ky va dang nhap hai user qua HTTP")
    response = alice.post(BASE + "/", data={
        "name": f"Kiem thu GD3 {suffix}", "csrf_token": csrf(alice, "/"),
    }, allow_redirects=False, timeout=10)
    assert response.status_code == 302, "Create room failed"
    room_path = response.headers["Location"]
    room_id = int(room_path.rsplit("/", 1)[1])
    for client in (alice, bob):
        assert client.post(BASE + room_path + "/join", data={"csrf_token": csrf(client, room_path)}, allow_redirects=False, timeout=10).status_code == 302
        client.get(BASE + room_path, timeout=10).raise_for_status()
    print("[OK] Hai user tham gia cung phong")

    sockets = []
    inboxes = [queue.Queue(), queue.Queue()]
    try:
        for http_session, inbox in zip((alice, bob), inboxes):
            sock = socketio.Client(http_session=http_session, reconnection=False, request_timeout=10)
            sock.on("new_message", inbox.put)
            sockets.append(sock)
            sock.connect(BASE, transports=["websocket"], wait_timeout=10)
            assert sock.transport() == "websocket"
            assert sock.call("join", {"room_id": room_id}, timeout=10)["ok"]
        print("[OK] Hai ket noi WebSocket that (khong dung polling)")

        contents = [f"[GD3 {suffix}] Alice gui tin realtime", f"[GD3 {suffix}] Bob tra loi realtime"]
        for sender, content in zip(sockets, contents):
            result = sender.call("send_message", {"room_id": room_id, "content": content}, timeout=10)
            assert result["ok"], "Message not acknowledged"
            for inbox in inboxes:
                received = inbox.get(timeout=10)
                assert received["content"] == content
                assert received["id"] == result["id"]
        print("[OK] Gui va nhan tin hai chieu; server xac nhan da luu")

        for client in (alice, bob):
            history = client.get(BASE + room_path, timeout=10)
            history.raise_for_status()
            assert all(content in history.text for content in contents)
        print("[OK] Tai lai trang van co lich su tin nhan")
        print(f"ROOM_VERIFIED={room_id}")
        access_path = os.environ.get("DEMO_ACCESS_FILE")
        if access_path:
            descriptor = os.open(access_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(
                    f"Tai khoan A: probe_alice_{suffix}\n"
                    f"Tai khoan B: probe_bob_{suffix}\n"
                    f"Mat khau chung cua hai tai khoan demo: {password}\n"
                    f"Phong: Kiem thu GD3 {suffix}\n"
                    f"Duong dan phong: {room_path}\n"
                    "Chi xem mat khau tren VM, khong chup anh hoac gui noi dung file.\n"
                )
            print("[OK] Da luu tai khoan demo vao file rieng tren VM, khong in mat khau")
        print("LIVE_CHAT_CHECK_OK")
    finally:
        for sock in sockets:
            if sock.connected:
                sock.disconnect()
        alice.close()
        bob.close()


if __name__ == "__main__":
    main()
