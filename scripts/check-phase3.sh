#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

printf 'GIAI DOAN 3 - CHAT VA POSTGRESQL\n'
docker compose -f compose.yml -f compose.phase3.yml ps
printf '\nFlask ket noi database: '
curl --fail --silent --show-error http://localhost:5000/healthz
printf '\npgAdmin HTTP: '
curl --fail --silent --show-error -o /dev/null -w '%{http_code}\n' http://localhost:5050/login
docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U postgres -d chatdb -f - < scripts/evidence-gd3.sql
printf '\nGIAI_DOAN_3_OK\n'
