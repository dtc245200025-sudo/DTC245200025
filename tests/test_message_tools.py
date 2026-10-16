from io import BytesIO
import re

from PIL import Image
import pytest
from sqlalchemy import event, text

from test_direct import people
from chatapp import create_app, db, socketio
from chatapp.models import ChatAttachment, DirectMessage, Message, MessageReceipt
from chatapp.chat_tools import MAX_FILE


@pytest.fixture(params=["room", "direct"])
def chat(people, request):
    app, alice, bob, carol = people
    if request.param == "room":
        alice.post("/rooms/create", data={"name": "Advanced room", "max_members": "10"})
        bob.post("/rooms/1/join")
    else:
        alice.post("/direct/start/2")
    return app, alice, bob, carol, request.param


def send(app, client, scope, content="Private receipt marker", nonce="0123456789abcdef"):
    sock = socketio.test_client(app, flask_test_client=client)
    target = {"room_id" if scope == "room" else "conversation_id": 1}
    result = sock.emit("send_message" if scope == "room" else "direct_send", {**target, "content": content, "client_nonce": nonce}, callback=True)
    sock.disconnect()
    assert result["ok"]
    return result["message"]


def ack(sock, scope, message_id=1, kind="delivered"):
    return sock.emit("message_receipt", {"scope": scope, "target_id": 1, "message_ids": [message_id], "kind": kind}, callback=True)


def upload(client, scope, raw=b"Demo attachment", name="report.txt", content="File caption", nonce="file0123456789abcdef"):
    return client.post(f"/chat/{scope}/1/attachments", data={"file": (BytesIO(raw), name), "content": content, "client_nonce": nonce})


def image_bytes():
    output = BytesIO()
    Image.new("RGB", (20, 10), (246, 211, 223)).save(output, format="PNG")
    return output.getvalue()


def test_receipts_only_recipient_and_first_times_are_stable(chat):
    app, alice, bob, carol, scope = chat
    message = send(app, alice, scope)
    assert message["receipt_summary"] == {"recipients": 1, "delivered": 0, "seen": 0}
    a, b, c = [socketio.test_client(app, flask_test_client=client) for client in (alice,bob,carol)]
    try:
        for sock in (a,b,c): sock.get_received()
        assert not ack(a, scope)["ok"] and not ack(c, scope)["ok"]
        assert ack(b, scope)["ok"]
        details = alice.get(f"/chat/{scope}/1/messages/1/details").json
        assert details["receipts"][0]["delivered_at"] and not details["receipts"][0]["seen_at"]
        first = details["receipts"][0]["delivered_at"]
        assert ack(b, scope, kind="seen")["ok"]
        updated = alice.get(f"/chat/{scope}/1/messages/1/details").json
        assert updated["receipts"][0]["delivered_at"] == first and updated["receipts"][0]["seen_at"]
        assert ack(b, scope, kind="seen")["ok"]
        assert alice.get(f"/chat/{scope}/1/messages/1/details").json == updated
        assert any(event["name"] == "receipt_updated" for event in a.get_received())
        assert not any(event["name"] == "receipt_updated" for event in c.get_received())
        assert carol.get(f"/chat/{scope}/1/messages/1/details").status_code == 404
        state = alice.post(f"/chat/{scope}/1/states", data={"message_ids": "1"}).json
        assert state["states"][0]["summary"] == {"recipients":1,"delivered":1,"seen":1}
        assert not bob.post(f"/chat/{scope}/1/states", data={"message_ids": "1"}).json["states"]
    finally:
        for sock in (a,b,c): sock.disconnect()


def test_seen_implies_delivery_and_not_online_status(chat):
    app, alice, bob, _, scope = chat
    b = socketio.test_client(app, flask_test_client=bob)
    try:
        message = send(app,alice,scope)
        assert message["receipt_summary"]["delivered"] == 0  # Online is not receipt.
        assert ack(b,scope,kind="seen")["ok"]
        row = alice.get(f"/chat/{scope}/1/messages/1/details").json["receipts"][0]
        assert row["delivered_at"] == row["seen_at"]
    finally: b.disconnect()


@pytest.mark.parametrize("data", [None, [], {}, {"scope": [], "target_id": 1, "kind": "seen", "message_ids": [1]},
    {"scope": "room", "target_id": True, "kind": "seen", "message_ids": [1]},
    {"scope": "room", "target_id": 1, "kind": [], "message_ids": [1]},
    {"scope": "room", "target_id": 1, "kind": "seen", "message_ids": [True]},
    {"scope": "room", "target_id": 1, "kind": "seen", "message_ids": list(range(1,102))}])
def test_invalid_receipts_are_rejected(people, data):
    app, alice, _, _ = people
    sock = socketio.test_client(app, flask_test_client=alice)
    try: assert not sock.emit("message_receipt",data,callback=True)["ok"]
    finally: sock.disconnect()


def test_snapshot_excludes_late_joiner_and_details_hide_other_receivers(people):
    app, alice,bob,carol = people
    alice.post("/rooms/create",data={"name":"Snapshot","max_members":"10"}); bob.post("/rooms/1/join")
    send(app,alice,"room")
    carol.post("/rooms/1/join")
    c = socketio.test_client(app,flask_test_client=carol)
    try:
        assert not ack(c,"room")["ok"]
        send(app,alice,"room","Second message","2123456789abcdef")
        details = bob.get("/chat/room/1/messages/2/details").json
        assert not details["author"] and [row["user_id"] for row in details["receipts"]] == [2]
        assert len(alice.get("/chat/room/1/messages/2/details").json["receipts"]) == 2
        assert not c.emit("message_receipt",{"scope":"room","target_id":1,"kind":"seen","message_ids":[1,2]},callback=True)["ok"]
        with app.app_context(): assert not db.session.scalar(db.select(MessageReceipt.seen_at).where(MessageReceipt.user_id == 3))
        bob.post("/rooms/1/leave")
        b = socketio.test_client(app,flask_test_client=bob)
        try: assert not ack(b,"room",2)["ok"]
        finally: b.disconnect()
    finally: c.disconnect()


def test_file_transfer_permission_retry_and_safe_download(chat):
    app,alice,bob,carol,scope = chat
    raw = b"<script>untrusted file</script>"
    response = upload(alice,scope,raw,"../../unsafe.html")
    assert response.status_code == 201
    message = response.json["message"]; attachment = message["attachment"]
    assert attachment["filename"] == "unsafe.html" and not attachment["is_image"]
    again = upload(alice,scope,raw,"../../unsafe.html")
    assert again.status_code == 200 and again.json["message"]["id"] == message["id"]
    assert upload(alice,scope,b"changed","../../unsafe.html").status_code == 409
    for client in (alice,bob):
        downloaded = client.get(attachment["download_url"])
        assert downloaded.status_code == 200 and downloaded.data == raw
        assert downloaded.mimetype == "application/octet-stream" and "attachment;" in downloaded.headers["Content-Disposition"]
        assert downloaded.headers["X-Content-Type-Options"] == "nosniff"
        assert "sandbox" in downloaded.headers["Content-Security-Policy"]
        assert "no-store" in downloaded.headers["Cache-Control"]
        assert client.get(attachment["download_url"].replace("download","preview")).status_code == 404
    assert carol.get(attachment["download_url"]).status_code == 404
    assert upload(carol,scope).status_code == 404
    assert app.test_client().get(attachment["download_url"]).status_code == 302
    with app.app_context(): assert db.session.scalar(db.select(db.func.count(ChatAttachment.id))) == 1


def test_verified_image_preview_and_no_binary_in_history_queries(chat):
    app,alice,bob,_,scope = chat
    response = upload(alice,scope,image_bytes(),"ảnh.png")
    assert response.status_code == 201
    attachment = response.json["message"]["attachment"]
    assert attachment["is_image"]
    preview = bob.get(attachment["preview_url"])
    assert preview.status_code == 200 and preview.mimetype == "image/png"
    assert Image.open(BytesIO(preview.data)).size == (20,10)
    with app.app_context():
        engine = db.engine; statements=[]
        def capture(connection,cursor,statement,parameters,context,executemany): statements.append(statement)
        event.listen(engine,"before_cursor_execute",capture)
    try:
        history = bob.get(f"/chat/{scope}/1/history")
        assert history.status_code == 200 and history.json["messages"][0]["attachment"]["id"] == attachment["id"]
        assert not any("chat_attachments.data" in statement or "chat_attachments.preview_data" in statement for statement in statements)
    finally: event.remove(engine,"before_cursor_execute",capture)


@pytest.mark.parametrize("raw,name,status", [(b"", "empty.txt",400),(b"not image","fake.png",400),(b"x"*(MAX_FILE+1),"large.bin",413)], ids=["empty","fake-image","oversize"])
def test_bad_and_oversized_uploads_do_not_create_messages(chat,raw,name,status):
    app,alice,_,_,scope=chat
    assert upload(alice,scope,raw,name).status_code == status
    with app.app_context():
        model = Message if scope == "room" else DirectMessage
        assert db.session.scalar(db.select(db.func.count(model.id))) == 0
        assert db.session.scalar(db.select(db.func.count(ChatAttachment.id))) == 0


def test_exact_ten_mib_boundary_and_caption_validation(chat):
    app,alice,_,_,scope=chat
    assert upload(alice,scope,b"a"*MAX_FILE,"boundary.bin").status_code == 201
    assert upload(alice,scope,b"ok","short.txt",content="x"*1001,nonce="1123456789abcdef").status_code == 400
    assert upload(alice,scope,b"ok","short.txt",nonce="bad").status_code == 400
    with app.app_context(): assert db.session.scalar(db.select(db.func.count(ChatAttachment.id))) == 1


def test_search_text_emoji_filename_and_no_access_leak(chat):
    app,alice,bob,carol,scope=chat
    send(app,alice,scope,"Xin chào 😊 tìm tin","0123456789abcdef")
    upload(alice,scope,b"demo","report-demo.txt",content="Attachment caption")
    for query in ("😊","Xin","report-demo"):
        response = bob.post(f"/chat/{scope}/1/search",data={"q":query})
        assert response.status_code == 200 and len(response.json["messages"]) == 1
    assert not bob.post(f"/chat/{scope}/1/search",data={"q":"%"}).json["messages"]
    assert carol.post(f"/chat/{scope}/1/search",data={"q":"Xin"}).status_code == 404
    assert alice.get(f"/chat/{scope}/1/search?q=Xin").status_code == 405
    assert alice.post(f"/chat/{scope}/1/search",data={"q":"x"*101}).status_code == 400
    path = "/rooms/1" if scope == "room" else "/direct/1"
    page = alice.get(path).text
    assert "chat-emoji-toggle" in page and "chat-file-picker" in page and "chat-search-input" in page


def test_download_after_leave_or_unfriend_matches_history_policy(chat):
    app,alice,bob,_,scope=chat
    result=upload(alice,scope); url=result.json["message"]["attachment"]["download_url"]
    if scope == "room":
        bob.post("/rooms/1/leave")
        assert bob.get(url).status_code == 404
        assert upload(bob,scope,nonce="1123456789abcdef").status_code == 404
    else:
        bob.post("/friends/1/remove")
        assert bob.get(url).status_code == 200  # Retained private history.
        assert upload(bob,scope,nonce="1123456789abcdef").status_code == 403


def test_csrf_guards_upload_search_and_state_requests(chat):
    app,alice,_,_,scope=chat
    app.config["WTF_CSRF_ENABLED"]=True
    assert upload(alice,scope).status_code == 400
    assert alice.post(f"/chat/{scope}/1/search",data={"q":"test"}).status_code == 400
    assert alice.post(f"/chat/{scope}/1/states",data={"message_ids":"1"}).status_code == 400


def test_group_text_retry_nonce_is_idempotent(people):
    app,alice,bob,_=people
    alice.post("/rooms/create",data={"name":"Retry room"}); bob.post("/rooms/1/join")
    first=send(app,alice,"room"); second=send(app,alice,"room")
    assert first["id"] == second["id"]
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Message.id))) == 1
        assert db.session.scalar(db.select(db.func.count(MessageReceipt.id))) == 1


def test_upgrade_retains_history_without_fake_receipts(tmp_path):
    config={"TESTING":True,"WTF_CSRF_ENABLED":False,"SECRET_KEY":"test","SQLALCHEMY_DATABASE_URI":f"sqlite:///{(tmp_path/'legacy.sqlite').as_posix()}"}
    app=create_app(config)
    from test_app import register_and_login
    client=app.test_client(); register_and_login(client)
    client.post("/rooms/create",data={"name":"Legacy room"})
    with app.app_context():
        db.session.add(Message(room_id=1,user_id=1,content="Keep old messages")); db.session.commit()
        with db.engine.begin() as connection:
            connection.execute(text("DROP INDEX uq_room_message_nonce"))
            connection.execute(text("ALTER TABLE messages DROP COLUMN client_nonce"))
            connection.execute(text("ALTER TABLE messages DROP COLUMN receipts_tracked"))
            connection.execute(text("ALTER TABLE direct_messages DROP COLUMN receipts_tracked"))
    upgraded=create_app(config); create_app(config)  # Idempotent upgrade.
    with upgraded.app_context():
        message=db.session.get(Message,1)
        assert message.content == "Keep old messages" and message.receipts_tracked is False
        assert db.session.scalar(db.select(db.func.count(MessageReceipt.id))) == 0
