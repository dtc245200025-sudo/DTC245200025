"""One normalized relationship per pair; lock both user rows before mutations."""

from flask import abort
from sqlalchemy import or_

from . import db, socketio
from .models import Friendship, User


def pair_condition(user_id):
    return or_(Friendship.user_low_id == user_id, Friendship.user_high_id == user_id)


def incoming_count(user_id):
    return db.session.scalar(db.select(db.func.count(Friendship.id)).where(
        pair_condition(user_id), Friendship.status == "pending", Friendship.requester_id != user_id,
    ))


def lock_pair(user_id, other_id):
    if other_id == user_id:
        abort(400, "Không thể kết bạn với chính mình.")
    if not 0 < other_id <= 2_147_483_647:
        abort(404)
    low, high = sorted((user_id, other_id))
    # Lock in a consistent order, including when the relationship does not yet
    # exist, so simultaneous A->B/B->A requests cannot create two records.
    users = db.session.scalars(db.select(User).where(User.id.in_((low, high)))
                               .order_by(User.id).with_for_update()
                               .execution_options(populate_existing=True)).all()
    if len(users) != 2:
        abort(404)
    relation = db.session.scalar(db.select(Friendship).where(
        Friendship.user_low_id == low, Friendship.user_high_id == high,
    ).with_for_update().execution_options(populate_existing=True))
    return low, high, relation


def notify_pair(low, high):
    # Only the two parties receive relationship changes, not every user.
    for user_id in (low, high):
        socketio.emit("friends_changed", {"incoming_count": incoming_count(user_id)}, to=f"user:{user_id}")
