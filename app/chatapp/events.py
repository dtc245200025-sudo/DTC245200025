from flask import current_app, request, session
from flask_socketio import emit, join_room, leave_room
from prometheus_client import Counter

from . import db, socketio
from .models import Message, Room, RoomMember, User
from . import presence


CHAT_MESSAGES = Counter("chat_messages_total", "Persisted chat messages")


def parse_room(data):
    if not isinstance(data, dict):
        return None
    value = data.get("room_id")
    if isinstance(value, bool) or not isinstance(value, int) or not 0 < value <= 2_147_483_647:
        return None
    return value


def on_connect(auth=None):
    user = authenticated_user()
    if not user:
        return False
    join_room("authenticated")
    join_room(f"user:{user.id}")
    first_connection = presence.connect(request.sid, user.id)
    emit("presence_snapshot", {"online_ids": presence.online_ids()})
    from .friendship_service import incoming_count
    emit("friends_changed", {"incoming_count": incoming_count(user.id)})
    emit("unread_changed", {})
    if first_connection:
        emit("presence", {"user_id": user.id, "online": True}, to="authenticated")


def on_disconnect(reason=None):
    from .typing_events import stop_typing
    stop_typing(request.sid)
    user_id, last_connection = presence.disconnect(request.sid)
    if last_connection:
        socketio.emit("presence", {"user_id": user_id, "online": False}, to="authenticated")


def authenticated_user():
    user = db.session.get(User, session["user_id"]) if session.get("user_id") else None
    return user if user and session.get("auth_version", 0) == user.auth_version else None


def disconnect_user(user_id):
    socketio.emit("session_revoked", {}, to=f"user:{user_id}")
    for sid in presence.sessions_for(user_id):
        socketio.server.disconnect(sid, namespace="/")


def allowed(room_id):
    user_id = session.get("user_id")
    if not user_id or room_id is None or not authenticated_user():
        return False
    return db.session.scalar(
        db.select(RoomMember).where(
            RoomMember.room_id == room_id, RoomMember.user_id == user_id
        )
    ) is not None


def on_join(data):
    room_id = parse_room(data)
    if not allowed(room_id):
        return {"ok": False, "error": "Bạn chưa tham gia phòng này."}
    join_room(str(room_id))
    emit("status", {"message": f"{authenticated_user().label} đã tham gia phòng."}, to=str(room_id))
    return {"ok": True}


def on_leave(data):
    room_id = parse_room(data)
    if not allowed(room_id):
        return {"ok": False}
    from .typing_events import stop_typing
    stop_typing(request.sid, "room", room_id)
    leave_room(str(room_id))
    return {"ok": True}


def on_message(data):
    import re
    from .messaging import add_recipients, publish, serialize
    room_id = parse_room(data)
    if not isinstance(data, dict) or not isinstance(data.get("content"), str):
        return {"ok": False, "error": "Tin nhắn không hợp lệ."}
    content = data["content"].strip()
    nonce = data.get("client_nonce")
    if nonce is not None and (not isinstance(nonce, str) or not re.fullmatch(r"[A-Za-z0-9_-]{16,64}", nonce)):
        return {"ok": False, "error": "Mã gửi không hợp lệ."}
    if not allowed(room_id) or not content or len(content) > 1000:
        return {"ok": False, "error": "Kiểm tra phòng và độ dài tin nhắn (1–1000 ký tự)."}
    # Same row lock as join/leave avoids recipient snapshots racing membership.
    db.session.scalar(db.select(Room).where(Room.id == room_id).with_for_update())
    if not allowed(room_id):
        return {"ok": False, "error": "Bạn không còn trong phòng này."}
    if nonce:
        saved = db.session.scalar(db.select(Message).where(Message.room_id == room_id, Message.user_id == session["user_id"], Message.client_nonce == nonce))
        if saved:
            if saved.content != content or saved.attachment:
                return {"ok": False, "error": "Mã gửi đã dùng cho tin khác."}
            return {"ok": True, "id": saved.id, "message": serialize(saved, "room")}
    message = Message(room_id=room_id, user_id=session["user_id"], content=content, client_nonce=nonce)
    db.session.add(message)
    add_recipients(message, "room")
    db.session.commit()
    from .typing_events import stop_typing
    stop_typing(request.sid, "room", room_id)
    CHAT_MESSAGES.inc()
    current_app.logger.info("chat_message_saved room_id=%s message_id=%s", room_id, message.id)
    return {"ok": True, "id": message.id, "message": publish(message, "room")}


def register_events(server):
    from .typing_events import on_typing, reset
    presence.reset()
    reset()
    server.on_event("connect", on_connect)
    server.on_event("disconnect", on_disconnect)
    server.on_event("join", on_join)
    server.on_event("leave", on_leave)
    server.on_event("send_message", on_message)
    server.on_event("typing", on_typing)
    from .receipts import on_receipt
    server.on_event("message_receipt", on_receipt)
