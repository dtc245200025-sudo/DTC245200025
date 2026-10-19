"""Generate real group/DM/upload and rejection events; never output credentials/content."""
from io import BytesIO
import json
import os
from pathlib import Path
import secrets
import time

import requests
import socketio

from verify_live_chat import BASE, csrf
from verify_notifications_live import login


def main():
    os.umask(0o077)
    values = dict(line.split(': ', 1) for line in Path(os.environ['DEMO_ACCESS_FILE']).read_text(encoding='utf-8').splitlines() if ': ' in line)
    marker = 'GD6_PRIVATE_CANARY_' + secrets.token_hex(12)
    evidence = {'start': str(time.time_ns()), 'canary': marker, 'messages': []}
    clients = [login(values, letter) for letter in ('A', 'B', 'C')]
    sockets = []
    try:
        for client in clients[:2]:
            sock = socketio.Client(http_session=client, reconnection=False)
            sock.connect(BASE, transports=['websocket'], wait_timeout=10); sockets.append(sock)
        for scope, key in (('room', 'Phong nhom'), ('direct', 'Chat rieng')):
            target_id = int(values[key].rsplit('/', 1)[1])
            result = sockets[0].call('send_message' if scope == 'room' else 'direct_send', {
                'room_id' if scope == 'room' else 'conversation_id': target_id,
                'client_nonce': secrets.token_hex(16), 'content': marker}, timeout=10)
            assert result['ok']
            evidence['messages'].append({'event': 'chat_message_saved' if scope == 'room' else 'direct_message_saved', 'id': result['message']['id']})
            assert sockets[1].call('message_receipt', {'scope': scope, 'target_id': target_id,
                'message_ids': [result['message']['id']], 'kind': 'seen'}, timeout=10)['ok']
            uploaded = clients[0].post(BASE + f'/chat/{scope}/{target_id}/attachments',
                data={'csrf_token': csrf(clients[0], '/profile'), 'content': marker, 'client_nonce': secrets.token_hex(16)},
                files={'file': (marker + '.txt', BytesIO(marker.encode()))}, timeout=15)
            assert uploaded.status_code == 201
            assert clients[2].get(BASE + f'/chat/{scope}/{target_id}/history', timeout=10).status_code == 404
        assert requests.get(BASE + '/healthz', params={'token': marker}, headers={'User-Agent': marker}, timeout=10).status_code == 200
        assert requests.get(BASE + '/' + marker, timeout=10).status_code == 404
        assert requests.get(BASE + '/metrics', timeout=10).status_code == 404
        Path(os.environ['LOGGING_EVIDENCE_FILE']).write_text(json.dumps(evidence), encoding='utf-8')
        print('LOGGING_ACTIVITY_OK: nhom/rieng/upload/receipt va chan quyen qua Nginx that')
    finally:
        for sock in sockets:
            if sock.connected: sock.disconnect()
        for client in clients: client.close()


if __name__ == '__main__': main()
