#!/usr/bin/env bash
set -uo pipefail

if [[ ! -f /etc/os-release ]]; then
  printf 'Script nay phai chay trong Terminal Ubuntu VMware.\n'
  exit 1
fi

failures=0
check() {
  local label="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    printf '[OK] %s\n' "$label"
  else
    printf '[THIEU] %s\n' "$label"
    failures=$((failures + 1))
  fi
}

printf 'He dieu hanh: '
. /etc/os-release && printf '%s %s\n' "$NAME" "$VERSION_ID"
if [[ "$ID" != ubuntu ]]; then
  printf 'Can kiem tra lai: he dieu hanh hien tai khong phai Ubuntu.\n'
  failures=$((failures + 1))
fi
printf 'Tai nguyen:\n'
printf '  CPU: %s\n' "$(nproc)"
free -h | awk '/Mem:/ {print "  RAM: "$2}'
df -h / | awk 'NR==2 {print "  Disk /: "$4" free"}'

check 'Git' git --version
check 'Docker Engine' docker --version
check 'Docker Compose plugin' docker compose version
check 'Docker daemon access' docker info
check 'OpenSSL tao secret' openssl version
printf 'Dia chi IP: %s\n' "$(hostname -I)"

if (( failures > 0 )); then
  printf '\nCan xu ly %s muc truoc khi chay project.\n' "$failures"
  exit 1
fi

printf '\nMoi cong cu nen da san sang.\n'
