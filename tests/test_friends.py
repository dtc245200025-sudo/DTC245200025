import pytest
from sqlalchemy.exc import IntegrityError

from test_app import make_app, register_and_login
from chatapp import create_app, db, socketio
from chatapp.models import Friendship, Message, RoomMember, User


@pytest.fixture
def people():
    app = make_app()
    clients = [app.test_client() for _ in range(3)]
    for client, name in zip(clients, ("alice", "bob", "carol")):
        register_and_login(client, name)
    return app, *clients


def relation(app):
    with app.app_context():
        return db.session.scalar(db.select(Friendship))


def test_search_username_display_name_and_exact_email_without_private_data_leak(people):
    app, alice, bob, _ = people
    bob.post("/profile", data={"display_name": "Minh Anh", "bio": "", "profile_public": "on"})
    for query in ("BOB", "minh", "BOB@EXAMPLE.COM"):
        response = alice.post("/friends/search", data={"q": query})
        assert response.status_code == 200
        assert "Xem hồ sơ @bob" in response.text
    # Search term can occur in the input; the private address must not appear in cards.
    result = alice.post("/friends/search", data={"q": "bob"}).text
    assert "bob@example.com" not in result
    assert 'data-friend-user="1"' not in result
    assert "Xem hồ sơ @bob" not in alice.post("/friends/search", data={"q": "bob@example.co"}).text
    assert "Xem hồ sơ @bob" not in alice.post("/friends/search", data={"q": "%"}).text
    bob.post("/profile", data={"display_name": "Secret name", "bio": "private-bio-marker"})
    assert "Xem hồ sơ @bob" not in alice.post("/friends/search", data={"q": "Secret name"}).text
    result = alice.post("/friends/search", data={"q": "bob@example.com"}).text
    assert "Xem hồ sơ @bob" in result and "Secret name" not in result and "private-bio-marker" not in result


def test_email_public_setting_and_search_html_are_escaped(people):
    app, alice, bob, _ = people
    bob.post("/profile", data={"display_name": "<b>Bob</b>", "bio": "", "profile_public": "on", "email_public": "on"})
    page = alice.post("/friends/search", data={"q": "bob"}).text
    assert "bob@example.com" in page and "&lt;b&gt;Bob&lt;/b&gt;" in page and "<b>Bob</b>" not in page
    page = alice.post("/friends/search", data={"q": '<script>alert("x")</script>'}).text
    assert '<script>alert("x")</script>' not in page


def test_request_is_pending_and_recipient_only_can_accept(people):
    app, alice, bob, carol = people
    assert alice.post("/friends/2/request").status_code == 302
    assert relation(app).status == "pending"
    assert 'action="/friends/1/accept"' in bob.get("/friends?view=requests").text
    assert alice.post("/friends/2/accept").status_code == 403
    assert carol.post("/friends/2/accept").status_code == 404
    assert relation(app).status == "pending"
    assert bob.post("/friends/1/accept").status_code == 302
    assert relation(app).status == "accepted"
    assert 'data-friend-user="2"' in alice.get("/friends").text
    assert 'data-friend-user="1"' in bob.get("/friends").text


def test_duplicate_and_crossed_requests_never_auto_accept(people):
    app, alice, bob, _ = people
    for _ in range(2):
        assert alice.post("/friends/2/request").status_code == 302
    assert bob.post("/friends/1/request").status_code == 302
    with app.app_context():
        row = db.session.scalar(db.select(Friendship))
        assert row.status == "pending" and row.requester_id == 1
        assert db.session.scalar(db.select(db.func.count(Friendship.id))) == 1
    bob.post("/friends/1/accept")
    alice.post("/friends/2/request")
    bob.post("/friends/1/accept")
    assert relation(app).status == "accepted"


def test_decline_cancel_and_retry_preserve_single_pair(people):
    app, alice, bob, _ = people
    alice.post("/friends/2/request")
    assert bob.post("/friends/1/cancel").status_code == 403
    assert alice.post("/friends/2/decline").status_code == 403
    assert bob.post("/friends/1/decline").status_code == 302
    assert relation(app).status == "declined"
    bob.post("/friends/1/request")
    assert relation(app).requester_id == 2
    assert alice.post("/friends/2/cancel").status_code == 403
    bob.post("/friends/1/cancel")
    assert relation(app).status == "cancelled"
    alice.post("/friends/2/request")
    assert relation(app).status == "pending"
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Friendship.id))) == 1


def test_unfriend_does_not_remove_chat_history_or_membership(people):
    app, alice, bob, _ = people
    alice.post("/rooms/create", data={"name": "Keep history"})
    bob.post("/rooms/1/join")
    with app.app_context():
        db.session.add(Message(room_id=1, user_id=1, content="Keep this message"))
        db.session.commit()
    alice.post("/friends/2/request")
    bob.post("/friends/1/accept")
    assert bob.post("/friends/1/remove").status_code == 302
    assert relation(app).status == "removed"
    assert 'data-friend-user="2"' not in alice.get("/friends").text
    assert "Keep this message" in bob.get("/rooms/1").text
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(RoomMember.id))) == 2
    alice.post("/friends/2/request")
    assert relation(app).status == "pending"


@pytest.mark.parametrize("path,expected", [("/friends/1/request", 400), ("/friends/999/request", 404), ("/friends/2147483648/request", 404), ("/friends/2/unknown", 404)])
def test_self_missing_user_and_bad_action_are_rejected(people, path, expected):
    app, alice, _, _ = people
    assert alice.post(path).status_code == expected
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Friendship.id))) == 0


def test_guest_and_csrf_protection(people):
    app, alice, _, _ = people
    assert app.test_client().get("/friends").status_code == 302
    assert app.test_client().post("/friends/1/request").status_code == 302
    app.config["WTF_CSRF_ENABLED"] = True
    for path in ("/friends/2/request", "/friends/search", "/friends/panel"):
        assert alice.post(path, data={"q": "bob"}).status_code == 400


def test_relation_events_are_private_and_presence_tracks_last_tab(people):
    app, alice, bob, carol = people
    sockets = [socketio.test_client(app, flask_test_client=client) for client in (alice, bob, carol)]
    for sock in sockets:
        sock.get_received()
    alice.post("/friends/2/request")
    assert any(event["name"] == "friends_changed" and event["args"][0]["incoming_count"] == 1 for event in sockets[1].get_received())
    assert not any(event["name"] == "friends_changed" for event in sockets[2].get_received())
    bob.post("/friends/1/accept")
    for sock in sockets[:2]:
        assert any(event["name"] == "friends_changed" and event["args"][0]["incoming_count"] == 0 for event in sock.get_received())
    second_tab = socketio.test_client(app, flask_test_client=bob)
    sockets[0].get_received()
    sockets[1].disconnect()
    assert not any(event["name"] == "presence" and event["args"][0] == {"user_id": 2, "online": False} for event in sockets[0].get_received())
    second_tab.disconnect()
    assert any(event["name"] == "presence" and event["args"][0] == {"user_id": 2, "online": False} for event in sockets[0].get_received())
    for sock in sockets:
        if sock.is_connected():
            sock.disconnect()


def test_panel_and_requests_badge_show_current_state_without_email_url(people):
    app, alice, bob, _ = people
    alice.post("/friends/2/request")
    page = bob.get("/friends?view=requests")
    assert page.headers["Cache-Control"] == "no-store"
    assert 'data-friend-request-count >1' in page.text
    panel = bob.post("/friends/panel", data={"view": "requests"})
    assert panel.status_code == 200 and 'action="/friends/1/accept"' in panel.text
    assert bob.post("/friends/panel", data={"view": "bad"}).status_code == 400
    search = bob.post("/friends/search", data={"q": "alice@example.com"})
    assert search.status_code == 200 and search.location is None


def test_database_rejects_self_pair_and_outsider_requester(people):
    app, *_ = people
    with app.app_context():
        for low, high, requester in ((1, 1, 1), (2, 1, 1), (1, 2, 3)):
            db.session.add(Friendship(user_low_id=low, user_high_id=high, requester_id=requester, status="pending"))
            with pytest.raises(IntegrityError):
                db.session.commit()
            db.session.rollback()


def test_schema_upgrade_creates_friendships_without_changing_existing_records(tmp_path):
    uri = f"sqlite:///{(tmp_path / 'upgrade.sqlite').as_posix()}"
    config = {"TESTING": True, "WTF_CSRF_ENABLED": False, "SECRET_KEY": "test-key", "SQLALCHEMY_DATABASE_URI": uri}
    first = create_app(config)
    client = first.test_client()
    register_and_login(client)
    client.post("/rooms/create", data={"name": "Existing"})
    with first.app_context():
        db.session.add(Message(room_id=1, user_id=1, content="Preserve"))
        db.session.commit()
        # Simulate the pre-friends schema; only this temporary test DB is changed.
        Friendship.__table__.drop(db.engine)
    second = create_app(config)
    with second.app_context():
        assert db.session.get(User, 1).username == "alice"
        assert db.session.get(Message, 1).content == "Preserve"
        assert db.session.scalar(db.select(db.func.count(Friendship.id))) == 0
