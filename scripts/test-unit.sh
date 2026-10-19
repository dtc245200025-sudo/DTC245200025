#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
task_container="$(docker compose ps -q app)"
test -n "$task_container"
task_image="$(docker inspect --format '{{.Image}}' "$task_container")"
# Separate temporary container, no network, .env or PostgreSQL volume.
docker run --rm --network none --read-only \
  --tmpfs /tmp:size=128m,noexec,nosuid \
  --mount "type=bind,src=$PWD/app,dst=/srv/app,readonly" \
  --mount "type=bind,src=$PWD/tests,dst=/srv/tests,readonly" \
  --workdir /srv --entrypoint python "$task_image" \
  -m pytest -q -p no:cacheprovider /srv/tests
