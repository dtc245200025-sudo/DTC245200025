from datetime import datetime, timezone

from flask import session
from prometheus_client import Counter

from . import db, socketio
from .messaging import MODELS, accessible, receipt_column, summary, target_column, valid_id
from .models import MessageReceipt


ACKS = Counter("chat_receipt_updates_total", "First delivered/seen acknowledgements", ["kind"])


def on_receipt(data):
    from .events import authenticated_user
    user = authenticated_user()
    if not user or not isinstance(data, dict):
        return {"ok": False}
    scope, target_id, ids, kind = data.get("scope"), data.get("target_id"), data.get("message_ids"), data.get("kind")
    if not isinstance(kind, str) or kind not in {"delivered", "seen"} or not isinstance(ids, list) or not 1 <= len(ids) <= 100 or not all(valid_id(item) for item in ids):
        return {"ok": False}
    if not accessible(scope, target_id, user.id):
        return {"ok": False}
    ids = sorted(set(ids))
    model = MODELS[scope]
    messages = db.session.scalars(db.select(model).where(target_column(model, scope) == target_id, model.id.in_(ids))).all()
    if len(messages) != len(ids) or any(message.user_id == user.id or not message.receipts_tracked for message in messages):
        return {"ok": False}
    rows = db.session.scalars(db.select(MessageReceipt).where(receipt_column(scope).in_(ids), MessageReceipt.user_id == user.id)
                              .order_by(MessageReceipt.id).with_for_update().execution_options(populate_existing=True)).all()
    # A late joiner was not an intended recipient when the message was sent.
    if len(rows) != len(ids):
        return {"ok": False}
    changed = set()
    now = datetime.now(timezone.utc)
    for row in rows:
        message_id = row.room_message_id if scope == "room" else row.direct_message_id
        if row.delivered_at is None:
            row.delivered_at = now
            changed.add(message_id)
        if kind == "seen" and row.seen_at is None:
            row.seen_at = now
            changed.add(message_id)
    db.session.commit()
    for message in messages:
        if message.id in changed:
            ACKS.labels(kind).inc()
            socketio.emit("receipt_updated", {"scope": scope, "target_id": target_id, "message_id": message.id,
                                             "summary": summary(message)}, to=f"user:{message.user_id}")
    if changed and kind == "seen":
        from .notifications import changed as notify_unread
        notify_unread(user.id)
    return {"ok": True}
