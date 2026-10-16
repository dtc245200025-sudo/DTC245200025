"""Ephemeral typing hints: no keystrokes or draft content stored/transmitted."""

from threading import RLock
import time

from flask import request
from flask_socketio import rooms

from . import socketio


_lock = RLock()
_active = {}
TTL = 4


def room_name(scope, target_id):
    return str(target_id) if scope == "room" else f"direct:{target_id}"


def reset():
    with _lock:
        _active.clear()


def _payload(scope, target_id, user_id, name):
    now = time.monotonic()
    active = any(key[1:] == (scope, target_id) and value[0] == user_id and now - value[2] < TTL for key, value in _active.items())
    return {"scope": scope, "target_id": target_id, "user_id": user_id, "name": name, "typing": active}


def set_typing(sid, user_id, name, scope, target_id, active):
    now = time.monotonic()
    key = (sid, scope, target_id)
    with _lock:
        for expired in [key for key, value in _active.items() if now - value[2] >= TTL]:
            del _active[expired]
        previous = _active.get(key)
        if active:
            if previous and now - previous[2] < .6:
                return None
            if not previous and sum(item[0] == sid for item in _active) >= 8:
                return None
            _active[key] = (user_id, name, now)
        else:
            _active.pop(key, None)
        return _payload(scope, target_id, user_id, name)


def stop_typing(sid, scope=None, target_id=None):
    with _lock:
        keys = [key for key in _active if key[0] == sid and (scope is None or key[1:] == (scope, target_id))]
        removed = [(key, _active.pop(key)) for key in keys]
        payloads = [_payload(key[1], key[2], value[0], value[1]) for key, value in removed]
    for body in payloads:
        socketio.emit("typing", body, to=room_name(body["scope"], body["target_id"]), skip_sid=sid)


def on_typing(data):
    from .events import authenticated_user, allowed
    from .direct import socket_conversation, can_send
    user = authenticated_user()
    if not user or not isinstance(data, dict) or type(data.get("typing")) is not bool:
        return {"ok": False}
    scope, target_id = data.get("scope"), data.get("target_id")
    if not isinstance(scope, str) or scope not in {"room", "direct"} or type(target_id) is not int or not 0 < target_id <= 2_147_483_647:
        return {"ok": False}
    target = room_name(scope, target_id)
    if target not in rooms():
        return {"ok": False}
    if scope == "room":
        if not allowed(target_id):
            return {"ok": False}
    else:
        conversation = socket_conversation({"conversation_id": target_id})
        if not conversation or not can_send(conversation):
            return {"ok": False}
    body = set_typing(request.sid, user.id, user.label if user.profile_public else user.username, scope, target_id, data["typing"])
    if body:
        socketio.emit("typing", body, to=target, skip_sid=request.sid)
    return {"ok": True}
