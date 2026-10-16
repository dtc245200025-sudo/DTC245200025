from io import BytesIO
from datetime import timedelta, timezone
import unicodedata
import warnings

from flask import Blueprint, abort, flash, g, make_response, redirect, render_template, request, session, url_for
from PIL import Image, ImageOps, UnidentifiedImageError

from . import db
from .events import disconnect_user
from .models import RoomMember, User
from .routes import login_required


profiles = Blueprint("profiles", __name__)
MAX_AVATAR_BYTES = 10 * 1024 * 1024


@profiles.app_template_filter("join_date")
def join_date(value):
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone(timedelta(hours=7))).strftime("%d/%m/%Y")


def profile_page(tab="info", status=200):
    count = db.session.scalar(db.select(db.func.count(RoomMember.id)).where(RoomMember.user_id == g.current_user.id))
    return render_template("profile.html", profile_user=g.current_user, own_profile=True,
                           can_view_profile=True, active_tab=tab, room_count=count), status


def valid_text(value):
    return not any(unicodedata.category(char) in {"Cc", "Cf", "Cs"} for char in value)


@profiles.route("/profile", methods=["GET", "POST"])
@login_required
def my_profile():
    if request.method == "POST":
        label = request.form.get("display_name", "").strip()
        bio = request.form.get("bio", "").strip()
        if request.form.get("username", g.current_user.username) != g.current_user.username:
            flash("Username dùng để đăng nhập và không thể thay đổi.", "error")
            return profile_page(status=400)
        if not 1 <= len(label) <= 80 or not valid_text(label) or len(bio) > 150 or not valid_text(bio):
            flash("Tên hiển thị cần 1–80 ký tự; giới thiệu tối đa 150 ký tự và không chứa ký tự điều khiển.", "error")
            return profile_page(status=400)
        g.current_user.display_name = label
        g.current_user.bio = bio
        g.current_user.profile_public = request.form.get("profile_public") == "on"
        g.current_user.email_public = request.form.get("email_public") == "on"
        db.session.commit()
        flash("Đã lưu thay đổi hồ sơ.", "success")
        return redirect(url_for("profiles.my_profile"))
    return profile_page("security" if request.args.get("tab") == "security" else "info")


@profiles.get("/users/<int:user_id>")
@login_required
def user_profile(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == g.current_user.id:
        return redirect(url_for("profiles.my_profile"))
    return render_template("profile.html", profile_user=user, own_profile=False,
                           can_view_profile=user.profile_public, active_tab="info", room_count=None)


@profiles.post("/profile/password")
@login_required
def change_password():
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirmation = request.form.get("password_confirmation", "")
    if not g.current_user.check_password(current_password):
        flash("Mật khẩu hiện tại không đúng.", "error")
        return profile_page("security", 400)
    if not 8 <= len(new_password) <= 128:
        flash("Mật khẩu mới phải dài từ 8 đến 128 ký tự.", "error")
        return profile_page("security", 400)
    if new_password != confirmation:
        flash("Xác nhận mật khẩu mới chưa khớp.", "error")
        return profile_page("security", 400)
    if g.current_user.check_password(new_password):
        flash("Mật khẩu mới phải khác mật khẩu hiện tại.", "error")
        return profile_page("security", 400)
    user_id = g.current_user.id
    g.current_user.set_password(new_password)
    g.current_user.auth_version += 1
    db.session.commit()
    disconnect_user(user_id)
    session.clear()
    flash("Đã cập nhật mật khẩu. Vui lòng đăng nhập lại; các phiên cũ đã hết hiệu lực.", "success")
    return redirect(url_for("web.login"))


def normalize_avatar(payload):
    if not payload or len(payload) > MAX_AVATAR_BYTES:
        raise ValueError("Ảnh không được vượt quá 10 MB.")
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(BytesIO(payload), formats=("JPEG", "PNG", "WEBP")) as source:
            if source.width * source.height > 16_000_000:
                raise ValueError("Ảnh quá lớn. Vui lòng chọn ảnh tối đa 16 triệu điểm ảnh.")
            source.load()
            image = ImageOps.exif_transpose(source).convert("RGBA")
            image.thumbnail((256, 256), Image.Resampling.LANCZOS)
            clean = Image.new("RGBA", image.size)
            clean.paste(image)
            target = BytesIO()
            clean.save(target, format="PNG", optimize=True)
            return target.getvalue()


@profiles.post("/profile/avatar")
@login_required
def upload_avatar():
    avatar = request.files.get("avatar")
    if avatar is None:
        flash("Vui lòng chọn ảnh JPG, PNG hoặc WebP.", "error")
        return profile_page(status=400)
    try:
        cleaned = normalize_avatar(avatar.stream.read(MAX_AVATAR_BYTES + 1))
    except (ValueError, OSError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        flash("Ảnh không hợp lệ. Chọn JPG, PNG hoặc WebP tối đa 10 MB và 16 triệu điểm ảnh.", "error")
        return profile_page(status=400)
    g.current_user.avatar_data = cleaned
    db.session.commit()
    flash("Đã cập nhật avatar.", "success")
    return redirect(url_for("profiles.my_profile"))


@profiles.get("/users/<int:user_id>/avatar")
@login_required
def avatar(user_id):
    user = db.get_or_404(User, user_id)
    if not user.avatar_data or (user.id != g.current_user.id and not user.profile_public):
        abort(404)
    response = make_response(user.avatar_data)
    response.headers["Content-Type"] = "image/png"
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@profiles.app_errorhandler(413)
def upload_too_large(error):
    flash("Dung lượng tải lên quá lớn. Avatar tối đa 10 MB.", "error")
    return redirect(url_for("profiles.my_profile") if session.get("user_id") else url_for("web.login"), 303)
