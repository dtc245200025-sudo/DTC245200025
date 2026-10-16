#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
printf 'GIAI DOAN 4 - NGINX REVERSE PROXY\n'
docker compose config --quiet
docker compose exec -T nginx nginx -t
printf '\nHTTP VA SECURITY HEADERS\n'
task_headers="$(curl --fail --silent --show-error --head http://localhost/healthz)"
printf '%s\n' "$task_headers" | tr -d '\r' | sed -n -E '/^(HTTP\/|Server:|X-Frame-Options:|X-Content-Type-Options:|Referrer-Policy:|Permissions-Policy:)/Ip'
for task_header in X-Frame-Options X-Content-Type-Options Referrer-Policy Permissions-Policy; do
  printf '%s\n' "$task_headers" | grep -qi "^${task_header}:"
done
printf '\nCAC CONTAINER\n'
docker compose ps --format 'table {{.Service}}\t{{.Status}}\t{{.Ports}}'
task_app="$(docker compose ps -q app)"
task_db="$(docker compose ps -q postgres)"
test "$(docker inspect --format '{{len .HostConfig.PortBindings}}' "$task_app")" = 0
test "$(docker inspect --format '{{len .HostConfig.PortBindings}}' "$task_db")" = 0
if curl --silent --max-time 2 http://127.0.0.1:5000/healthz > /dev/null; then
  printf 'LOI: cong app 5000 van dang mo\n'; exit 1
fi
printf '\n[OK] App :5000 va PostgreSQL :5432 khong published ra host\n'
for task_path in metrics nginx_status; do
  test "$(curl --silent --output /dev/null --write-out '%{http_code}' "http://localhost/${task_path}")" = 404
done
printf '[OK] /metrics va /nginx_status bi chan tren cong web\n'
test "$(curl --silent --output /dev/null --write-out '%{http_code}' http://localhost:5050/login)" = 200
printf '[OK] pgAdmin localhost:5050 van hoat dong\n'
if git rev-parse --verify HEAD > /dev/null 2>&1; then
  printf '\nMOC COMMIT DA LUU\n'
  git log -1 --format='%h %s'
fi
printf '\nGIAI_DOAN_4_OK\n'
