from datetime import datetime, timezone
import hashlib
from io import BytesIO
import re
from threading import BoundedSemaphore
import unicodedata
import uuid

from flask import Blueprint, abort, current_app, g, jsonify, request, send_file
from PIL import Image, ImageOps, UnidentifiedImageError
from prometheus_client import Counter
from sqlalchemy import or_

from . import db
from .messaging import MODELS, add_recipients, options, publish, require_access, serialize, target_column, valid_id, write_target
from .models import ChatAttachment, DirectConversation
from .routes import login_required


chat_tools = Blueprint("chat_tools", __name__)
MAX_FILE = 10 * 1024 * 1024
_uploads = BoundedSemaphore(2)
UPLOADS = Counter("chat_uploads_total", "Persisted chat attachments", ["scope"])
UPLOAD_BYTES = Counter("chat_upload_bytes_total", "Original bytes in persisted chat attachments")


def timestamp(value):
    return value.isoformat() if value else None


@chat_tools.get("/chat/<scope>/<int:target_id>/history")
@login_required
def history(scope, target_id):
    model = require_access(scope, target_id, g.current_user.id)
    values = {}
    for key in ("after", "before"):
        raw = request.args.get(key, "0")
        if not re.fullmatch(r"[0-9]{1,10}", raw) or int(raw) > 2_147_483_647:
            abort(400)
        values[key] = int(raw)
    if values["after"] and values["before"]:
        abort(400)
    statement = db.select(model).where(target_column(model, scope) == target_id).options(*options(model))
    if values["after"]:
        rows = db.session.scalars(statement.where(model.id > values["after"]).order_by(model.id).limit(100)).all()
    else:
        if values["before"]:
            statement = statement.where(model.id < values["before"])
        rows = list(reversed(db.session.scalars(statement.order_by(model.id.desc()).limit(100)).all()))
    permitted = True
    if scope == "direct":
        from .direct import can_send
        permitted = can_send(db.session.get(DirectConversation, target_id))
    return jsonify(messages=[serialize(row, scope) for row in rows], has_more=len(rows) == 100, can_send=permitted)


@chat_tools.post("/chat/<scope>/<int:target_id>/search")
@login_required
def search(scope, target_id):
    model = require_access(scope, target_id, g.current_user.id)
    query = request.form.get("q", "").strip()
    if not 1 <= len(query) <= 100:
        return {"error": "Nhập từ khóa từ 1 đến 100 ký tự."}, 400
    term = query.lower()
    rows = db.session.scalars(db.select(model).where(target_column(model, scope) == target_id, or_(
        db.func.lower(model.content).contains(term, autoescape=True),
        model.attachment.has(db.func.lower(ChatAttachment.filename).contains(term, autoescape=True)),
    )).options(*options(model)).order_by(model.id.desc()).limit(50)).all()
    return jsonify(messages=[serialize(row, scope) for row in rows], limit=50)


@chat_tools.post("/chat/<scope>/<int:target_id>/states")
@login_required
def states(scope, target_id):
    model = require_access(scope, target_id, g.current_user.id)
    raw_ids = request.form.getlist("message_ids")
    if not 1 <= len(raw_ids) <= 100 or any(not re.fullmatch(r"[0-9]{1,10}", value) or not valid_id(int(value)) for value in raw_ids):
        abort(400)
    rows = db.session.scalars(db.select(model).where(target_column(model, scope) == target_id,
        model.user_id == g.current_user.id, model.id.in_([int(value) for value in raw_ids])).options(*options(model))).all()
    from .messaging import summary
    return jsonify(states=[{"id": row.id, "summary": summary(row)} for row in rows])


@chat_tools.get("/chat/<scope>/<int:target_id>/messages/<int:message_id>/details")
@login_required
def details(scope, target_id, message_id):
    model = require_access(scope, target_id, g.current_user.id)
    if not valid_id(message_id):
        abort(404)
    message = db.session.scalar(db.select(model).where(target_column(model, scope) == target_id, model.id == message_id).options(*options(model)))
    if message is None:
        abort(404)
    author = message.user_id == g.current_user.id
    rows = message.receipts if author else [row for row in message.receipts if row.user_id == g.current_user.id]
    return jsonify(sent_at=timestamp(message.created_at), tracked=message.receipts_tracked, author=author,
        receipts=[{"name": row.user.label if row.user.profile_public else row.user.username, "user_id": row.user_id,
                   "delivered_at": timestamp(row.delivered_at), "seen_at": timestamp(row.seen_at)} for row in rows])


def clean_filename(value):
    name = value.replace("\\", "/").rsplit("/", 1)[-1]
    name = "".join(char for char in unicodedata.normalize("NFC", name) if unicodedata.category(char) not in {"Cc", "Cf", "Cs"}).strip(" .")
    return name[:180] or "tep-dinh-kem"


def image_preview(raw, filename):
    if filename.rsplit(".", 1)[-1].lower() not in {"png", "jpg", "jpeg", "webp"}:
        return None
    try:
        with Image.open(BytesIO(raw)) as image:
            if image.format not in {"PNG", "JPEG", "WEBP"} or image.width * image.height > 16_000_000:
                raise ValueError("image")
            image.load()
            sanitized = ImageOps.exif_transpose(image).convert("RGBA")
            sanitized.thumbnail((1600, 1600))
            output = BytesIO()
            sanitized.save(output, format="PNG")
            return output.getvalue()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        abort(400, "Ảnh không hợp lệ hoặc vượt 16 triệu điểm ảnh. Chọn JPG, PNG hoặc WebP khác.")


@chat_tools.post("/chat/<scope>/<int:target_id>/attachments")
@login_required
def upload(scope, target_id):
    # Check authorization before decoding or storing any user-supplied bytes.
    require_access(scope, target_id, g.current_user.id)
    if not _uploads.acquire(blocking=False):
        return {"error": "Đang xử lý hai tệp. Vui lòng thử lại sau."}, 429
    try:
        nonce = request.form.get("client_nonce", "")
        content = request.form.get("content", "").strip()
        if len(content) > 1000 or not re.fullmatch(r"[A-Za-z0-9_-]{16,64}", nonce):
            return {"error": "Nội dung hoặc mã gửi không hợp lệ."}, 400
        if len(request.files) != 1 or len(request.files.getlist("file")) != 1 or not request.files["file"].filename:
            return {"error": "Chọn một tệp cần gửi."}, 400
        file = request.files["file"]
        raw = file.stream.read(MAX_FILE + 1)
        if not raw:
            return {"error": "Không gửi tệp rỗng."}, 400
        if len(raw) > MAX_FILE:
            return {"error": "Mỗi tệp tối đa 10 MB (10 MiB)."}, 413
        name = clean_filename(file.filename)
        digest = hashlib.sha256(raw).hexdigest()
        model = write_target(scope, target_id, g.current_user.id)
        existing = db.session.scalar(db.select(model).where(target_column(model, scope) == target_id,
            model.user_id == g.current_user.id, model.client_nonce == nonce))
        if existing:
            attachment = existing.attachment
            if not attachment or existing.content != content or attachment.sha256 != digest or attachment.filename != name:
                return {"error": "Mã gửi đã dùng cho tin hoặc tệp khác."}, 409
            return {"ok": True, "message": serialize(existing, scope)}
        preview = image_preview(raw, name)
        message = model(user_id=g.current_user.id, client_nonce=nonce, content=content,
                        **{"room_id" if scope == "room" else "conversation_id": target_id})
        db.session.add(message)
        add_recipients(message, scope)
        message.attachment = ChatAttachment(id=str(uuid.uuid4()), filename=name, byte_size=len(raw), sha256=digest,
                                             data=raw, preview_data=preview, is_image=preview is not None)
        if scope == "direct":
            db.session.get(DirectConversation, target_id).updated_at = datetime.now(timezone.utc)
        db.session.commit()
        UPLOADS.labels(scope).inc(); UPLOAD_BYTES.inc(len(raw))
        if scope == "room":
            from .events import CHAT_MESSAGES
            CHAT_MESSAGES.inc()
        else:
            from .direct import DIRECT_MESSAGES
            DIRECT_MESSAGES.inc()
        # Never log filename, file contents, caption, or private download URLs.
        current_app.logger.info("chat_attachment_saved scope=%s target_id=%s message_id=%s bytes=%s", scope, target_id, message.id, len(raw))
        return {"ok": True, "message": publish(message, scope)}, 201
    finally:
        _uploads.release()


def authorized_attachment(attachment_id):
    attachment = db.get_or_404(ChatAttachment, attachment_id)
    scope = "room" if attachment.room_message_id is not None else "direct"
    message = db.session.get(MODELS[scope], attachment.room_message_id if scope == "room" else attachment.direct_message_id)
    require_access(scope, message.room_id if scope == "room" else message.conversation_id, g.current_user.id)
    return attachment


def file_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = "sandbox; default-src 'none'"
    response.headers["Cache-Control"] = "private, no-store"
    return response


@chat_tools.get("/attachments/<uuid:attachment_id>/download")
@login_required
def download(attachment_id):
    attachment = authorized_attachment(str(attachment_id))
    return file_headers(send_file(BytesIO(attachment.data), mimetype="application/octet-stream", as_attachment=True,
                                  download_name=attachment.filename, etag=False, max_age=0))


@chat_tools.get("/attachments/<uuid:attachment_id>/preview")
@login_required
def preview(attachment_id):
    attachment = authorized_attachment(str(attachment_id))
    if not attachment.is_image or not attachment.preview_data:
        abort(404)
    return file_headers(send_file(BytesIO(attachment.preview_data), mimetype="image/png", etag=False, max_age=0))


@chat_tools.app_errorhandler(413)
def too_large(error):
    return {"error": "Dữ liệu tải lên quá lớn. Mỗi tệp tối đa 10 MB (10 MiB)."}, 413
