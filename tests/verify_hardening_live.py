"""Real HTTP/Socket.IO audit through Nginx, using synthetic fixtures only."""
import json
import os
from pathlib import Path
import time

import requests
import socketio

from verify_live_chat import BASE, csrf
from verify_notifications_live import login


def main():
    values = dict(line.split(': ', 1) for line in Path(os.environ['DEMO_ACCESS_FILE']).read_text(encoding='utf-8').splitlines() if ': ' in line)
    clients = [login(values, letter) for letter in ('A', 'B', 'C')]
    extra = login(values, 'A'); replay = requests.Session(); replay.cookies.update(clients[0].cookies)
    sockets = []
    try:
        page = clients[0].get(BASE + '/profile', timeout=10)
        assert page.status_code == 200 and 'no-store' in page.headers.get('Cache-Control', '')
        assert 'title="Đăng xuất tất cả phiên của tài khoản này"' in page.text
        # Flask may only send a cookie when a session changes; the login form generates a CSRF session cookie for guests.
        fresh = requests.Session(); response = fresh.get(BASE + '/login', timeout=10)
        cookie = response.headers.get('Set-Cookie', '')
        assert 'HttpOnly' in cookie and 'SameSite=Lax' in cookie and 'Secure' not in cookie
        fresh.close()
        expected_headers = {'X-Frame-Options': 'SAMEORIGIN', 'X-Content-Type-Options': 'nosniff',
                            'Referrer-Policy': 'strict-origin-when-cross-origin',
                            'Permissions-Policy': 'camera=(), microphone=(), geolocation=()'}
        for path in ('/healthz', '/metrics'):
            response = requests.get(BASE + path, timeout=10)
            assert response.status_code == (200 if path == '/healthz' else 404)
            assert all(response.headers.get(key) == value for key,value in expected_headers.items())
        print('[OK] 4security headers tren200/404; cookie HttpOnly/SameSite=Lax; trang ca nhan no-store')
        for path in ('/profile','/profile/password','/logout','/chat/room/' + values['Phong nhom'].rsplit('/',1)[1] + '/search'):
            assert clients[0].post(BASE + path, data={}, allow_redirects=False, timeout=10).status_code == 400
            assert clients[0].post(BASE + path, data={'csrf_token': 'invalid'}, allow_redirects=False, timeout=10).status_code == 400
        assert clients[0].get(BASE + '/profile', timeout=10).status_code == 200
        print('[OK] POST thieu/saiCSRF bi400; khong thay password/profile/logout')
        forged = requests.Session()
        for item in clients[0].cookies:
            forged.cookies.set(item.name, item.value + 'tampered', domain=item.domain, path=item.path)
        assert forged.get(BASE + '/profile', allow_redirects=False, timeout=10).status_code == 302
        forged.close()
        blocked = clients[0].get(BASE + '/socket.io/', params={'EIO': '4','transport':'polling'},
                                headers={'Origin':'https://untrusted.invalid'}, timeout=10)
        assert blocked.status_code == 400 and 'Access-Control-Allow-Origin' not in blocked.headers
        print('[OK] Cookie bi sua bi tu choi; Socket.IO chan Origin ngoai')
        for scope,key in (('room','Phong nhom'),('direct','Chat rieng')):
            target = values[key].rsplit('/',1)[1]
            assert clients[2].get(BASE + f'/chat/{scope}/{target}/history', timeout=10).status_code == 404
            assert clients[2].get(BASE + values[f'File {scope}'], timeout=10).status_code == 404
            good = clients[1].get(BASE + values[f'File {scope}'], timeout=10)
            assert good.status_code == 200 and good.headers['Content-Type'].startswith('application/octet-stream')
            assert good.headers['Content-Disposition'].startswith('attachment;') and good.headers['X-Content-Type-Options'] == 'nosniff'
        print('[OK] Nguoi ngoai khong doc history/file; file thuong attachment/octet-stream/nosniff')
        for client in (clients[0], extra, clients[1]):
            sock = socketio.Client(http_session=client, reconnection=False)
            sock.connect(BASE, transports=['websocket'], wait_timeout=10); sockets.append(sock)
        result = clients[0].post(BASE + '/logout', data={'csrf_token': csrf(clients[0], '/profile')}, allow_redirects=False, timeout=10)
        assert result.status_code == 302
        deadline = time.monotonic() + 5
        while (sockets[0].connected or sockets[1].connected) and time.monotonic() < deadline: time.sleep(.1)
        assert not sockets[0].connected and not sockets[1].connected and sockets[2].connected
        assert replay.get(BASE + '/profile', allow_redirects=False, timeout=10).status_code == 302
        assert extra.get(BASE + '/profile', allow_redirects=False, timeout=10).status_code == 302
        assert clients[1].get(BASE + '/profile', timeout=10).status_code == 200
        print('[OK] Logout thu hoi cookie cu/HTTP/socket cua A; B van truy cap va ket noi')
        proof = {'headers': True, 'csrf': True, 'cookie_tamper': True, 'socket_origin': True,
                 'private_access': True, 'download_headers': True, 'logout_revocation': True,
                 'tls': False, 'at': int(time.time())}
        path = Path(os.environ['HARDENING_EVIDENCE_FILE']); path.write_text(json.dumps(proof), encoding='utf-8'); path.chmod(0o600)
        print('HARDENING_LIVE_OK')
    finally:
        for sock in sockets:
            if sock.connected: sock.disconnect()
        for client in [*clients, extra, replay]: client.close()


if __name__ == '__main__': main()
