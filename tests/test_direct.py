import pytest
from sqlalchemy.exc import IntegrityError

from test_app import make_app, register_and_login
from chatapp import create_app, db, socketio
from chatapp.models import DirectConversation, DirectMessage, Message, User
from chatapp import typing_events


@pytest.fixture
def people():
    app = make_app()
    clients = [app.test_client() for _ in range(3)]
    for client, name in zip(clients, ("alice", "bob", "carol")):
        register_and_login(client, name)
    clients[0].post("/friends/2/request")
    clients[1].post("/friends/1/accept")
    return app, *clients


def start(alice):
    result = alice.post("/direct/start/2")
    assert result.status_code == 302
    return result.headers["Location"]


def connect(app, *clients):
    return [socketio.test_client(app, flask_test_client=client) for client in clients]


def send(sock, content="Xin chào riêng", nonce="0123456789abcdef"):
    return sock.emit("direct_send", {"conversation_id": 1, "content": content, "client_nonce": nonce}, callback=True)


def test_start_from_both_sides_reuses_one_pair_and_requires_accepted_friend(people):
    app, alice, bob, carol = people
    path = start(alice)
    assert bob.post("/direct/start/1").headers["Location"] == path
    assert alice.post("/direct/start/3").status_code == 403
    assert alice.post("/direct/start/1").status_code == 400
    assert alice.post("/direct/start/999").status_code == 404
    assert alice.post("/direct/start/999999999999").status_code == 404
    assert alice.get("/direct/start/2").status_code == 405
    assert carol.post("/direct/start/1").status_code == 403
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(DirectConversation.id))) == 1
    assert 'action="/direct/start/2"' in alice.get("/friends").text


def test_http_history_inbox_and_socket_are_private(people):
    app, alice, bob, carol = people
    path = start(alice)
    a, b, c = connect(app, alice, bob, carol)
    try:
        for sock in (a, b):
            assert sock.emit("direct_join", {"conversation_id": 1}, callback=True)["ok"]
        assert not c.emit("direct_join", {"conversation_id": 1}, callback=True)["ok"]
        for sock in (a, b, c):
            sock.get_received()
        assert send(a, "private-only-marker")["ok"]
        for client in (alice, bob):
            assert "private-only-marker" in client.get(path).text
            assert "private-only-marker" in client.get("/direct").text
            assert client.get(path + "/history").json["messages"][0]["content"] == "private-only-marker"
        assert carol.get(path).status_code == 404
        assert carol.get(path + "/history").status_code == 404
        assert "private-only-marker" not in carol.get("/direct/panel").text
        assert not send(c, "forbidden")["ok"]
        for sock in (a, b):
            assert any(event["name"] == "direct_message" for event in sock.get_received())
        assert not any(event["name"] in {"direct_message", "direct_changed"} for event in c.get_received())
    finally:
        for sock in (a, b, c):
            sock.disconnect()


def test_retry_is_idempotent_and_nonce_cannot_change_content(people):
    app, alice, bob, _ = people
    start(alice)
    a, b = connect(app, alice, bob)
    try:
        first = send(a)
        a.get_received(); b.get_received()
        second = send(a)
        assert first == second and first["ok"]
        assert not send(a, "different body")["ok"]
        assert not any(event["name"] == "direct_message" for event in b.get_received())
        with app.app_context():
            assert db.session.scalar(db.select(db.func.count(DirectMessage.id))) == 1
            assert db.session.scalar(db.select(db.func.count(Message.id))) == 0
    finally:
        a.disconnect(); b.disconnect()


@pytest.mark.parametrize("data", [None, [], {}, {"conversation_id": True}, {"conversation_id": "1"}, {"conversation_id": 2**40},
    {"conversation_id": 1, "content": " "}, {"conversation_id": 1, "content": "x" * 1001},
    {"conversation_id": 1, "content": "hello", "client_nonce": "short"}, {"conversation_id": 1, "content": "hello", "client_nonce": []}])
def test_invalid_socket_input_is_rejected(people, data):
    app, alice, _, _ = people
    start(alice)
    a = connect(app, alice)[0]
    try:
        assert not a.emit("direct_send", data, callback=True)["ok"]
        with app.app_context():
            assert db.session.scalar(db.select(db.func.count(DirectMessage.id))) == 0
    finally:
        a.disconnect()


def test_unfriend_preserves_history_blocks_new_messages_and_reuses_on_reconnect(people):
    app, alice, bob, _ = people
    path = start(alice)
    a, b = connect(app, alice, bob)
    try:
        assert send(a)["ok"]
        bob.post("/friends/1/remove")
        for client in (alice, bob):
            response = client.get(path)
            assert "Xin chào riêng" in response.text and 'data-can-send="false"' in response.text
            assert client.get(path + "/history").json["can_send"] is False
        assert not send(a, "blocked", "1123456789abcdef")["ok"]
        assert send(a)["ok"]  # An ACK retry of an already saved message is read-only.
        assert alice.post("/direct/start/2").status_code == 403
        alice.post("/friends/2/request"); bob.post("/friends/1/accept")
        assert start(alice) == path
        assert send(b, "reply", "2123456789abcdef")["ok"]
    finally:
        a.disconnect(); b.disconnect()


def test_history_paging_and_html_escape_private_profile(people):
    app, alice, bob, _ = people
    path = start(alice)
    bob.post("/profile", data={"display_name": "Hidden display name", "bio": "secret"})
    with app.app_context():
        db.session.add_all([DirectMessage(conversation_id=1, user_id=2, client_nonce=f"nonce-{index:016d}", content=f"<script>{index}</script>") for index in range(105)])
        db.session.commit()
    page = alice.get(path).text
    assert "Hidden display name" not in page and "bob@example.com" not in page
    assert "&lt;script&gt;104&lt;/script&gt;" in page and "<script>104</script>" not in page
    latest = alice.get(path + "/history").json
    assert len(latest["messages"]) == 100 and latest["messages"][0]["id"] == 6
    assert latest["messages"][0]["username"] == "bob"
    after = alice.get(path + "/history?after=1").json
    assert len(after["messages"]) == 100 and after["messages"][-1]["id"] == 101 and after["has_more"]
    older = alice.get(path + "/history?before=6").json
    assert [item["id"] for item in older["messages"]] == [1, 2, 3, 4, 5] and not older["has_more"]
    for query in ("after=-1", "after=nan", "after=999999999999", "after=1&before=2"):
        assert alice.get(path + "/history?" + query).status_code == 400


def test_csrf_guest_and_revoked_session(people):
    app, alice, _, _ = people
    path = start(alice)
    a = connect(app, alice)[0]
    try:
        app.config["WTF_CSRF_ENABLED"] = True
        assert alice.post("/direct/start/2").status_code == 400
        guest = app.test_client()
        assert guest.get(path).status_code == 302 and guest.get(path + "/history").status_code == 302
        assert not socketio.test_client(app).is_connected()
        with app.app_context():
            db.session.get(User, 1).auth_version += 1
            db.session.commit()
        assert not send(a)["ok"]
        assert not a.emit("direct_join", {"conversation_id": 1}, callback=True)["ok"]
    finally:
        a.disconnect()


def typing(sock, active=True, scope="direct", target_id=1):
    return sock.emit("typing", {"scope": scope, "target_id": target_id, "typing": active}, callback=True)


def test_direct_typing_requires_join_and_does_not_leak_to_other_user(people):
    app, alice, bob, carol = people
    start(alice)
    a, b, c = connect(app, alice, bob, carol)
    try:
        assert not typing(a)["ok"]
        for sock in (a, b):
            sock.emit("direct_join", {"conversation_id": 1})
            sock.get_received()
        c.get_received()
        assert not typing(c)["ok"]
        assert typing(a)["ok"]
        event = next(event["args"][0] for event in b.get_received() if event["name"] == "typing")
        assert event == {"scope": "direct", "target_id": 1, "user_id": 1, "name": "alice", "typing": True}
        assert "content" not in event
        assert not any(event["name"] == "typing" for event in c.get_received())
        assert not any(event["name"] == "typing" for event in a.get_received())
        assert typing(a, False)["ok"]
        assert any(event["name"] == "typing" and not event["args"][0]["typing"] for event in b.get_received())
    finally:
        for sock in (a, b, c):
            sock.disconnect()


def test_group_typing_membership_scope_and_leave_stop(people):
    app, alice, bob, carol = people
    alice.post("/rooms/create", data={"name": "Typing room"}); bob.post("/rooms/1/join")
    a, b, c = connect(app, alice, bob, carol)
    try:
        for sock in (a, b):
            sock.emit("join", {"room_id": 1})
            sock.get_received()
        c.get_received()
        assert typing(a, scope="room")["ok"]
        assert any(event["name"] == "typing" and event["args"][0]["typing"] for event in b.get_received())
        assert not typing(c, scope="room")["ok"]
        assert not typing(a, scope="direct")["ok"]  # Same numeric ID must not cross the room/DM boundary.
        assert not c.get_received()
        a.emit("leave", {"room_id": 1})
        assert any(event["name"] == "typing" and not event["args"][0]["typing"] for event in b.get_received())
        assert not typing(a, scope="room")["ok"]
    finally:
        for sock in (a, b, c):
            sock.disconnect()


def test_typing_multitab_disconnect_send_and_unfriend(people):
    app, alice, bob, _ = people
    start(alice)
    a, a2, b = connect(app, alice, alice, bob)
    try:
        for sock in (a, a2, b):
            sock.emit("direct_join", {"conversation_id": 1}); sock.get_received()
        typing(a); typing(a2); b.get_received()
        a.disconnect()
        assert any(event["name"] == "typing" and event["args"][0]["typing"] for event in b.get_received())
        assert send(a2)["ok"]
        assert any(event["name"] == "typing" and not event["args"][0]["typing"] for event in b.get_received())
        typing(a2); b.get_received()
        a2.disconnect()
        assert any(event["name"] == "typing" and not event["args"][0]["typing"] for event in b.get_received())
        bob.post("/friends/1/remove")
        assert not typing(b)["ok"]
    finally:
        for sock in (a, a2, b):
            if sock.is_connected(): sock.disconnect()


@pytest.mark.parametrize("data", [None, [], {}, {"scope": [], "target_id": 1, "typing": True}, {"scope": "all", "target_id": 1, "typing": True},
    {"scope": "room", "target_id": True, "typing": True}, {"scope": "direct", "target_id": 1, "typing": "true"}])
def test_invalid_typing_payload_rejected(people, data):
    app, alice, _, _ = people
    a = connect(app, alice)[0]
    try:
        assert not a.emit("typing", data, callback=True)["ok"]
    finally:
        a.disconnect()


def test_typing_throttle_expiry_and_no_draft_storage(monkeypatch):
    typing_events.reset()
    now = [100.0]
    monkeypatch.setattr(typing_events.time, "monotonic", lambda: now[0])
    assert typing_events.set_typing("sid", 1, "A", "direct", 1, True)["typing"]
    assert typing_events.set_typing("sid", 1, "A", "direct", 1, True) is None
    now[0] += 5
    assert not typing_events.set_typing("sid", 1, "A", "direct", 1, False)["typing"]
    assert not typing_events._active


def test_additive_upgrade_preserves_legacy_data(tmp_path):
    config = {"TESTING": True, "SECRET_KEY": "test", "WTF_CSRF_ENABLED": False,
              "SQLALCHEMY_DATABASE_URI": f"sqlite:///{(tmp_path / 'legacy.sqlite').as_posix()}"}
    app = create_app(config)
    client = app.test_client(); register_and_login(client)
    client.post("/rooms/create", data={"name": "Legacy room"})
    with app.app_context():
        db.session.add(Message(room_id=1, user_id=1, content="Keep legacy history")); db.session.commit()
        DirectMessage.__table__.drop(db.engine); DirectConversation.__table__.drop(db.engine)
    upgraded = create_app(config)
    with upgraded.app_context():
        assert db.session.get(Message, 1).content == "Keep legacy history"
        assert db.session.get(User, 1).username == "alice"
        assert db.session.scalar(db.select(db.func.count(DirectConversation.id))) == 0
        db.session.add(DirectConversation(user_low_id=1, user_high_id=1))
        with pytest.raises(IntegrityError): db.session.commit()
        db.session.rollback()
