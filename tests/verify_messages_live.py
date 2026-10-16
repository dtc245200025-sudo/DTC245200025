"""Actual PostgreSQL/HTTP/WebSocket checks for message receipts and files."""

import hashlib
from io import BytesIO
import os
import queue
import re
import secrets
import time

from PIL import Image
import socketio

from verify_live_chat import BASE, account, csrf
from verify_friends_live import post, drain


def wait(inbox, predicate):
    deadline=time.monotonic()+10
    while time.monotonic()<deadline:
        event=inbox.get(timeout=max(.1,deadline-time.monotonic()))
        if predicate(event): return event[1]
    raise AssertionError("Expected realtime event not received")


def main():
    tag=secrets.token_hex(3); password=secrets.token_urlsafe(24)
    names=[f"messages34_{letter}_{tag}" for letter in ("a","b","c")]
    clients=[account(name,password) for name in names]; alice,bob,carol=clients
    ids=[int(re.search(r'data-presence-user="(\d+)"',client.get(BASE+"/profile",timeout=10).text).group(1)) for client in clients]
    a_id,b_id,c_id=ids
    for client,label in zip(clients,("Linh","Minh Anh","Người kiểm thử")):
        assert post(client,"/profile",{"display_name":label,"bio":"","profile_public":"on"}).status_code==302
    post(alice,f"/friends/{b_id}/request"); post(bob,f"/friends/{a_id}/accept")
    direct_path=post(alice,f"/direct/start/{b_id}").headers["Location"]
    room_path=post(alice,"/rooms/create",{"name":f"GD3.4b LinhChat {tag}","max_members":"10"}).headers["Location"]
    assert post(bob,room_path+"/join").status_code==302
    targets={"room":int(room_path.rsplit("/",1)[1]),"direct":int(direct_path.rsplit("/",1)[1])}
    output=BytesIO(); Image.new("RGB",(160,100),(246,211,223)).save(output,format="PNG"); png=output.getvalue()
    sockets=[]; inboxes=[queue.Queue() for _ in clients]; downloads={}
    try:
        for client,inbox in zip(clients,inboxes):
            sock=socketio.Client(http_session=client,reconnection=False)
            for kind in ("new_message","direct_message","receipt_updated"):
                sock.on(kind,lambda body,event=kind,target=inbox:target.put((event,body)))
            sock.connect(BASE,transports=["websocket"],wait_timeout=10); sockets.append(sock)
        for scope,target_id in targets.items():
            target={"room_id" if scope=="room" else "conversation_id":target_id}
            event_name="new_message" if scope=="room" else "direct_message"
            join_name="join" if scope=="room" else "direct_join"
            send_name="send_message" if scope=="room" else "direct_send"
            for sock in sockets[:2]: assert sock.call(join_name,target,timeout=10)["ok"]
            assert not sockets[2].call(join_name,target,timeout=10)["ok"]
            for inbox in inboxes: drain(inbox)
            nonce=secrets.token_hex(16)
            body={**target,"content":f"[GD3.4b {tag}] Xin chào 😊 {scope}","client_nonce":nonce}
            sent=sockets[0].call(send_name,body,timeout=10); assert sent["ok"]
            message=sent["message"]; message_id=message["id"]
            assert message["receipt_summary"]=={"recipients":1,"delivered":0,"seen":0}
            wait(inboxes[1],lambda event:event[0]==event_name and event[1]["id"]==message_id)
            receipt={"scope":scope,"target_id":target_id,"message_ids":[message_id],"kind":"delivered"}
            assert sockets[1].call("message_receipt",receipt,timeout=10)["ok"]
            wait(inboxes[0],lambda event:event[0]=="receipt_updated" and event[1]["message_id"]==message_id and event[1]["summary"]["delivered"]==1)
            assert sockets[1].call("message_receipt",{**receipt,"kind":"seen"},timeout=10)["ok"]
            wait(inboxes[0],lambda event:event[0]=="receipt_updated" and event[1]["message_id"]==message_id and event[1]["summary"]["seen"]==1)
            assert not sockets[2].call("message_receipt",receipt,timeout=10)["ok"]
            detail_url=f"/chat/{scope}/{target_id}/messages/{message_id}/details"
            details=alice.get(BASE+detail_url,timeout=10).json()
            assert details["receipts"][0]["delivered_at"] and details["receipts"][0]["seen_at"]
            assert carol.get(BASE+detail_url,timeout=10).status_code==404
            assert sockets[0].call(send_name,body,timeout=10)["message"]["id"]==message_id
            print(f"[OK] {scope}: gui/nhan/xem realtime, thoi gian that va chong gui trung")

            raw=f"LinhChat GD3.4b file evidence {tag} {scope}\n".encode()
            file_nonce=secrets.token_hex(16)
            file_values={"content":"Tệp minh chứng LinhChat","client_nonce":file_nonce,"csrf_token":csrf(alice,"/profile")}
            upload_url=BASE+f"/chat/{scope}/{target_id}/attachments"
            result=alice.post(upload_url,data=file_values,files={"file":(f"demo-{tag}-{scope}.txt",raw,"text/plain")},timeout=30)
            assert result.status_code==201
            file_message=result.json()["message"]; attachment=file_message["attachment"]
            wait(inboxes[1],lambda event:event[0]==event_name and event[1]["id"]==file_message["id"])
            retried=alice.post(upload_url,data=file_values,files={"file":(f"demo-{tag}-{scope}.txt",raw,"text/plain")},timeout=30)
            assert retried.status_code==200 and retried.json()["message"]["id"]==file_message["id"]
            downloaded=bob.get(BASE+attachment["download_url"],timeout=10)
            assert downloaded.status_code==200 and downloaded.content==raw
            assert downloaded.headers["Content-Type"].startswith("application/octet-stream")
            assert "attachment;" in downloaded.headers["Content-Disposition"] and downloaded.headers["X-Content-Type-Options"]=="nosniff"
            assert carol.get(BASE+attachment["download_url"],timeout=10).status_code==404
            assert sockets[1].call("message_receipt",{**receipt,"message_ids":[file_message["id"]]},timeout=10)["ok"]
            downloads[scope]=(attachment["download_url"],hashlib.sha256(raw).hexdigest())
            image_result=bob.post(upload_url,data={"content":"Ảnh thử giao diện hồng phấn 🌸","client_nonce":secrets.token_hex(16),"csrf_token":csrf(bob,"/profile")},
                                  files={"file":("linhchat-demo.png",png,"image/png")},timeout=30)
            assert image_result.status_code==201
            image=image_result.json()["message"]
            preview=alice.get(BASE+image["attachment"]["preview_url"],timeout=10)
            assert preview.status_code==200 and Image.open(BytesIO(preview.content)).size==(160,100)
            assert sockets[0].call("message_receipt",{**receipt,"message_ids":[image["id"]],"kind":"seen"},timeout=10)["ok"]
            search=post(bob,f"/chat/{scope}/{target_id}/search",{"q":"😊"})
            assert search.status_code==200 and any(item["id"]==message_id for item in search.json()["messages"])
            search=post(bob,f"/chat/{scope}/{target_id}/search",{"q":f"demo-{tag}-{scope}"})
            assert search.status_code==200 and len(search.json()["messages"])==1
            assert post(carol,f"/chat/{scope}/{target_id}/search",{"q":"😊"}).status_code==404
            before=len(alice.get(BASE+f"/chat/{scope}/{target_id}/history",timeout=10).json()["messages"])
            large=alice.post(upload_url,data={"client_nonce":secrets.token_hex(16),"csrf_token":csrf(alice,"/profile")},
                             files={"file":("oversized.bin",b"x"*(10*1024*1024+1))},timeout=30)
            assert large.status_code==413
            after=len(alice.get(BASE+f"/chat/{scope}/{target_id}/history",timeout=10).json()["messages"])
            assert before==after
            assert alice.post(upload_url,data={"client_nonce":secrets.token_hex(16)},files={"file":("no-csrf.txt",b"test")},timeout=10).status_code==400
            print(f"[OK] {scope}: tep/anh, download dung byte/dung quyen, tim text/emoji/ten tep; chan >10 MiB va CSRF")

        try:
            inboxes[2].get(timeout=.5)
            raise AssertionError("Unrelated user received message/receipt events")
        except queue.Empty: pass
        path=os.environ.get("DEMO_ACCESS_FILE")
        if path:
            descriptor=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(descriptor,"w",encoding="utf-8") as stream:
                stream.write("GD3.4b - Chi xem rieng tren VM, khong chup mat khau.\n")
                for letter,name in zip(("A","B","C"),names): stream.write(f"Tai khoan {letter}: {name}\n")
                stream.write(f"Mat khau chung: {password}\nChat rieng: {direct_path}\nPhong nhom: {room_path}\n")
                for scope,(download,digest) in downloads.items(): stream.write(f"File {scope}: {download}\nSHA {scope}: {digest}\n")
            print("[OK] Luu tai khoan va du lieu minh chung rieng tren VM, quyen 600")
        print("MESSAGES34B_LIVE_CHECK_OK")
    finally:
        for sock in sockets:
            if sock.connected: sock.disconnect()
        for client in clients: client.close()


if __name__=="__main__": main()
