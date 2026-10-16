from io import BytesIO

import pytest
from PIL import Image, PngImagePlugin
from sqlalchemy import create_engine, inspect, text

from test_app import make_app, register_and_login
from chatapp import db, socketio
from chatapp.models import User
from chatapp.migrations import upgrade_profile_schema


def test_edit_display_name_bio_and_username_is_immutable():
    app = make_app()
    alice, bob = app.test_client(), app.test_client()
    register_and_login(alice, "alice")
    register_and_login(bob, "bob")
    response = alice.post("/profile", data={
        "display_name": "Minh Anh", "username": "alice", "bio": "Thành viên LinhChat.", "profile_public": "on",
    })
    assert response.status_code == 302
    with app.app_context():
        user = db.session.get(User, 1)
        assert user.username == "alice"
        assert user.label == "Minh Anh"
        assert user.initials == "MA"
        assert user.bio == "Thành viên LinhChat."
    page = bob.get("/users/1").text
    assert "Minh Anh" in page and "Thành viên LinhChat." in page
    assert "alice@example.com" not in page
    assert 'name="display_name"' not in page
    assert alice.post("/profile", data={"username": "hijacked", "display_name": "Other", "bio": ""}).status_code == 400
    with app.app_context():
        assert db.session.get(User, 1).username == "alice"


def test_bio_length_and_html_escaping():
    app = make_app()
    client = app.test_client()
    register_and_login(client)
    assert client.post("/profile", data={"display_name": "Alice", "bio": "x" * 151}).status_code == 400
    assert client.post("/profile", data={"display_name": "Alice", "bio": "<script>alert(1)</script>", "profile_public": "on"}).status_code == 302
    page = client.get("/profile").text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page
    assert "<script>alert(1)</script>" not in page


def test_private_profile_does_not_leak_bio_email_or_edit_forms():
    app = make_app()
    alice, bob = app.test_client(), app.test_client()
    register_and_login(alice, "alice")
    register_and_login(bob, "bob")
    alice.post("/profile", data={"display_name": "Private name", "bio": "Private biography", "email_public": "on"})
    page = bob.get("/users/1").text
    assert "Hồ sơ này đang ở chế độ riêng tư" in page
    assert "Private biography" not in page and "alice@example.com" not in page
    assert "Private name" not in page
    assert 'name="display_name"' not in page
    assert "Private biography" in alice.get("/profile").text
    assert app.test_client().get("/users/1").status_code == 302


def test_email_visibility_is_opt_in():
    app = make_app()
    alice, bob = app.test_client(), app.test_client()
    register_and_login(alice, "alice")
    register_and_login(bob, "bob")
    alice.post("/profile", data={"display_name": "Alice", "bio": "", "profile_public": "on", "email_public": "on"})
    assert "alice@example.com" in bob.get("/users/1").text
    alice.post("/profile", data={"display_name": "Alice", "bio": "", "profile_public": "on"})
    assert "alice@example.com" not in bob.get("/users/1").text


@pytest.mark.parametrize("current,new,confirmation", [
    ("wrong-password", "newpassword123", "newpassword123"),
    ("password123", "short", "short"),
    ("password123", "newpassword123", "does-not-match"),
    ("password123", "password123", "password123"),
])
def test_invalid_password_change_preserves_password(current, new, confirmation):
    app = make_app()
    client = app.test_client()
    register_and_login(client)
    response = client.post("/profile/password", data={"current_password": current, "new_password": new, "password_confirmation": confirmation})
    assert response.status_code == 400
    assert 'aria-selected="true" data-profile-tab="security"' in response.text
    with app.app_context():
        user = db.session.get(User, 1)
        assert user.check_password("password123")
        assert user.auth_version == 0


def test_password_change_hashes_password_and_invalidates_old_sessions_and_sockets():
    app = make_app()
    first, other = app.test_client(), app.test_client()
    register_and_login(first)
    other.post("/login", data={"identifier": "alice", "password": "password123"})
    sockets = [socketio.test_client(app, flask_test_client=client) for client in (first, other)]
    assert all(sock.is_connected() for sock in sockets)
    response = first.post("/profile/password", data={"current_password": "password123", "new_password": "newpassword123", "password_confirmation": "newpassword123"})
    assert response.status_code == 302 and response.location.endswith("/login")
    assert not any(sock.is_connected() for sock in sockets)
    assert other.get("/profile").status_code == 302
    assert first.post("/login", data={"identifier": "alice", "password": "password123"}).status_code == 401
    assert first.post("/login", data={"identifier": "alice", "password": "newpassword123"}).status_code == 302
    with app.app_context():
        user = db.session.get(User, 1)
        assert user.password_hash != "newpassword123"
        assert user.check_password("newpassword123")
        assert user.auth_version == 1


def png_image():
    data = BytesIO()
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("Comment", "private-image-metadata")
    Image.new("RGB", (512, 400), color="pink").save(data, format="PNG", pnginfo=metadata)
    return data.getvalue()


def test_avatar_is_reencoded_resized_private_and_retained_in_database():
    app = make_app()
    alice, bob = app.test_client(), app.test_client()
    register_and_login(alice, "alice")
    register_and_login(bob, "bob")
    response = alice.post("/profile/avatar", data={"avatar": (BytesIO(png_image()), "photo.png")}, content_type="multipart/form-data")
    assert response.status_code == 302
    result = alice.get("/users/1/avatar")
    assert result.content_type == "image/png"
    assert "no-store" in result.headers["Cache-Control"]
    assert result.headers["X-Content-Type-Options"] == "nosniff"
    assert b"private-image-metadata" not in result.data
    image = Image.open(BytesIO(result.data))
    assert max(image.size) <= 256
    assert bob.get("/users/1/avatar").status_code == 200
    alice.post("/profile", data={"display_name": "Alice", "bio": ""})
    assert bob.get("/users/1/avatar").status_code == 404
    assert alice.get("/users/1/avatar").status_code == 200


@pytest.mark.parametrize("payload,filename", [(b"<svg onload='alert(1)'></svg>", "fake.png"), (b"not an image", "fake.jpg"), (b"x" * (10 * 1024 * 1024 + 1), "too-large.png")], ids=["svg-is-not-png", "invalid-jpeg", "over-10mb"])
def test_invalid_and_oversized_avatars_are_rejected(payload, filename):
    app = make_app()
    client = app.test_client()
    register_and_login(client)
    response = client.post("/profile/avatar", data={"avatar": (BytesIO(payload), filename)}, content_type="multipart/form-data")
    assert response.status_code == 400
    with app.app_context():
        assert db.session.get(User, 1).avatar_data is None


def test_presence_counts_multiple_tabs_and_only_goes_offline_after_last_disconnect():
    app = make_app()
    alice, bob = app.test_client(), app.test_client()
    register_and_login(alice, "alice")
    register_and_login(bob, "bob")
    observer = socketio.test_client(app, flask_test_client=bob)
    observer.get_received()
    first = socketio.test_client(app, flask_test_client=alice)
    events = observer.get_received()
    assert any(event["name"] == "presence" and event["args"][0] == {"user_id": 1, "online": True} for event in events)
    second = socketio.test_client(app, flask_test_client=alice)
    observer.get_received()
    first.disconnect()
    assert not any(event["name"] == "presence" and event["args"][0].get("user_id") == 1 and not event["args"][0]["online"] for event in observer.get_received())
    second.disconnect()
    assert any(event["name"] == "presence" and event["args"][0] == {"user_id": 1, "online": False} for event in observer.get_received())
    observer.disconnect()


def test_profile_updates_require_csrf():
    app = make_app()
    client = app.test_client()
    register_and_login(client)
    app.config["WTF_CSRF_ENABLED"] = True
    assert client.post("/profile", data={"display_name": "Changed", "bio": ""}).status_code == 400
    assert client.post("/profile/password", data={"current_password": "password123", "new_password": "newpassword123", "password_confirmation": "newpassword123"}).status_code == 400


def test_profile_migration_is_idempotent_and_preserves_existing_user():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, username VARCHAR(80), password_hash VARCHAR(255))"))
        connection.execute(text("INSERT INTO users VALUES (1, 'old', 'original-hash')"))
    upgrade_profile_schema(engine)
    upgrade_profile_schema(engine)
    assert {"display_name", "bio", "profile_public", "email_public", "avatar_data", "auth_version"} <= {column["name"] for column in inspect(engine).get_columns("users")}
    with engine.connect() as connection:
        assert connection.execute(text("SELECT username, password_hash, bio, auth_version FROM users")).one() == ("old", "original-hash", "", 0)
