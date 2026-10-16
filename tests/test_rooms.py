import hashlib
import re

import pytest
from sqlalchemy import create_engine, inspect, text

from test_app import make_app, register_and_login
from chatapp import db, socketio
from chatapp.models import Message, Room, RoomJoinRequest, RoomMember
from chatapp.migrations import upgrade_room_schema


def setup_room(mode="open", limit=2):
    app = make_app()
    alice, bob, carol = (app.test_client() for _ in range(3))
    for client, name in ((alice, "alice"), (bob, "bob"), (carol, "carol")):
        register_and_login(client, name)
    response = alice.post("/rooms/create", data={"name": "Test room", "visibility": "public" if mode == "open" else "private",
                                               "join_mode": mode, "max_members": str(limit), "room_password": "roompassword123"})
    assert response.status_code == 302
    return app, alice, bob, carol


def test_public_get_does_not_join_and_capacity_counts_owner():
    app, alice, bob, carol = setup_room()
    assert "Tham gia phòng" in bob.get("/rooms/1").text
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(RoomMember.id))) == 1
    assert bob.post("/rooms/1/join").status_code == 302
    assert bob.post("/rooms/1/join").status_code == 302
    response = carol.post("/rooms/1/join")
    assert response.status_code == 409 and "Phòng đã đầy" in response.text
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(RoomMember.id))) == 2
    assert bob.post("/rooms/1/leave").status_code == 302
    assert carol.post("/rooms/1/join").status_code == 302
    assert alice.post("/rooms/1/leave").status_code == 302
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(RoomMember.id))) == 2


@pytest.mark.parametrize("fields", [
    {"visibility": "invalid"}, {"name": "x"}, {"visibility": "public", "max_members": "1"},
    {"max_members": "501"}, {"max_members": "-1"}, {"max_members": "2.5"},
    {"visibility": "private", "join_mode": "open"}, {"visibility": "private", "join_mode": "invalid"},
    {"visibility": "private", "join_mode": "password", "room_password": "short"},
])
def test_invalid_room_configuration_is_rejected(fields):
    app = make_app()
    client = app.test_client()
    register_and_login(client)
    response = client.post("/rooms/create", data={"name": "Example", **fields})
    assert response.status_code == 400
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Room.id))) == 0


def test_password_room_has_no_history_leak_and_stores_only_hash():
    app, alice, bob, _ = setup_room("password")
    with app.app_context():
        room = db.session.get(Room, 1)
        assert room.password_hash.startswith("scrypt:") and "roompassword123" not in room.password_hash
        db.session.add(Message(room_id=1, user_id=1, content="private-history-marker"))
        db.session.commit()
    assert "private-history-marker" not in bob.get("/rooms/1").text
    assert bob.get("/rooms/1").status_code == 403
    assert bob.post("/rooms/1/join", data={"room_password": "wrong"}).status_code == 403
    sock = socketio.test_client(app, flask_test_client=bob)
    assert not sock.emit("join", {"room_id": 1}, callback=True)["ok"]
    assert not sock.emit("send_message", {"room_id": 1, "content": "blocked"}, callback=True)["ok"]
    assert bob.post("/rooms/1/join", data={"room_password": "roompassword123"}).status_code == 302
    assert "private-history-marker" in bob.get("/rooms/1").text
    assert sock.emit("join", {"room_id": 1}, callback=True)["ok"]
    sock.disconnect()


def test_approval_only_owner_can_approve_or_reject_and_request_is_idempotent():
    app, alice, bob, carol = setup_room("approval")
    assert bob.get("/rooms/1").status_code == 403
    for _ in range(2):
        assert bob.post("/rooms/1/join").status_code == 302
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(RoomJoinRequest.id))) == 1
        assert db.session.scalar(db.select(db.func.count(RoomMember.id))) == 1
    assert bob.get("/rooms/1/manage").status_code == 403
    assert carol.post("/rooms/1/requests/1/approve").status_code == 403
    assert alice.post("/rooms/1/requests/1/reject").status_code == 302
    assert "đã bị từ chối" in bob.get("/rooms/1").text
    bob.post("/rooms/1/join")
    assert alice.post("/rooms/1/requests/1/approve").status_code == 302
    assert alice.post("/rooms/1/requests/1/approve").status_code == 302
    assert bob.get("/rooms/1").status_code == 200
    assert 'id="messages"' in bob.get("/rooms/1").text
    with app.app_context():
        assert db.session.get(RoomJoinRequest, 1).status == "approved"
        assert db.session.scalar(db.select(db.func.count(RoomMember.id))) == 2


def test_request_cannot_be_processed_from_a_different_room():
    app, alice, bob, _ = setup_room("approval")
    bob.post("/rooms/1/join")
    alice.post("/rooms/create", data={"name": "Other", "visibility": "private", "join_mode": "approval"})
    assert alice.post("/rooms/2/requests/1/approve").status_code == 404


def test_invitation_hidden_search_hashed_token_and_rotation():
    app, alice, bob, carol = setup_room("invite")
    assert "Test room" not in bob.get("/rooms/search").text
    assert "Test room" in alice.get("/rooms/search?scope=mine").text
    assert bob.get("/rooms/1").status_code == 404
    assert bob.post("/rooms/1/join").status_code == 404
    assert bob.post("/rooms/1/invitation").status_code == 403
    response = alice.post("/rooms/1/invitation")
    token = re.search(r'value="http://localhost/rooms/invite#([A-Za-z0-9_-]+)"', response.text).group(1)
    with app.app_context():
        assert db.session.get(Room, 1).invite_token_hash == hashlib.sha256(token.encode()).hexdigest()
    assert token not in alice.get("/rooms/1/manage").text
    assert bob.post("/rooms/invite", data={"invite_token": "forged"}).status_code == 403
    assert bob.post("/rooms/invite", data={"invite_token": token}).status_code == 302
    alice.post("/rooms/1/invitation")
    assert carol.post("/rooms/invite", data={"invite_token": token}).status_code == 403
    assert 'id="messages"' in bob.get("/rooms/1").text
    assert "Test room" in bob.get("/rooms/search?scope=mine").text
    assert bob.get("/rooms/1/manage").status_code == 403


def test_leaving_removes_socket_subscription_and_send_permission():
    app, alice, bob, _ = setup_room("password")
    bob.post("/rooms/1/join", data={"room_password": "roompassword123"})
    owner = socketio.test_client(app, flask_test_client=alice)
    guest = socketio.test_client(app, flask_test_client=bob)
    for sock in (owner, guest):
        assert sock.emit("join", {"room_id": 1}, callback=True)["ok"]
        sock.get_received()
    bob.post("/rooms/1/leave")
    guest.get_received()
    assert not guest.emit("send_message", {"room_id": 1, "content": "blocked"}, callback=True)["ok"]
    assert owner.emit("send_message", {"room_id": 1, "content": "members-only"}, callback=True)["ok"]
    assert not any(event["name"] == "new_message" for event in guest.get_received())
    for sock in (owner, guest):
        sock.disconnect()


def test_room_operations_require_csrf_and_invite_login_return_is_safe():
    app, alice, bob, _ = setup_room("open")
    app.config["WTF_CSRF_ENABLED"] = True
    assert bob.post("/rooms/1/join").status_code == 400
    assert alice.post("/rooms/create", data={"name": "Bad"}).status_code == 400
    assert alice.post("/rooms/1/leave").status_code == 400
    app.config["WTF_CSRF_ENABLED"] = False
    assert alice.post("/login?next=https://evil.example", data={"username": "alice", "password": "password123"}).location == "/"
    assert alice.post("/login?next=/rooms/invite", data={"username": "alice", "password": "password123"}).location == "/rooms/invite"
    response = bob.get("/rooms/invite")
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Referrer-Policy"] == "no-referrer"


def test_room_migration_preserves_legacy_records_and_is_idempotent():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE rooms (id INTEGER PRIMARY KEY, name VARCHAR(100), created_by INTEGER)"))
        connection.execute(text("INSERT INTO rooms VALUES (1, 'Old room', 1)"))
    upgrade_room_schema(engine)
    upgrade_room_schema(engine)
    assert {"visibility", "join_mode", "max_members", "password_hash", "invite_token_hash"} <= {c["name"] for c in inspect(engine).get_columns("rooms")}
    with engine.connect() as connection:
        assert connection.execute(text("SELECT name, visibility, join_mode, max_members FROM rooms")).one() == ("Old room", "public", "open", None)
