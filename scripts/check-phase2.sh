#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

printf 'GIAI DOAN 2 - SOURCE VA FLASK\n'
printf 'Source: app/chatapp, app/Dockerfile, tests/test_app.py\n'
printf 'Database kiem thu: SQLite trong bo nho (PostgreSQL o Giai doan 3).\n\n'
docker compose -f compose.phase2.yml ps
docker compose -f compose.phase2.yml run --rm --no-deps -T \
  -v "$PWD/tests:/tests:ro" \
  app python -m pytest /tests -q -p no:cacheprovider
printf '\nFlask health: '
curl --fail --silent --show-error http://localhost:5000/healthz
printf '\nTrang dang nhap HTTP: '
curl --fail --silent --show-error -o /dev/null -w '%{http_code}\n' http://localhost:5000/login
printf '\nGIAI_DOAN_2_OK\n'
