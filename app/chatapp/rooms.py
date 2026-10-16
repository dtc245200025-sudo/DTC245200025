from datetime import datetime, timezone
import hashlib
import re
import secrets
import unicodedata

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from . import db, socketio
from . import presence
from .models import Message, Room, RoomJoinRequest, RoomMember
from .room_access import admit, lock_room, member_count, membership
from .routes import login_required


room_actions = Blueprint("room_actions", __name__)


@room_actions.after_request
def private_response(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


def create_room_page():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        visibility = request.form.get("visibility", "public")
        mode = request.form.get("join_mode", "approval") if visibility == "private" else "open"
        limit = None
        password = request.form.get("room_password", "")
        error = None
        if not 2 <= len(name) <= 100 or any(unicodedata.category(c) in {"Cc", "Cf", "Cs"} for c in name):
            error = "Tên phòng cần 2–100 ký tự và không chứa ký tự điều khiển."
        elif visibility not in {"public", "private"} or mode not in {"open", "approval", "password", "invite"} or (visibility == "private" and mode == "open"):
            error = "Trạng thái hoặc cách tham gia phòng không hợp lệ."
        elif visibility == "public":
            raw_limit = request.form.get("max_members", "50")
            if not re.fullmatch(r"[0-9]{1,3}", raw_limit) or not 2 <= int(raw_limit) <= 500:
                error = "Phòng Public cần giới hạn từ 2 đến 500 người, tính cả chủ phòng."
            else:
                limit = int(raw_limit)
        elif mode == "password" and not 8 <= len(password) <= 128:
            error = "Mật khẩu phòng cần từ 8 đến 128 ký tự."
        if error:
            flash(error, "error")
            return render_template("create_room.html"), 400
        room = Room(name=name, created_by=g.current_user.id, visibility=visibility, join_mode=mode,
                    max_members=limit, password_hash=generate_password_hash(password) if mode == "password" else None)
        db.session.add(room)
        try:
            db.session.flush()
            db.session.add(RoomMember(room_id=room.id, user_id=g.current_user.id))
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Tên phòng đã tồn tại. Hãy chọn tên khác.", "error")
            return render_template("create_room.html"), 409
        if mode == "invite":
            return redirect(url_for("room_actions.manage", room_id=room.id))
        return redirect(url_for("web.chat", room_id=room.id))
    return render_template("create_room.html")


def search_rooms_page():
    query = request.args.get("q", "").strip()[:100]
    mine = request.args.get("scope") == "mine"
    joined = db.select(RoomMember.id).where(RoomMember.room_id == Room.id, RoomMember.user_id == g.current_user.id).exists()
    count = db.select(db.func.count(RoomMember.id)).where(RoomMember.room_id == Room.id).scalar_subquery()
    statement = db.select(Room, count.label("member_count"), joined.label("joined"))
    # Invite-only room metadata is not discoverable by nonmembers.
    statement = statement.where(joined if mine else or_(Room.join_mode != "invite", joined))
    if query:
        statement = statement.where(db.func.lower(Room.name).contains(query.lower(), autoescape=True))
    rows = db.session.execute(statement.order_by(Room.created_at.desc(), Room.id.desc()).limit(100)).all()
    return render_template("rooms.html", room_rows=rows, query=query, mine=mine)


def gate(room, status=200):
    pending = db.session.scalar(db.select(RoomJoinRequest).where(
        RoomJoinRequest.room_id == room.id, RoomJoinRequest.user_id == g.current_user.id,
    ))
    return render_template("room_join.html", room=room, count=member_count(room.id), join_request=pending), status


def chat_page(room_id):
    room = db.get_or_404(Room, room_id)
    if not membership(room.id, g.current_user.id):
        if room.join_mode == "invite":
            abort(404)
        return gate(room, 403 if room.visibility == "private" else 200)
    from .messaging import options
    messages = db.session.scalars(db.select(Message).options(*options(Message)).where(Message.room_id == room_id)
                                  .order_by(Message.id.desc()).limit(100)).all()
    return render_template("chat.html", room=room, messages=list(reversed(messages)), count=member_count(room_id))


@room_actions.post("/rooms/<int:room_id>/join")
@login_required
def join(room_id):
    room = lock_room(room_id)
    if membership(room.id, g.current_user.id):
        return redirect(url_for("web.chat", room_id=room.id))
    if room.join_mode == "invite":
        abort(404)
    if room.join_mode == "password" and not (room.password_hash and check_password_hash(room.password_hash, request.form.get("room_password", "")[:129])):
        flash("Mật khẩu phòng không đúng.", "error")
        return gate(room, 403)
    if room.join_mode == "approval":
        application = db.session.scalar(db.select(RoomJoinRequest).where(
            RoomJoinRequest.room_id == room.id, RoomJoinRequest.user_id == g.current_user.id,
        ))
        if application is None:
            db.session.add(RoomJoinRequest(room_id=room.id, user_id=g.current_user.id))
        else:
            application.status = "pending"
            application.created_at = datetime.now(timezone.utc)
        db.session.commit()
        socketio.emit("room_request_pending", {"room_id": room.id}, to=f"user:{room.created_by}")
        flash("Đã gửi yêu cầu. Hãy chờ chủ phòng phê duyệt.", "success")
        return redirect(url_for("web.chat", room_id=room.id))
    if not admit(room, g.current_user.id):
        flash("Phòng đã đầy. Vui lòng chọn phòng khác hoặc chờ có chỗ trống.", "error")
        return gate(room, 409)
    db.session.commit()
    return redirect(url_for("web.chat", room_id=room.id))


def owner_room(room_id):
    room = lock_room(room_id)
    if room.created_by != g.current_user.id:
        abort(403)
    return room


def management_page(room, invitation_url=None):
    applications = db.session.scalars(db.select(RoomJoinRequest).where(
        RoomJoinRequest.room_id == room.id, RoomJoinRequest.status == "pending",
    ).order_by(RoomJoinRequest.created_at)).all()
    members = db.session.scalars(db.select(RoomMember).where(RoomMember.room_id == room.id)).all()
    return render_template("room_manage.html", room=room, applications=applications, count=len(members), invitation_url=invitation_url)


@room_actions.get("/rooms/<int:room_id>/manage")
@login_required
def manage(room_id):
    return management_page(owner_room(room_id))


@room_actions.post("/rooms/<int:room_id>/requests/<int:application_id>/<decision>")
@login_required
def decide(room_id, application_id, decision):
    room = owner_room(room_id)
    if room.join_mode != "approval" or decision not in {"approve", "reject"}:
        abort(400)
    application = db.get_or_404(RoomJoinRequest, application_id)
    if application.room_id != room.id:
        abort(404)
    if application.status != "pending":
        flash("Yêu cầu này đã được xử lý.", "error")
        return redirect(url_for("room_actions.manage", room_id=room.id))
    if decision == "approve":
        if not admit(room, application.user_id):
            abort(409)
        application.status = "approved"
    else:
        application.status = "rejected"
    db.session.commit()
    socketio.emit("room_request_result", {"room_id": room.id, "approved": decision == "approve"}, to=f"user:{application.user_id}")
    flash("Đã phê duyệt thành viên." if decision == "approve" else "Đã từ chối yêu cầu.", "success")
    return redirect(url_for("room_actions.manage", room_id=room.id))


@room_actions.post("/rooms/<int:room_id>/invitation")
@login_required
def invitation(room_id):
    room = owner_room(room_id)
    if room.join_mode != "invite":
        abort(400)
    token = secrets.token_urlsafe(32)
    room.invite_token_hash = hashlib.sha256(token.encode()).hexdigest()
    db.session.commit()
    # Fragment never reaches HTTP access logs or referrer headers. Only a hash
    # is persisted. The owner sees the raw link once and can rotate it later.
    link = url_for("room_actions.invite", _external=True) + "#" + token
    return management_page(room, link)


@room_actions.route("/rooms/invite", methods=["GET", "POST"])
def invite():
    if request.method == "POST":
        if not g.current_user:
            return redirect(url_for("web.login", next="/rooms/invite"))
        token = request.form.get("invite_token", "")
        room = None
        if re.fullmatch(r"[A-Za-z0-9_-]{43}", token):
            room = db.session.scalar(db.select(Room).where(
                Room.join_mode == "invite", Room.visibility == "private",
                Room.invite_token_hash == hashlib.sha256(token.encode()).hexdigest(),
            ).with_for_update().execution_options(populate_existing=True))
        if room is None:
            flash("Link mời không hợp lệ hoặc đã được thay mới. Hãy xin chủ phòng link mới.", "error")
            return render_template("room_invite.html"), 403
        if not admit(room, g.current_user.id):
            abort(409)
        db.session.commit()
        return redirect(url_for("web.chat", room_id=room.id))
    return render_template("room_invite.html")


@room_actions.post("/rooms/<int:room_id>/leave")
@login_required
def leave(room_id):
    room = lock_room(room_id)
    if room.created_by == g.current_user.id:
        flash("Chủ phòng cần ở lại để quản lý phòng.", "error")
        return redirect(url_for("web.chat", room_id=room.id))
    member = membership(room.id, g.current_user.id)
    if not member:
        abort(403)
    db.session.delete(member)
    application = db.session.scalar(db.select(RoomJoinRequest).where(
        RoomJoinRequest.room_id == room.id, RoomJoinRequest.user_id == g.current_user.id,
    ))
    if application:
        application.status = "cancelled"
    db.session.commit()
    # Remove every tab from the Socket.IO room, not from the whole application.
    for sid in presence.sessions_for(g.current_user.id):
        from .typing_events import stop_typing
        stop_typing(sid, "room", room.id)
        socketio.emit("room_left", {"room_id": room.id}, to=sid)
        socketio.server.leave_room(sid, str(room.id), namespace="/")
    flash("Bạn đã rời phòng.", "success")
    from .notifications import changed
    changed(g.current_user.id)
    return redirect(url_for("web.search_rooms"))
