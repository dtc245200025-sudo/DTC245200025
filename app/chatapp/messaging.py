"""Shared serialization, access and recipient snapshots for group/direct chat."""

from flask import abort, session, url_for
from sqlalchemy.orm import joinedload, selectinload

from . import db, socketio
from .models import DirectConversation, DirectMessage, Message, MessageReceipt, Room, RoomMember


MODELS = {"room": Message, "direct": DirectMessage}


def valid_id(value):
    return type(value) is int and 0 < value <= 2_147_483_647


def options(model):
    return (joinedload(model.user), selectinload(model.receipts), selectinload(model.attachment))


def target_column(model, scope):
    return model.room_id if scope == "room" else model.conversation_id


def receipt_column(scope):
    return MessageReceipt.room_message_id if scope == "room" else MessageReceipt.direct_message_id


def accessible(scope, target_id, user_id):
    if not isinstance(scope, str) or scope not in MODELS or not valid_id(target_id):
        return False
    if scope == "room":
        return db.session.scalar(db.select(RoomMember.id).where(RoomMember.room_id == target_id, RoomMember.user_id == user_id)) is not None
    from .direct import participant
    return bool(participant(db.session.get(DirectConversation, target_id), user_id))


def require_access(scope, target_id, user_id):
    if not accessible(scope, target_id, user_id):
        abort(404)
    return MODELS[scope]


def summary(message):
    return {"recipients": len(message.receipts),
            "delivered": sum(row.delivered_at is not None for row in message.receipts),
            "seen": sum(row.seen_at is not None for row in message.receipts)}


def attachment_payload(attachment):
    if attachment is None:
        return None
    return {"id": attachment.id, "filename": attachment.filename, "size": attachment.byte_size, "is_image": attachment.is_image,
            "download_url": url_for("chat_tools.download", attachment_id=attachment.id),
            "preview_url": url_for("chat_tools.preview", attachment_id=attachment.id) if attachment.is_image else None}


def serialize(message, scope):
    target_id = message.room_id if scope == "room" else message.conversation_id
    return {"id": message.id, "scope": scope, "target_id": target_id,
            "room_id" if scope == "room" else "conversation_id": target_id,
            "user_id": message.user_id, "username": message.user.label if message.user.profile_public else message.user.username,
            "content": message.content, "created_at": message.created_at.isoformat(),
            "receipts_tracked": message.receipts_tracked, "receipt_summary": summary(message),
            "recipient_ids": [row.user_id for row in message.receipts],
            "attachment": attachment_payload(message.attachment)}


def add_recipients(message, scope):
    if scope == "room":
        recipients = db.session.scalars(db.select(RoomMember.user_id).where(RoomMember.room_id == message.room_id, RoomMember.user_id != message.user_id)).all()
    else:
        conversation = db.session.get(DirectConversation, message.conversation_id)
        recipients = [conversation.user_high_id if conversation.user_low_id == message.user_id else conversation.user_low_id]
    message.receipts_tracked = True
    message.receipts = [MessageReceipt(user_id=user_id) for user_id in recipients]


def publish(message, scope):
    body = serialize(message, scope)
    if scope == "room":
        # Deliver the complete envelope to members on any application page.
        # Personal rooms avoid duplicate delivery when a chat is also open.
        members = db.session.scalars(db.select(RoomMember.user_id).where(RoomMember.room_id == message.room_id)).all()
        for user_id in members:
            socketio.emit("new_message", body, to=f"user:{user_id}")
    else:
        from .direct import notify_inbox
        conversation = db.session.get(DirectConversation, message.conversation_id)
        for user_id in (conversation.user_low_id, conversation.user_high_id):
            socketio.emit("direct_message", body, to=f"user:{user_id}")
        notify_inbox(conversation)
    from .notifications import notify_message
    notify_message(message, scope)
    return body


def write_target(scope, target_id, user_id):
    """Lock in the same order as membership/friendship changes."""
    require_access(scope, target_id, user_id)
    if scope == "room":
        from .room_access import lock_room, membership
        lock_room(target_id)
        if not membership(target_id, user_id):
            abort(404)
    else:
        from .friendship_service import lock_pair
        conversation = db.session.get(DirectConversation, target_id)
        other = conversation.user_high_id if conversation.user_low_id == user_id else conversation.user_low_id
        _, _, relation = lock_pair(user_id, other)
        if not relation or relation.status != "accepted":
            abort(403, "Hai bạn cần kết bạn để gửi tin nhắn mới.")
    return MODELS[scope]
