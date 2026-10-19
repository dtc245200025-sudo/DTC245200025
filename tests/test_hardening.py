import pytest

from test_app import make_app, register_and_login
from chatapp import create_app, socketio


def test_logout_disconnects_existing_sockets_but_not_other_users():
    app = make_app()
    alice, bob = app.test_client(), app.test_client()
    register_and_login(alice, 'alice'); register_and_login(bob, 'bob')
    old_cookie = alice.get_cookie(app.config['SESSION_COOKIE_NAME']).value
    first = socketio.test_client(app, flask_test_client=alice)
    second = socketio.test_client(app, flask_test_client=alice)
    other = socketio.test_client(app, flask_test_client=bob)
    try:
        assert alice.post('/logout').status_code == 302
        assert not first.is_connected() and not second.is_connected()
        assert other.is_connected()
        assert alice.get('/profile').status_code == 302
        assert not socketio.test_client(app, flask_test_client=alice).is_connected()
        replay = app.test_client(); replay.set_cookie(app.config['SESSION_COOKIE_NAME'], old_cookie)
        assert replay.get('/profile').status_code == 302
        assert not socketio.test_client(app, flask_test_client=replay).is_connected()
        assert bob.get('/profile').status_code == 200
    finally:
        for sock in (first, second, other):
            if sock.is_connected(): sock.disconnect()


@pytest.mark.parametrize('path', ['/register', '/login', '/logout'])
def test_auth_posts_require_valid_csrf(path):
    app = create_app({'TESTING': True, 'SECRET_KEY': 'hardening-test-key',
                      'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    client = app.test_client()
    assert client.post(path, data={}).status_code == 400
    assert client.post(path, data={'csrf_token': 'invalid-token'}).status_code == 400


def test_signed_cookie_tampering_is_rejected():
    app = make_app(); client = app.test_client(); register_and_login(client)
    cookie = client.get_cookie(app.config['SESSION_COOKIE_NAME'])
    guest = app.test_client()
    guest.set_cookie(app.config['SESSION_COOKIE_NAME'], cookie.value + 'tampered')
    assert guest.get('/profile').status_code == 302
    assert not socketio.test_client(app, flask_test_client=guest).is_connected()


def test_login_cannot_redirect_to_external_url_and_cookie_is_http_only():
    app = make_app(); client = app.test_client(); register_and_login(client)
    response = client.post('/login?next=https://untrusted.example/', data={'identifier': 'alice', 'password': 'password123'})
    assert response.status_code == 302 and response.location == '/'
    cookie = response.headers.get('Set-Cookie', '')
    assert 'HttpOnly' in cookie and 'SameSite=Lax' in cookie
    assert 'Secure' not in cookie  # HTTP lab: do not falsely claim HTTPS.
