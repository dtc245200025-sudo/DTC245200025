from io import BytesIO

from test_direct import people
from test_message_tools import chat, send, ack
from chatapp import db, socketio
from chatapp.models import DirectMessage, Message


def events(sock, name):
    return [event["args"][0] for event in sock.get_received() if event["name"] == name]


def test_notify_recipient_outside_chat_not_sender_or_outsider_and_no_retry_duplicate(chat):
    app, alice, bob, carol, scope = chat
    a, b, c = [socketio.test_client(app, flask_test_client=client) for client in (alice, bob, carol)]
    try:
        for sock in (a, b, c): sock.get_received()
        send(app, alice, scope, "<script>untrusted preview</script>")
        notices = events(b, "message_notification")
        assert len(notices) == 1
        assert notices[0]["scope"] == scope and notices[0]["target_id"] == 1
        assert notices[0]["preview"] == "<script>untrusted preview</script>"
        assert notices[0]["url"] == ("/rooms/1" if scope == "room" else "/direct/1")
        assert not events(a, "message_notification") and not events(c, "message_notification")
        send(app, alice, scope, "<script>untrusted preview</script>")
        assert not events(b, "message_notification")
    finally:
        for sock in (a, b, c): sock.disconnect()


def test_unread_persists_across_reconnect_and_only_seen_clears_all_recipient_tabs(chat):
    app, alice, bob, carol, scope = chat
    send(app, alice, scope)
    key = "rooms" if scope == "room" else "directs"
    for _ in range(2):
        assert bob.get("/notifications/state").json[key] == {"1": 1}
        assert alice.get("/notifications/state").json["total"] == 0
        assert carol.get("/notifications/state").json["total"] == 0
        assert bob.get("/notifications/state?user_id=1").json["total"] == 1
    b1, b2, c = [socketio.test_client(app, flask_test_client=client) for client in (bob, bob, carol)]
    try:
        assert events(b1, "unread_changed") == [{}]
        assert not events(b2, "message_notification")  # Reconnect doesn't replay popups.
        c.get_received()
        assert ack(b1, scope)["ok"]
        assert bob.get("/notifications/state").json["total"] == 1  # Delivered != seen.
        assert ack(b1, scope, kind="seen")["ok"]
        assert events(b2, "unread_changed") == [{}]
        assert not events(c, "unread_changed")
        assert bob.get("/notifications/state").json["total"] == 0
        assert "no-store" in bob.get("/notifications/state").headers["Cache-Control"]
    finally:
        for sock in (b1, b2, c): sock.disconnect()
    assert app.test_client().get("/notifications/state").status_code == 302


def test_group_leave_excludes_old_unread_and_stops_notifications(people):
    app, alice, bob, _ = people
    alice.post("/rooms/create", data={"name": "Notify room", "max_members": "10"})
    bob.post("/rooms/1/join")
    send(app, alice, "room")
    assert bob.get("/notifications/state").json["room_total"] == 1
    b = socketio.test_client(app, flask_test_client=bob)
    try:
        b.get_received()
        bob.post("/rooms/1/leave")
        assert events(b, "unread_changed") == [{}]
        assert bob.get("/notifications/state").json["total"] == 0
        send(app, alice, "room", "After leave", "2123456789abcdef")
        assert not events(b, "message_notification")
    finally: b.disconnect()


def test_attachment_generates_one_notice_with_safe_metadata(chat):
    app, alice, bob, _, scope = chat
    b = socketio.test_client(app, flask_test_client=bob)
    try:
        b.get_received()
        for expected_status in (201, 200):
            response = alice.post(f"/chat/{scope}/1/attachments", data={"file": (BytesIO(b"notice file"), "notes.txt"),
                "content": "", "client_nonce": "attachment1234567890"})
            assert response.status_code == expected_status
            notices = events(b, "message_notification")
            if expected_status == 201:
                assert len(notices) == 1 and notices[0]["preview"] == "Tệp: notes.txt"
                assert "data" not in notices[0] and "recipient_ids" not in notices[0]
            else: assert not notices
        assert bob.get("/notifications/state").json["total"] == 1
    finally: b.disconnect()


def test_legacy_history_is_not_fabricated_as_unread(chat):
    app, _, bob, _, scope = chat
    with app.app_context():
        model = Message if scope == "room" else DirectMessage
        values = {"room_id" if scope == "room" else "conversation_id": 1}
        db.session.add(model(**values, user_id=1, content="Old message", client_nonce="old12345678901234", receipts_tracked=False))
        db.session.commit()
    assert bob.get("/notifications/state").json["total"] == 0


def test_full_envelope_arrives_outside_chat_once_and_never_to_outsider(chat):
    app, alice, bob, carol, scope = chat
    b, c = [socketio.test_client(app, flask_test_client=client) for client in (bob, carol)]
    try:
        b.get_received(); c.get_received()
        text = "x" * 800  # Longer than the toast preview.
        sent = send(app, alice, scope, text)
        kind = "new_message" if scope == "room" else "direct_message"
        received = events(b, kind)
        assert len(received) == 1 and received[0]["content"] == text
        assert received[0]["id"] == sent["id"] and received[0]["recipient_ids"] == [2]
        assert not events(c, kind)
        # Subscribing to the active chat must not duplicate its personal envelope.
        assert b.emit("join" if scope == "room" else "direct_join",
            {"room_id" if scope == "room" else "conversation_id": 1}, callback=True)["ok"]
        b.get_received()
        send(app, alice, scope, "Next", "second12345678901234")
        assert len(events(b, kind)) == 1
    finally:
        b.disconnect(); c.disconnect()
