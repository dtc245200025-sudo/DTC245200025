#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
printf 'GIAI DOAN 5 - PROMETHEUS VA GRAFANA\n'
docker compose --profile monitoring config --quiet
docker compose --profile monitoring ps --format 'table {{.Service}}\t{{.Status}}\t{{.Ports}}'
python3 tests/verify_monitoring.py
printf '\nMOC COMMIT\n'
git log -2 --format='%h %s'
