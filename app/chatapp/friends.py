from datetime import datetime, timezone

from email_validator import EmailNotValidError
from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from sqlalchemy import case, or_

from . import db
from .friendship_service import incoming_count, lock_pair, notify_pair, pair_condition
from .models import Friendship, User
from .routes import login_required, normalized_email


friends = Blueprint("friends", __name__)
VIEWS = {"friends", "requests", "search"}


def relationship_rows(user_id, status, direction=None):
    other_id = case((Friendship.user_low_id == user_id, Friendship.user_high_id), else_=Friendship.user_low_id)
    statement = db.select(User, Friendship).join(Friendship, User.id == other_id).where(
        pair_condition(user_id), Friendship.status == status,
    )
    if direction == "incoming":
        statement = statement.where(Friendship.requester_id != user_id)
    elif direction == "outgoing":
        statement = statement.where(Friendship.requester_id == user_id)
    return db.session.execute(statement.order_by(Friendship.updated_at.desc(), Friendship.id.desc()).limit(100)).all()


def search_rows(user_id, query):
    if not 2 <= len(query) <= 254:
        return []
    term = query.lower()
    conditions = [db.func.lower(User.username).contains(term, autoescape=True),
                  db.and_(User.profile_public.is_(True), db.func.lower(User.display_name).contains(term, autoescape=True))]
    if "@" in query:
        try:
            email = normalized_email(query)
        except EmailNotValidError:
            return []
        # Exact email lookup only; private emails are never rendered in cards.
        conditions = [db.func.lower(User.email) == email]
    users = db.session.scalars(db.select(User).where(User.id != user_id, or_(*conditions))
                               .order_by(User.username).limit(50)).all()
    relations = db.session.scalars(db.select(Friendship).where(pair_condition(user_id))).all()
    by_user = {relation.user_high_id if relation.user_low_id == user_id else relation.user_low_id: relation for relation in relations}
    return [(user, by_user.get(user.id)) for user in users]


def page_data(view, query=""):
    user_id = g.current_user.id
    accepted = relationship_rows(user_id, "accepted") if view == "friends" else []
    incoming = relationship_rows(user_id, "pending", "incoming") if view == "requests" else []
    outgoing = relationship_rows(user_id, "pending", "outgoing") if view == "requests" else []
    total = db.session.scalar(db.select(db.func.count(Friendship.id)).where(pair_condition(user_id), Friendship.status == "accepted"))
    return dict(view=view, query=query, accepted=accepted, incoming=incoming, outgoing=outgoing,
                results=search_rows(user_id, query) if view == "search" else [], total_friends=total,
                pending_count=incoming_count(user_id))


@friends.get("/friends")
@login_required
def index():
    view = request.args.get("view", "friends")
    return render_template("friends.html", **page_data(view if view in VIEWS else "friends"))


@friends.post("/friends/search")
@login_required
def search():
    query = request.form.get("q", "").strip()[:254]
    return render_template("friends.html", **page_data("search", query))


@friends.post("/friends/panel")
@login_required
def panel():
    view = request.form.get("view", "friends")
    if view not in VIEWS:
        abort(400)
    return render_template("_friends_panel.html", **page_data(view, request.form.get("q", "").strip()[:254]))


@friends.post("/friends/<int:other_id>/<action>")
@login_required
def change(other_id, action):
    if action not in {"request", "accept", "decline", "cancel", "remove"}:
        abort(404)
    user_id = g.current_user.id
    low, high, relation = lock_pair(user_id, other_id)
    changed = False
    destination = "requests"
    if action == "request":
        if relation and relation.status == "accepted":
            flash("Hai bạn đã là bạn bè.", "success")
            destination = "friends"
        elif relation and relation.status == "pending":
            flash("Bạn đã gửi lời mời này." if relation.requester_id == user_id else "Người này đã gửi lời mời cho bạn. Hãy chấp nhận trong mục Lời mời.", "success")
        else:
            if relation is None:
                relation = Friendship(user_low_id=low, user_high_id=high, requester_id=user_id)
                db.session.add(relation)
            relation.status = "pending"
            relation.requester_id = user_id
            relation.created_at = datetime.now(timezone.utc)
            changed = True
            flash("Đã gửi lời mời kết bạn.", "success")
    else:
        if relation is None:
            abort(404)
        if action in {"accept", "decline"}:
            if relation.requester_id == user_id:
                abort(403)
            if relation.status == "pending":
                relation.status = "accepted" if action == "accept" else "declined"
                changed = True
                flash("Đã chấp nhận lời mời. Hai bạn đã là bạn bè." if action == "accept" else "Đã từ chối lời mời.", "success")
                destination = "friends" if action == "accept" else "requests"
            else:
                flash("Lời mời này đã được xử lý.", "success")
        elif action == "cancel":
            if relation.requester_id != user_id:
                abort(403)
            if relation.status == "pending":
                relation.status = "cancelled"
                changed = True
                flash("Đã thu hồi lời mời.", "success")
        elif action == "remove":
            destination = "friends"
            if relation.status == "accepted":
                relation.status = "removed"
                changed = True
                flash("Đã hủy kết bạn. Lịch sử phòng chat không bị xóa.", "success")
    if changed:
        relation.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        notify_pair(low, high)
    return redirect(url_for("friends.index", view=destination))
