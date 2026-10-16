"""Two-party conversations, separate from group rooms and membership."""

from datetime import datetime, timezone
import re

from flask import Blueprint, abort, current_app, g, jsonify, request, session, url_for, redirect, render_template
from flask_socketio import emit, join_room, leave_room
from prometheus_client import Counter
from sqlalchemy import case, or_

from . import db, socketio
from .friendship_service import lock_pair
from .models import DirectConversation, DirectMessage, Friendship, User
from .routes import login_required


direct = Blueprint("direct", __name__)
DIRECT_MESSAGES = Counter("chat_direct_messages_total", "Persisted direct chat messages")


def participant(conversation, user_id):
    return conversation and user_id in (conversation.user_low_id, conversation.user_high_id)


def can_send(conversation):
    return db.session.scalar(db.select(Friendship.id).where(
        Friendship.user_low_id == conversation.user_low_id,
        Friendship.user_high_id == conversation.user_high_id, Friendship.status == "accepted",
    )) is not None


def payload(message):
    from .messaging import serialize
    return serialize(message, "direct")


def history_rows(conversation_id, after=0, before=None):
    from .messaging import options
    statement = db.select(DirectMessage).where(DirectMessage.conversation_id == conversation_id).options(*options(DirectMessage))
    if after:
        return db.session.scalars(statement.where(DirectMessage.id > after).order_by(DirectMessage.id).limit(100)).all()
    if before:
        statement = statement.where(DirectMessage.id < before)
    return list(reversed(db.session.scalars(statement.order_by(DirectMessage.id.desc()).limit(100)).all()))


def inbox_rows(user_id):
    other_id = case((DirectConversation.user_low_id == user_id, DirectConversation.user_high_id), else_=DirectConversation.user_low_id)
    latest_id = db.select(db.func.max(DirectMessage.id)).where(DirectMessage.conversation_id == DirectConversation.id).correlate(DirectConversation).scalar_subquery()
    return db.session.execute(db.select(DirectConversation, User, DirectMessage)
        .join(User, User.id == other_id).outerjoin(DirectMessage, DirectMessage.id == latest_id)
        .where(or_(DirectConversation.user_low_id == user_id, DirectConversation.user_high_id == user_id))
        .order_by(DirectConversation.updated_at.desc(), DirectConversation.id.desc()).limit(100)).all()


@direct.post("/direct/start/<int:other_id>")
@login_required
def start(other_id):
    low, high, relation = lock_pair(g.current_user.id, other_id)
    if not relation or relation.status != "accepted":
        abort(403, "Hai bạn cần kết bạn trước khi bắt đầu trò chuyện riêng.")
    conversation = db.session.scalar(db.select(DirectConversation).where(
        DirectConversation.user_low_id == low, DirectConversation.user_high_id == high,
    ))
    if conversation is None:
        conversation = DirectConversation(user_low_id=low, user_high_id=high)
        db.session.add(conversation)
        db.session.commit()
        notify_inbox(conversation)
    return redirect(url_for("direct.chat", conversation_id=conversation.id))


def get_conversation(conversation_id):
    if not 0 < conversation_id <= 2_147_483_647:
        abort(404)
    conversation = db.session.get(DirectConversation, conversation_id)
    if not participant(conversation, g.current_user.id):
        abort(404)
    return conversation


@direct.get("/direct")
@login_required
def index():
    return render_template("direct.html", inbox=inbox_rows(g.current_user.id), conversation=None)


@direct.get("/direct/panel")
@login_required
def panel():
    return render_template("_direct_inbox.html", inbox=inbox_rows(g.current_user.id))


@direct.get("/direct/<int:conversation_id>")
@login_required
def chat(conversation_id):
    conversation = get_conversation(conversation_id)
    other_id = conversation.user_high_id if conversation.user_low_id == g.current_user.id else conversation.user_low_id
    return render_template("direct.html", conversation=conversation, peer=db.session.get(User, other_id),
                           messages=history_rows(conversation.id), can_send=can_send(conversation), inbox=inbox_rows(g.current_user.id))


@direct.get("/direct/<int:conversation_id>/history")
@login_required
def history(conversation_id):
    conversation = get_conversation(conversation_id)
    values = {}
    for key in ("after", "before"):
        raw = request.args.get(key, "0")
        if not re.fullmatch(r"[0-9]{1,10}", raw) or int(raw) > 2_147_483_647:
            abort(400)
        values[key] = int(raw)
    if values["after"] and values["before"]:
        abort(400)
    messages = history_rows(conversation.id, **values)
    return jsonify(messages=[payload(message) for message in messages], can_send=can_send(conversation), has_more=len(messages) == 100)


def notify_inbox(conversation):
    for user_id in (conversation.user_low_id, conversation.user_high_id):
        socketio.emit("direct_changed", {"conversation_id": conversation.id}, to=f"user:{user_id}")


def parse_id(data):
    value = data.get("conversation_id") if isinstance(data, dict) else None
    return value if type(value) is int and 0 < value <= 2_147_483_647 else None


def socket_conversation(data):
    from .events import authenticated_user
    user = authenticated_user()
    conversation_id = parse_id(data)
    conversation = db.session.get(DirectConversation, conversation_id) if user and conversation_id else None
    return conversation if user and participant(conversation, user.id) else None


def on_join(data):
    conversation = socket_conversation(data)
    if not conversation:
        return {"ok": False, "error": "Không tìm thấy cuộc trò chuyện."}
    join_room(f"direct:{conversation.id}")
    return {"ok": True}


def on_leave(data):
    conversation = socket_conversation(data)
    if not conversation:
        return {"ok": False}
    from .typing_events import stop_typing
    stop_typing(request.sid, "direct", conversation.id)
    leave_room(f"direct:{conversation.id}")
    return {"ok": True}


def on_message(data):
    conversation = socket_conversation(data)
    if not conversation or not isinstance(data.get("content"), str):
        return {"ok": False, "error": "Tin nhắn hoặc cuộc trò chuyện không hợp lệ."}
    content, nonce = data["content"].strip(), data.get("client_nonce")
    if not content or len(content) > 1000 or not isinstance(nonce, str) or not re.fullmatch(r"[A-Za-z0-9_-]{16,64}", nonce):
        return {"ok": False, "error": "Tin nhắn cần 1–1000 ký tự và mã gửi hợp lệ."}
    other_id = conversation.user_high_id if conversation.user_low_id == session["user_id"] else conversation.user_low_id
    # Same lock order as unfriend/start serializes permission checks and retries.
    _, _, relation = lock_pair(session["user_id"], other_id)
    saved = db.session.scalar(db.select(DirectMessage).where(
        DirectMessage.conversation_id == conversation.id, DirectMessage.user_id == session["user_id"], DirectMessage.client_nonce == nonce,
    ))
    if saved:
        if saved.content != content or saved.attachment:
            return {"ok": False, "error": "Mã gửi đã dùng cho một tin nhắn khác."}
        return {"ok": True, "message": payload(saved)}
    if not relation or relation.status != "accepted":
        return {"ok": False, "error": "Hai bạn cần kết bạn để gửi tin nhắn mới."}
    message = DirectMessage(conversation_id=conversation.id, user_id=session["user_id"], content=content, client_nonce=nonce)
    db.session.add(message)
    from .messaging import add_recipients, publish
    add_recipients(message, "direct")
    conversation.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    DIRECT_MESSAGES.inc()
    current_app.logger.info("direct_message_saved conversation_id=%s message_id=%s", conversation.id, message.id)
    body = publish(message, "direct")
    from .typing_events import stop_typing
    stop_typing(request.sid, "direct", conversation.id)
    return {"ok": True, "message": body}


def register_direct_events(server):
    server.on_event("direct_join", on_join)
    server.on_event("direct_leave", on_leave)
    server.on_event("direct_send", on_message)
