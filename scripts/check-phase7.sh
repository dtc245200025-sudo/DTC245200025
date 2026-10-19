#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
printf 'GIAI DOAN 7 - HARDENING LINHCHAT\n'
python3 tests/verify_hardening.py
printf '\nHTTP VA SECURITY HEADERS\n'
curl --fail --silent --head http://localhost/healthz | tr -d '\r' |
  sed -n -E '/^(HTTP\/|X-Frame-Options:|X-Content-Type-Options:|Referrer-Policy:|Permissions-Policy:)/Ip'
python3 - <<'PY'
import json
import subprocess
import hashlib
from pathlib import Path
data=json.loads(Path('work/hardening-live.json').read_text())
assert all(data[key] for key in ('headers','csrf','cookie_tamper','socket_origin','private_access','download_headers','logout_revocation'))
assert not data['tls']
container=subprocess.check_output(['docker','compose','ps','-q','app'],text=True).strip()
image=json.loads(subprocess.check_output(['docker','inspect',container],text=True))[0]['Image']
assert data['app_image']==image, 'App image changed; rerun live audit before using saved evidence'
assert data['nginx_config']==hashlib.sha256(Path('nginx/nginx.conf').read_bytes()).hexdigest(), 'Nginx config changed; rerun live audit'
print('[EVIDENCE] HTTP/WebSocket da chay dat: CSRF, cookie, Origin, quyen, logout; day la ket qua lan test da luu')
PY
printf '\nGIAI_DOAN_7_OK\n'
