#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
printf 'GIAI DOAN 8 - KIEM TRA BAN GIAO LINHCHAT (HINH 13)\n'
docker compose --profile monitoring --profile logging config --quiet
python3 tests/verify_delivery.py
