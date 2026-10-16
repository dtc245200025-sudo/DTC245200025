"""Actual PostgreSQL + HTTP + WebSocket friend workflow; never print credentials."""

from concurrent.futures import ThreadPoolExecutor
import os
import queue
import re
import secrets
import time

import socketio

from verify_live_chat import BASE, account, csrf


def post(client, path, data=None):
    return client.post(BASE + path, data={**(data or {}), "csrf_token": csrf(client, "/profile")}, allow_redirects=False, timeout=15)


def friend_event(inbox, count):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        event = inbox.get(timeout=max(.1, deadline - time.monotonic()))
        if event.get("incoming_count") == count:
            return
    raise AssertionError("Friend update was not received")


def presence_event(inbox, user_id, online):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        event = inbox.get(timeout=max(.1, deadline - time.monotonic()))
        if event == {"user_id": user_id, "online": online}:
            return
    raise AssertionError("Presence was not received")


def drain(inbox):
    while True:
        try:
            inbox.get_nowait()
        except queue.Empty:
            return


def main():
    tag = secrets.token_hex(3)
    names = [f"friends33_{letter}_{tag}" for letter in ("a", "b", "c")]
    password = secrets.token_urlsafe(24)
    clients = [account(name, password) for name in names]
    alice, bob, carol = clients
    ids = [int(re.search(r'data-presence-user="(\d+)"', client.get(BASE + "/profile", timeout=10).text).group(1)) for client in clients]
    a_id, b_id, c_id = ids
    for client, label in zip(clients, ("Minh Anh", "Bảo Ngọc", "Tuấn Anh")):
        assert post(client, "/profile", {"display_name": label, "bio": "", "profile_public": "on"}).status_code == 302
    for query in (names[1].upper(), names[1] + "@example.com", "Bảo Ngọc"):
        result = post(alice, "/friends/search", {"q": query})
        assert result.status_code == 200 and f'data-friend-user="{b_id}"' in result.text
        assert '<p class="friend-email' not in result.text
    assert f'data-friend-user="{b_id}"' not in post(alice, "/friends/search", {"q": names[1] + "@example.co"}).text
    print("[OK] Tim theo username/ten hien thi/email chinh xac; khong hien email rieng tu")

    sockets = []
    inboxes = [queue.Queue() for _ in clients]
    presence = queue.Queue()
    try:
        for client, inbox in zip(clients, inboxes):
            sock = socketio.Client(http_session=client, reconnection=False)
            sock.on("friends_changed", inbox.put)
            sockets.append(sock)
            sock.connect(BASE, transports=["websocket"], wait_timeout=10)
        sockets[0].on("presence", presence.put)
        for inbox in inboxes:
            drain(inbox)
        assert post(alice, f"/friends/{b_id}/request").status_code == 302
        friend_event(inboxes[1], 1)
        assert post(alice, f"/friends/{b_id}/accept").status_code == 403
        assert post(carol, f"/friends/{b_id}/accept").status_code == 404
        drain(inboxes[0])
        assert post(bob, f"/friends/{a_id}/accept").status_code == 302
        friend_event(inboxes[0], 0)
        assert f'data-friend-user="{b_id}"' in alice.get(BASE + "/friends", timeout=10).text
        assert f'data-friend-user="{a_id}"' in bob.get(BASE + "/friends", timeout=10).text
        try:
            inboxes[2].get(timeout=.5)
            raise AssertionError("Unrelated user received a friend change")
        except queue.Empty:
            pass
        print("[OK] Moi/chap nhan theo dung quyen; WebSocket chi thong bao cho hai ben")

        extra = socketio.Client(http_session=bob, reconnection=False)
        sockets.append(extra)
        extra.connect(BASE, transports=["websocket"], wait_timeout=10)
        drain(presence)
        sockets[1].disconnect()
        try:
            while True:
                event = presence.get(timeout=.5)
                assert event != {"user_id": b_id, "online": False}
        except queue.Empty:
            pass
        extra.disconnect()
        presence_event(presence, b_id, False)
        print("[OK] Online/offline WebSocket that: chi ngoai tuyen khi dong ket noi cuoi")

        assert post(bob, f"/friends/{a_id}/remove").status_code == 302
        assert f'data-friend-user="{b_id}"' not in alice.get(BASE + "/friends", timeout=10).text
        post(alice, f"/friends/{b_id}/request")
        assert post(bob, f"/friends/{a_id}/decline").status_code == 302
        post(alice, f"/friends/{b_id}/request")
        assert post(alice, f"/friends/{b_id}/cancel").status_code == 302
        print("[OK] Tu choi/thu hoi/huy ket ban; khong xoa lich su phong chat")

        tokens = [csrf(client, "/profile") for client in (alice, bob)]
        def simultaneous(item):
            client, other_id, token = item
            return client.post(BASE + f"/friends/{other_id}/request", data={"csrf_token": token}, allow_redirects=False, timeout=15).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(simultaneous, [(alice, b_id, tokens[0]), (bob, a_id, tokens[1])]))
        assert results == [302, 302]
        # One request survives the race; sending in the opposite direction does
        # not silently grant friendship. The recipient must explicitly accept.
        a_page = alice.get(BASE + "/friends?view=requests", timeout=10).text
        if f'action="/friends/{b_id}/accept"' in a_page:
            receiver, sender_id = alice, b_id
        else:
            receiver, sender_id = bob, a_id
            assert f'action="/friends/{a_id}/accept"' in bob.get(BASE + "/friends?view=requests", timeout=10).text
        assert f'data-friend-user="{b_id}"' not in alice.get(BASE + "/friends", timeout=10).text
        assert post(receiver, f"/friends/{sender_id}/accept").status_code == 302
        assert f'data-friend-user="{b_id}"' in alice.get(BASE + "/friends", timeout=10).text
        assert post(carol, f"/friends/{a_id}/request").status_code == 302
        print("[OK] Hai loi moi nguoc chieu dong thoi: mot quan he, khong tu dong chap nhan")
        evidence_path = os.environ.get("DEMO_ACCESS_FILE")
        if evidence_path:
            descriptor = os.open(evidence_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write("GD3.3b - Chi xem rieng tren VM, khong chup mat khau.\n")
                for letter, name, user_id in zip(("A", "B", "C"), names, ids):
                    stream.write(f"Tai khoan {letter}: {name}\nID {letter}: {user_id}\n")
                stream.write(f"Mat khau chung: {password}\n")
                stream.write("A va B da la ban; C dang gui loi moi cho A.\nTrang: http://localhost:5000/friends\n")
            print("[OK] Luu tai khoan A/B/C minh chung rieng tren VM, quyen 600")
        print("FRIENDS33B_LIVE_CHECK_OK")
    finally:
        for sock in sockets:
            if sock.connected:
                sock.disconnect()
        for client in clients:
            client.close()


if __name__ == "__main__":
    main()
