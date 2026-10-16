#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
printf 'GIAI DOAN 3.1 - TAI KHOAN EMAIL VA GIAO DIEN\n'
docker compose -f compose.yml -f compose.phase3.yml run --rm --no-deps -T \
  -v "$PWD/tests:/tests:ro" app python -m pytest /tests -q -p no:cacheprovider
printf '\nFlask health: '
curl --fail --silent --show-error http://localhost:5000/healthz
printf '\n'
docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U postgres -d chatdb -f - < scripts/evidence-phase31.sql
printf '\nGIAI_DOAN_31_OK\n'
