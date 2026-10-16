"""In-app notifications; unread state comes from durable recipient receipts."""

from flask import Blueprint, g, jsonify, url_for
from sqlalchemy import or_

from . import db, socketio
from .models import DirectConversation, DirectMessage, Message, MessageReceipt, Room, RoomMember
from .routes import login_required


notifications = Blueprint("notifications", __name__)


def unread_state(user_id):
    rooms = dict(db.session.execute(db.select(Message.room_id, db.func.count(MessageReceipt.id))
        .join(MessageReceipt, MessageReceipt.room_message_id == Message.id)
        .join(RoomMember, (RoomMember.room_id == Message.room_id) & (RoomMember.user_id == user_id))
        .where(MessageReceipt.user_id == user_id, MessageReceipt.seen_at.is_(None))
        .group_by(Message.room_id)).all())
    directs = dict(db.session.execute(db.select(DirectMessage.conversation_id, db.func.count(MessageReceipt.id))
        .join(MessageReceipt, MessageReceipt.direct_message_id == DirectMessage.id)
        .join(DirectConversation, DirectConversation.id == DirectMessage.conversation_id)
        .where(MessageReceipt.user_id == user_id, MessageReceipt.seen_at.is_(None),
               or_(DirectConversation.user_low_id == user_id, DirectConversation.user_high_id == user_id))
        .group_by(DirectMessage.conversation_id)).all())
    room_total, direct_total = sum(rooms.values()), sum(directs.values())
    return {"rooms": rooms, "directs": directs, "room_total": room_total,
            "direct_total": direct_total, "total": room_total + direct_total}


@notifications.get("/notifications/state")
@login_required
def state():
    # Never accept another user's ID or mark anything seen through a GET.
    return jsonify(unread_state(g.current_user.id))


def changed(user_id):
    # Invalidate rather than push counts that can arrive out of order.
    socketio.emit("unread_changed", {}, to=f"user:{user_id}")


def notify_message(message, scope):
    if scope == "room":
        title = "# " + db.session.get(Room, message.room_id).name
        target_id = message.room_id
        link = url_for("web.chat", room_id=target_id)
        members = set(db.session.scalars(db.select(RoomMember.user_id).where(RoomMember.room_id == target_id)))
    else:
        title = "Tin nhắn riêng"
        target_id = message.conversation_id
        link = url_for("direct.chat", conversation_id=target_id)
        conversation = db.session.get(DirectConversation, target_id)
        members = {conversation.user_low_id, conversation.user_high_id}
    sender = message.user.label if message.user.profile_public else message.user.username
    body = {"scope": scope, "target_id": target_id, "message_id": message.id,
            "sender": sender, "title": title, "url": link,
            "preview": (message.content or ("Tệp: " + message.attachment.filename if message.attachment else "Tin nhắn mới"))[:180]}
    for receipt in message.receipts:
        if receipt.user_id != message.user_id and receipt.user_id in members:
            socketio.emit("message_notification", body, to=f"user:{receipt.user_id}")
            changed(receipt.user_id)
