"""Shared membership checks and serialized room admission (PostgreSQL row lock)."""

from flask import abort

from . import db
from .models import Room, RoomMember


def membership(room_id, user_id):
    return db.session.scalar(db.select(RoomMember).where(
        RoomMember.room_id == room_id, RoomMember.user_id == user_id,
    ))


def member_count(room_id):
    return db.session.scalar(db.select(db.func.count(RoomMember.id)).where(RoomMember.room_id == room_id))


def lock_room(room_id):
    # All admission/leave/approval paths acquire this same row lock. Refresh any
    # ORM instance already loaded in the request before checking capacity.
    room = db.session.scalar(db.select(Room).where(Room.id == room_id)
                             .with_for_update().execution_options(populate_existing=True))
    if room is None:
        abort(404)
    return room


def admit(room, user_id):
    """Caller must hold lock_room through commit. Existing members are idempotent."""
    if membership(room.id, user_id):
        return True
    if room.max_members is not None and member_count(room.id) >= room.max_members:
        return False
    db.session.add(RoomMember(room_id=room.id, user_id=user_id))
    return True
