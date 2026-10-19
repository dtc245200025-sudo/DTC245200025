from functools import wraps
import re

from email_validator import EmailNotValidError, validate_email
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text, func, or_

from . import db
from .models import User


web = Blueprint("web", __name__)


def normalized_email(value):
    return validate_email(value.strip(), check_deliverability=False).normalized.lower()


@web.before_app_request
def load_current_user():
    g.current_user = db.session.get(User, session["user_id"]) if session.get("user_id") else None
    if session.get("user_id") and (
        g.current_user is None or session.get("auth_version", 0) != g.current_user.auth_version
    ):
        session.clear()
        g.current_user = None


@web.app_context_processor
def account_context():
    from .presence import is_online
    from .friendship_service import incoming_count
    user = getattr(g, "current_user", None)
    from .notifications import unread_state
    return {"current_user": user, "is_online": is_online, "friend_requests_count": incoming_count(user.id) if user else 0,
            "unread": unread_state(user.id) if user else {"room_total": 0, "direct_total": 0, "rooms": {}, "directs": {}}}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("web.login"))
        return view(*args, **kwargs)

    return wrapped


@web.get("/healthz")
def healthz():
    try:
        db.session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        db.session.rollback()
        return {"status": "unavailable"}, 503
    return {"status": "ok"}


@web.get("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


@web.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not re.fullmatch(r"[A-Za-z0-9_.-]{3,80}", username) or not 8 <= len(password) <= 128:
            flash("Tên tài khoản: 3–80 chữ, số, dấu chấm, gạch dưới hoặc gạch ngang. Mật khẩu: 8–128 ký tự.", "error")
            return render_template("register.html"), 400
        try:
            email = normalized_email(request.form.get("email", ""))
        except EmailNotValidError:
            flash("Vui lòng nhập địa chỉ email hợp lệ.", "error")
            return render_template("register.html"), 400
        existing = db.session.scalar(db.select(User).where(or_(
            func.lower(User.username) == username.lower(), func.lower(User.email) == email,
        )))
        if existing:
            flash("Tên tài khoản hoặc email đã được sử dụng.", "error")
            return render_template("register.html"), 409
        user = User(username=username.lower(), email=email)
        user.set_password(password)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Tên tài khoản hoặc email đã được sử dụng.", "error")
            return render_template("register.html"), 409
        flash("Đăng ký thành công. Hãy đăng nhập.", "success")
        return redirect(url_for("web.login"))
    return render_template("register.html")


@web.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier", request.form.get("username", "")).strip()
        # Exact username first keeps older mixed-case accounts unambiguous.
        user = db.session.scalar(
            db.select(User).where(User.username == identifier)
        )
        if user is None:
            lookup = identifier.lower()
            if "@" in identifier:
                try:
                    lookup = normalized_email(identifier)
                except EmailNotValidError:
                    pass
                candidates = db.session.scalars(db.select(User).where(func.lower(User.email) == lookup).limit(2)).all()
            else:
                candidates = db.session.scalars(db.select(User).where(func.lower(User.username) == lookup).limit(2)).all()
            user = candidates[0] if len(candidates) == 1 else None
        if not user or not user.check_password(request.form.get("password", "")):
            flash("Thông tin đăng nhập không đúng.", "error")
            return render_template("login.html"), 401
        session.clear()
        session["user_id"] = user.id
        session["username"] = user.username
        session["auth_version"] = user.auth_version
        # Never accept an arbitrary external post-login redirect.
        return redirect(url_for("room_actions.invite") if request.args.get("next") == "/rooms/invite" else url_for("web.rooms"))
    return render_template("login.html")


@web.post("/logout")
def logout():
    # Global sign-out for this account: copied cookies and existing sockets expire.
    if g.current_user is not None:
        user_id = g.current_user.id
        db.session.execute(db.update(User).where(User.id == user_id).values(auth_version=User.auth_version + 1))
        db.session.commit()
        from .events import disconnect_user
        disconnect_user(user_id)
    session.clear()
    return redirect(url_for("web.login"))


@web.route("/", methods=["GET", "POST"])
@login_required
def rooms():
    if request.method == "POST":
        return create_room()
    return render_template("home.html")


@web.route("/rooms/create", methods=["GET", "POST"])
@login_required
def create_room():
    from .rooms import create_room_page
    return create_room_page()


@web.get("/rooms/search")
@login_required
def search_rooms():
    from .rooms import search_rooms_page
    return search_rooms_page()


@web.route("/account", methods=["GET", "POST"])
@login_required
def account():
    if request.method == "POST":
        if not g.current_user.check_password(request.form.get("current_password", "")):
            flash("Mật khẩu hiện tại không đúng.", "error")
            return render_template("account.html"), 400
        try:
            email = normalized_email(request.form.get("email", ""))
        except EmailNotValidError:
            flash("Vui lòng nhập địa chỉ email hợp lệ.", "error")
            return render_template("account.html"), 400
        g.current_user.email = email
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Email đã được sử dụng bởi tài khoản khác.", "error")
            return render_template("account.html"), 409
        flash("Đã cập nhật email. Bạn có thể dùng email này để đăng nhập.", "success")
        return redirect(url_for("web.account"))
    return render_template("account.html")


@web.get("/rooms/<int:room_id>")
@login_required
def chat(room_id):
    from .rooms import chat_page
    return chat_page(room_id)
