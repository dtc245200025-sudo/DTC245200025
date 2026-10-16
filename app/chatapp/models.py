from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from . import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    # Nullable only for accounts created before the email upgrade.
    email = db.Column(db.String(254), nullable=True)
    display_name = db.Column(db.String(80), nullable=True)
    bio = db.Column(db.String(150), nullable=False, default="", server_default="")
    profile_public = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())
    email_public = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    avatar_data = db.Column(db.LargeBinary, nullable=True)
    auth_version = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    __table_args__ = (db.Index("uq_users_email_lower", db.func.lower(email), unique=True),)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def label(self):
        return self.display_name or self.username

    @property
    def initials(self):
        parts = self.label.split()
        if len(parts) > 1:
            return (parts[0][0] + parts[-1][0]).upper()
        return self.label[:2].upper()


class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    visibility = db.Column(db.String(10), nullable=False, default="public", server_default="public")
    join_mode = db.Column(db.String(12), nullable=False, default="open", server_default="open")
    # NULL preserves unlimited capacity for legacy rooms; new Public rooms require a limit.
    max_members = db.Column(db.Integer, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    invite_token_hash = db.Column(db.String(64), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    @property
    def access_label(self):
        return {"open": "Vào tự do", "approval": "Chủ phòng phê duyệt", "password": "Mật khẩu", "invite": "Link mời"}.get(self.join_mode, "")


class RoomMember(db.Model):
    __tablename__ = "room_members"
    __table_args__ = (db.UniqueConstraint("room_id", "user_id"),)

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)


class Message(db.Model):
    __tablename__ = "messages"
    __table_args__ = (db.Index("uq_room_message_nonce", "room_id", "user_id", "client_nonce", unique=True),)

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = db.Column(db.String(1000), nullable=False)
    client_nonce = db.Column(db.String(64), nullable=True)
    receipts_tracked = db.Column(db.Boolean, nullable=False, default=True, server_default=db.false())
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    user = db.relationship("User")
    receipts = db.relationship("MessageReceipt", foreign_keys="MessageReceipt.room_message_id")
    attachment = db.relationship("ChatAttachment", foreign_keys="ChatAttachment.room_message_id", uselist=False)


class RoomJoinRequest(db.Model):
    __tablename__ = "room_join_requests"
    __table_args__ = (db.UniqueConstraint("room_id", "user_id"),)

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = db.Column(db.String(12), nullable=False, default="pending")
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    user = db.relationship("User")


class Friendship(db.Model):
    __tablename__ = "friendships"
    __table_args__ = (
        db.UniqueConstraint("user_low_id", "user_high_id", name="uq_friendship_pair"),
        db.CheckConstraint("user_low_id < user_high_id", name="ck_friendship_order"),
        db.CheckConstraint("requester_id = user_low_id OR requester_id = user_high_id", name="ck_friendship_requester"),
        db.CheckConstraint("status IN ('pending', 'accepted', 'declined', 'cancelled', 'removed')", name="ck_friendship_status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_low_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user_high_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = db.Column(db.String(12), nullable=False, default="pending", index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class DirectConversation(db.Model):
    __tablename__ = "direct_conversations"
    __table_args__ = (
        db.UniqueConstraint("user_low_id", "user_high_id", name="uq_direct_pair"),
        db.CheckConstraint("user_low_id < user_high_id", name="ck_direct_order"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_low_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user_high_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)


class DirectMessage(db.Model):
    __tablename__ = "direct_messages"
    __table_args__ = (
        db.UniqueConstraint("conversation_id", "user_id", "client_nonce", name="uq_direct_message_nonce"),
        db.Index("ix_direct_history", "conversation_id", "id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("direct_conversations.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    client_nonce = db.Column(db.String(64), nullable=False)
    content = db.Column(db.String(1000), nullable=False)
    receipts_tracked = db.Column(db.Boolean, nullable=False, default=True, server_default=db.false())
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    user = db.relationship("User")
    receipts = db.relationship("MessageReceipt", foreign_keys="MessageReceipt.direct_message_id")
    attachment = db.relationship("ChatAttachment", foreign_keys="ChatAttachment.direct_message_id", uselist=False)


class MessageReceipt(db.Model):
    __tablename__ = "message_receipts"
    __table_args__ = (
        db.CheckConstraint("(room_message_id IS NOT NULL AND direct_message_id IS NULL) OR (room_message_id IS NULL AND direct_message_id IS NOT NULL)", name="ck_receipt_message"),
        db.UniqueConstraint("room_message_id", "user_id", name="uq_room_receipt"),
        db.UniqueConstraint("direct_message_id", "user_id", name="uq_direct_receipt"),
    )
    id = db.Column(db.Integer, primary_key=True)
    room_message_id = db.Column(db.Integer, db.ForeignKey("messages.id", ondelete="CASCADE"), nullable=True, index=True)
    direct_message_id = db.Column(db.Integer, db.ForeignKey("direct_messages.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    delivered_at = db.Column(db.DateTime(timezone=True), nullable=True)
    seen_at = db.Column(db.DateTime(timezone=True), nullable=True)
    user = db.relationship("User")


class ChatAttachment(db.Model):
    __tablename__ = "chat_attachments"
    __table_args__ = (
        db.CheckConstraint("(room_message_id IS NOT NULL AND direct_message_id IS NULL) OR (room_message_id IS NULL AND direct_message_id IS NOT NULL)", name="ck_attachment_message"),
        db.CheckConstraint("byte_size > 0 AND byte_size <= 10485760", name="ck_attachment_size"),
    )
    id = db.Column(db.String(36), primary_key=True)
    room_message_id = db.Column(db.Integer, db.ForeignKey("messages.id", ondelete="CASCADE"), nullable=True, unique=True)
    direct_message_id = db.Column(db.Integer, db.ForeignKey("direct_messages.id", ondelete="CASCADE"), nullable=True, unique=True)
    filename = db.Column(db.String(180), nullable=False)
    byte_size = db.Column(db.Integer, nullable=False)
    sha256 = db.Column(db.String(64), nullable=False)
    # Original bytes only load on authorized download, never in history queries.
    data = db.deferred(db.Column(db.LargeBinary, nullable=False))
    preview_data = db.deferred(db.Column(db.LargeBinary, nullable=True))
    is_image = db.Column(db.Boolean, nullable=False, default=False)
