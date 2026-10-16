import os
import sys
import re

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from chatapp import create_app, db
from chatapp.models import Message, Room, RoomMember, User


def make_app():
    return create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-key",
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })


def register_and_login(client, username="alice", password="password123"):
    client.post("/register", data={"username": username, "email": f"{username}@example.com", "password": password})
    return client.post("/login", data={"username": username, "password": password})


def test_healthcheck():
    app = make_app()
    assert app.test_client().get("/healthz").json == {"status": "ok"}


def test_register_login_create_room():
    app = make_app()
    client = app.test_client()
    response = register_and_login(client)
    assert response.status_code == 302
    response = client.post("/", data={"name": "General"})
    assert response.status_code == 302
    with app.app_context():
        assert db.session.scalar(db.select(User).where(User.username == "alice"))
        assert db.session.scalar(db.select(Room).where(Room.name == "General"))


def test_socket_message_is_persisted():
    app = make_app()
    client = app.test_client()
    register_and_login(client)
    client.post("/", data={"name": "General"})
    with app.app_context():
        room = db.session.scalar(db.select(Room).where(Room.name == "General"))
        assert db.session.scalar(db.select(RoomMember).where(RoomMember.room_id == room.id))
    from chatapp import socketio
    socket_client = socketio.test_client(app, flask_test_client=client)
    socket_client.emit("join", {"room_id": room.id})
    socket_client.emit("send_message", {"room_id": room.id, "content": "Xin chào"})
    with app.app_context():
        message = db.session.scalar(db.select(Message))
        assert message.content == "Xin chào"


def test_two_users_receive_message_and_other_room_does_not():
    from chatapp import socketio
    app = make_app()
    alice, bob, carol = (app.test_client() for _ in range(3))
    for client, name in ((alice, "alice"), (bob, "bob"), (carol, "carol")):
        register_and_login(client, name)
    alice.post("/", data={"name": "General"})
    carol.post("/", data={"name": "Other"})
    with app.app_context():
        general_id = db.session.scalar(db.select(Room.id).where(Room.name == "General"))
        other_id = db.session.scalar(db.select(Room.id).where(Room.name == "Other"))
    bob.post(f"/rooms/{general_id}/join")
    clients = [socketio.test_client(app, flask_test_client=c) for c in (alice, bob, carol)]
    for client, room_id in zip(clients, (general_id, general_id, other_id)):
        assert client.emit("join", {"room_id": room_id}, callback=True)["ok"]
        client.get_received()
    clients[0].get_received()
    result = clients[0].emit("send_message", {"room_id": general_id, "content": "Xin chào"}, callback=True)
    assert result["ok"]
    for client in clients[:2]:
        received = client.get_received()
        assert any(event["name"] == "new_message" and event["args"][0]["content"] == "Xin chào" for event in received)
    assert not any(event["name"] == "new_message" for event in clients[2].get_received())
    for client in clients:
        client.disconnect()


@pytest.mark.parametrize("payload", [None, [], {"room_id": "bad"}, {"room_id": True}, {"room_id": 1, "content": " "}, {"room_id": 1, "content": "x" * 1001}])
def test_invalid_socket_input_is_rejected(payload):
    from chatapp import socketio
    app = make_app()
    client = app.test_client()
    register_and_login(client)
    client.post("/", data={"name": "General"})
    sock = socketio.test_client(app, flask_test_client=client)
    assert not sock.emit("send_message", payload, callback=True)["ok"]
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Message.id))) == 0
    sock.disconnect()


def test_guest_socket_and_nonmember_send_rejected():
    from chatapp import socketio
    app = make_app()
    assert not socketio.test_client(app).is_connected()
    alice, bob = app.test_client(), app.test_client()
    register_and_login(alice, "alice")
    register_and_login(bob, "bob")
    alice.post("/", data={"name": "General"})
    sock = socketio.test_client(app, flask_test_client=bob)
    assert not sock.emit("send_message", {"room_id": 1, "content": "Forbidden"}, callback=True)["ok"]
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Message.id))) == 0
    sock.disconnect()


def test_csrf_and_password_hash_and_local_client_library():
    app = make_app()
    app.config["WTF_CSRF_ENABLED"] = True
    client = app.test_client()
    assert client.post("/register", data={"username": "alice", "password": "password123"}).status_code == 400
    page = client.get("/register").text
    token = re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)
    response = client.post("/register", data={"username": "alice", "email": "alice@example.com", "password": "password123", "csrf_token": token})
    assert response.status_code == 302
    with app.app_context():
        user = db.session.scalar(db.select(User))
        assert user.password_hash != "password123"
        assert user.check_password("password123")
    assert client.get("/static/vendor/socket.io.min.js").status_code == 200


def test_metrics_endpoint_exports_chat_metrics():
    app = make_app()
    client = app.test_client()
    client.get("/healthz")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "chat_http_requests_total" in response.text
    assert "chat_messages_total" in response.text
