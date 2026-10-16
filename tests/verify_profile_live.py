"""Exercise profile/privacy/avatar/presence/password against live HTTP + PostgreSQL."""

from io import BytesIO
import queue
import re
import secrets
import time

from PIL import Image
import requests
import socketio

from verify_live_chat import BASE, account, csrf


def post(client, path, data, expected=302):
    response = client.post(BASE + path, data={**data, "csrf_token": csrf(client, "/profile")}, allow_redirects=False, timeout=10)
    assert response.status_code == expected, "Profile operation returned an unexpected status"
    return response


def wait_presence(inbox, user_id, online):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        result = inbox.get(timeout=max(.1, deadline - time.monotonic()))
        if result == {"user_id": user_id, "online": online}:
            return
    raise AssertionError("Presence event was not received")


def main():
    suffix = secrets.token_hex(4)
    password = secrets.token_urlsafe(24)
    username_a, username_b = f"profile_a_{suffix}", f"profile_b_{suffix}"
    alice, bob = account(username_a, password), account(username_b, password)
    alice_id = int(re.search(r'data-presence-user="(\d+)"', alice.get(BASE + "/profile", timeout=10).text).group(1))
    bob_id = int(re.search(r'data-presence-user="(\d+)"', bob.get(BASE + "/profile", timeout=10).text).group(1))
    post(alice, "/profile", {"display_name": "Minh Anh", "bio": "Profile live check", "profile_public": "on"})
    page = bob.get(BASE + f"/users/{alice_id}", timeout=10).text
    assert "Minh Anh" in page and "Profile live check" in page
    assert 'name="display_name"' not in page
    post(alice, "/profile", {"username": "cannot-change", "display_name": "Wrong", "bio": ""}, expected=400)
    print("[OK] Ho so ca nhan/nguoi khac, ten hien thi va username co dinh")

    post(alice, "/profile", {"display_name": "Minh Anh", "bio": "Private live check"})
    private_page = bob.get(BASE + f"/users/{alice_id}", timeout=10).text
    assert "Private live check" not in private_page
    assert "Hồ sơ này đang ở chế độ riêng tư" in private_page
    post(alice, "/profile", {"display_name": "Minh Anh", "bio": "Profile live check", "profile_public": "on"})
    print("[OK] Quyen rieng tu duoc kiem tra o server")

    image_data = BytesIO()
    Image.new("RGB", (512, 512), color="#eab4cb").save(image_data, format="PNG")
    uploaded = bob.post(BASE + "/profile/avatar", data={"csrf_token": csrf(bob, "/profile")},
                        files={"avatar": ("avatar.png", image_data.getvalue(), "image/png")}, allow_redirects=False, timeout=10)
    assert uploaded.status_code == 302
    avatar = alice.get(BASE + f"/users/{bob_id}/avatar", timeout=10)
    assert avatar.status_code == 200 and avatar.headers["Content-Type"] == "image/png"
    assert Image.open(BytesIO(avatar.content)).size == (256, 256)
    post(bob, "/profile", {"display_name": "Bảo Ngọc", "bio": ""})
    assert alice.get(BASE + f"/users/{bob_id}/avatar", timeout=10).status_code == 404
    post(bob, "/profile", {"display_name": "Bảo Ngọc", "bio": "", "profile_public": "on"})
    print("[OK] Avatar that duoc chuan hoa, luu va an khi ho so rieng tu")

    inbox = queue.Queue()
    bob_socket = socketio.Client(http_session=bob, reconnection=False)
    alice_socket = socketio.Client(http_session=alice, reconnection=False)
    bob_socket.on("presence", inbox.put)
    try:
        bob_socket.connect(BASE, transports=["websocket"])
        alice_socket.connect(BASE, transports=["websocket"])
        wait_presence(inbox, alice_id, True)
        alice_socket.disconnect()
        wait_presence(inbox, alice_id, False)
        print("[OK] Online/offline theo ket noi WebSocket that")
    finally:
        if alice_socket.connected:
            alice_socket.disconnect()
        if bob_socket.connected:
            bob_socket.disconnect()

    old_session = requests.Session()
    old_session.cookies.update(alice.cookies)
    new_password = secrets.token_urlsafe(24)
    post(alice, "/profile/password", {"current_password": password, "new_password": new_password, "password_confirmation": new_password})
    assert old_session.get(BASE + "/profile", allow_redirects=False, timeout=10).status_code == 302
    token = csrf(alice, "/login")
    assert alice.post(BASE + "/login", data={"identifier": username_a, "password": password, "csrf_token": token}, allow_redirects=False, timeout=10).status_code == 401
    token = csrf(alice, "/login")
    assert alice.post(BASE + "/login", data={"identifier": username_a, "password": new_password, "csrf_token": token}, allow_redirects=False, timeout=10).status_code == 302
    print("[OK] Doi mat khau: mat khau cu bi tu choi, mat khau moi dang nhap duoc, phien cu het hieu luc")
    print("PROFILE_LIVE_CHECK_OK")


if __name__ == "__main__":
    main()
