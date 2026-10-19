#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
printf 'GIAI DOAN 6 - LOKI VA PROMTAIL\n'
docker compose --profile monitoring --profile logging config --quiet
docker compose --profile monitoring --profile logging ps --format 'table {{.Service}}\t{{.Status}}\t{{.Ports}}'
python3 tests/verify_logging.py
python3 tests/verify_monitoring.py --with-logging
printf '\nBA MOC COMMIT\n'
git log --grep='^feat: milestone ' --format='%h %s'
