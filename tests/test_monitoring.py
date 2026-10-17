from prometheus_client import REGISTRY

from test_direct import people
from chatapp import socketio


def test_socket_gauges_count_sessions_separately_from_people(people):
    app, alice, bob, _ = people
    a1 = socketio.test_client(app, flask_test_client=alice)
    a2 = socketio.test_client(app, flask_test_client=alice)
    b = socketio.test_client(app, flask_test_client=bob)
    try:
        assert REGISTRY.get_sample_value("chat_socket_connections") == 3
        assert REGISTRY.get_sample_value("chat_online_users") == 2
        assert not socketio.test_client(app).is_connected()
        a1.disconnect()
        assert REGISTRY.get_sample_value("chat_socket_connections") == 2
        assert REGISTRY.get_sample_value("chat_online_users") == 2
        a2.disconnect()
        assert REGISTRY.get_sample_value("chat_socket_connections") == 1
        assert REGISTRY.get_sample_value("chat_online_users") == 1
        metrics = bob.get("/metrics").text
        assert "chat_socket_connections 1.0" in metrics
        assert "chat_online_users 1.0" in metrics
        assert "alice" not in metrics and "bob" not in metrics
    finally:
        for sock in (a1, a2, b):
            if sock.is_connected(): sock.disconnect()
    assert REGISTRY.get_sample_value("chat_socket_connections") == 0
    assert REGISTRY.get_sample_value("chat_online_users") == 0
