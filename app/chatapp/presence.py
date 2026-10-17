"""Presence of authenticated Socket.IO connections in this single-worker app."""

from threading import RLock
from prometheus_client import Gauge


_lock = RLock()
_sessions = {}


def connect(sid, user_id):
    with _lock:
        was_online = user_id in _sessions.values()
        _sessions[sid] = user_id
        return not was_online


def disconnect(sid):
    with _lock:
        user_id = _sessions.pop(sid, None)
        return user_id, user_id is not None and user_id not in _sessions.values()


def is_online(user_id):
    with _lock:
        return user_id in _sessions.values()


def online_ids():
    with _lock:
        return sorted(set(_sessions.values()))


def sessions_for(user_id):
    with _lock:
        return [sid for sid, owner in _sessions.items() if owner == user_id]


def reset():
    with _lock:
        _sessions.clear()


def connection_count():
    with _lock:
        return len(_sessions)


# Single-worker gauges read current state, so disconnects and resets cannot
# leave a stale count. No usernames, socket IDs or other private metric labels.
SOCKET_CONNECTIONS = Gauge("chat_socket_connections", "Current authenticated Socket.IO connections")
ONLINE_USERS = Gauge("chat_online_users", "Current distinct users with an authenticated Socket.IO connection")
SOCKET_CONNECTIONS.set_function(connection_count)
ONLINE_USERS.set_function(lambda: len(online_ids()))
