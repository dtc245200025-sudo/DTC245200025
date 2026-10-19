#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Uses only existing synthetic A/B/C fixtures; no credentials printed.
docker run --rm --network de32-chat_observability --user "$(id -u):$(id -g)" \
  -e BASE_URL=http://nginx:8080 -e DEMO_ACCESS_FILE=/evidence/gd34b-demo-access.txt \
  -e LOGGING_EVIDENCE_FILE=/evidence/logging-evidence.json \
  -v "$PWD/work:/evidence" de32-chat-live-check python -u verify_logging_activity.py
chmod 600 work/logging-evidence.json
python3 tests/verify_logging.py
