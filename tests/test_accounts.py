import pytest
from sqlalchemy import create_engine, inspect, text

from test_app import make_app, register_and_login
from chatapp import db
from chatapp.models import User
from chatapp.migrations import upgrade_email_schema


@pytest.mark.parametrize("email", ["", "not-an-email", "user@localhost", "a b@example.com"])
def test_registration_requires_valid_email(email):
    app = make_app()
    client = app.test_client()
    response = client.post("/register", data={"username": "alice", "email": email, "password": "password123"})
    assert response.status_code == 400
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(User.id))) == 0


def test_email_and_username_are_case_insensitive_and_unique():
    app = make_app()
    client = app.test_client()
    assert client.post("/register", data={"username": "Alice", "email": "Alice@Example.com", "password": "password123"}).status_code == 302
    assert client.post("/register", data={"username": "bob", "email": "ALICE@example.COM", "password": "password123"}).status_code == 409
    assert client.post("/register", data={"username": "ALICE", "email": "other@example.com", "password": "password123"}).status_code == 409
    for identifier in ("alice", "ALICE", "alice@example.com", "ALICE@EXAMPLE.COM"):
        assert client.post("/login", data={"identifier": identifier, "password": "password123"}).status_code == 302
        with client.session_transaction() as state:
            assert state["user_id"] == 1
        client.post("/logout")
    assert client.post("/login", data={"identifier": "alice@example.com", "password": "wrong-password"}).status_code == 401


def test_legacy_account_can_add_email_with_password_confirmation():
    app = make_app()
    with app.app_context():
        user = User(username="legacy")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
    client = app.test_client()
    assert client.post("/login", data={"identifier": "legacy", "password": "password123"}).status_code == 302
    assert client.post("/account", data={"email": "legacy@example.com", "current_password": "wrong"}).status_code == 400
    with app.app_context():
        assert db.session.get(User, 1).email is None
    assert client.post("/account", data={"email": "legacy@example.com", "current_password": "password123"}).status_code == 302
    client.post("/logout")
    assert client.post("/login", data={"identifier": "LEGACY@example.com", "password": "password123"}).status_code == 302


def test_email_change_cannot_take_another_accounts_email():
    app = make_app()
    alice, bob = app.test_client(), app.test_client()
    register_and_login(alice, "alice")
    register_and_login(bob, "bob")
    response = bob.post("/account", data={"email": "ALICE@example.com", "current_password": "password123"})
    assert response.status_code == 409
    with app.app_context():
        assert db.session.scalar(db.select(User).where(User.username == "bob")).email == "bob@example.com"


def test_new_home_navigation_and_room_search():
    app = make_app()
    client = app.test_client()
    register_and_login(client)
    page = client.get("/").text
    assert "Xin chào đến với" in page
    assert 'href="/rooms/create"' in page
    assert 'href="/rooms/search"' in page
    assert 'class="account-dock"' in page
    assert 'data-theme-toggle' in page
    assert client.post("/rooms/create", data={"name": "LinhChat study"}).status_code == 302
    assert "LinhChat study" in client.get("/rooms/search?q=study").text
    assert "LinhChat study" not in client.get("/rooms/search?q=not-found").text
    assert "LinhChat study" not in client.get("/rooms/search?q=%25").text


def test_email_migration_is_additive_and_idempotent():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, username VARCHAR(80), password_hash VARCHAR(255))"))
        connection.execute(text("INSERT INTO users VALUES (1, 'old-account', 'existing-hash')"))
    upgrade_email_schema(engine)
    upgrade_email_schema(engine)
    assert "email" in {column["name"] for column in inspect(engine).get_columns("users")}
    with engine.connect() as connection:
        assert connection.execute(text("SELECT username, password_hash, email FROM users")).one() == ("old-account", "existing-hash", None)
