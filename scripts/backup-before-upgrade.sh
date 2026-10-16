#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
umask 077
mkdir -p work/backups
task_tag="$(date +%Y%m%d-%H%M%S)"
task_prefix="work/backups/before-phase31-${task_tag}"
docker compose exec -T postgres pg_dump -U postgres -d chatdb -Fc > "${task_prefix}.dump"
tar -czf "${task_prefix}-source.tgz" app tests compose.yml compose.phase3.yml .env.example .gitignore README.md
test -s "${task_prefix}.dump"
test -s "${task_prefix}-source.tgz"
printf 'BACKUP_OK: %s (database va source; khong in du lieu rieng tu)\n' "$task_prefix"
