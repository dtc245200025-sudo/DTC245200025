#!/usr/bin/env bash
set -euo pipefail

base_url="${BASE_URL:-http://localhost}"

docker compose --profile monitoring --profile logging ps
curl --fail --silent --show-error "$base_url/healthz"
curl --fail --silent --show-error "http://localhost:9090/-/healthy"
curl --fail --silent --show-error "http://localhost:3000/api/health"
printf '\nSmoke test dat.\n'
