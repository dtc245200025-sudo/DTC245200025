#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ -e .env ]]; then
  printf '.env da ton tai; giu nguyen, khong ghi de.\n'
  exit 0
fi
command -v openssl >/dev/null || { printf 'Can cai openssl truoc.\n'; exit 1; }
umask 077
secret() { openssl rand -hex 24; }
{
  printf 'POSTGRES_DB=chatdb\nPOSTGRES_USER=postgres\n'
  printf 'POSTGRES_PASSWORD=%s\n' "$(secret)"
  printf 'APP_DB_USER=chatuser\nAPP_DB_PASSWORD=%s\n' "$(secret)"
  printf 'POSTGRES_EXPORTER_PASSWORD=%s\n' "$(secret)"
  printf 'SECRET_KEY=%s\n' "$(secret)"
  printf 'PGADMIN_DEFAULT_EMAIL=admin@example.com\nPGADMIN_DEFAULT_PASSWORD=%s\n' "$(secret)"
  printf 'GRAFANA_ADMIN_USER=admin\nGRAFANA_ADMIN_PASSWORD=%s\n' "$(secret)"
  printf 'BIND_ADDRESS=0.0.0.0\nADMIN_BIND_ADDRESS=127.0.0.1\n'
} > .env
printf 'Da tao .env voi secret rieng. Khong chup anh/noi dung .env.\n'
