#!/usr/bin/env bash
set -euo pipefail

if [[ "$EUID" -ne 0 ]]; then
  printf 'Chay script nay bang sudo bash scripts/install-docker-ubuntu.sh\n' >&2
  exit 1
fi
. /etc/os-release
[[ "$ID" == ubuntu ]] || { printf 'Script chi danh cho Ubuntu.\n'; exit 1; }
task_user="${SUDO_USER:-}"
[[ -n "$task_user" && "$task_user" != root ]] || { printf 'Hay chay sudo tu tai khoan Ubuntu thuong.\n'; exit 1; }
id "$task_user" >/dev/null

for package in docker.io docker-compose docker-compose-v2 docker-doc docker-buildx podman-docker containerd runc; do
  if dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q '^install ok installed$'; then
    printf 'Phat hien goi co the xung dot: %s. Dung de kiem tra, khong tu go cai dat.\n' "$package" >&2
    exit 1
  fi
done

apt-get update
apt-get install -y ca-certificates curl git openssl
install -m 0755 -d /etc/apt/keyrings
curl --fail --show-error --location --retry 3 --max-time 60 \
  https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
task_arch="$(dpkg --print-architecture)"
task_codename="${UBUNTU_CODENAME:-$VERSION_CODENAME}"
printf 'Types: deb\nURIs: https://download.docker.com/linux/ubuntu\nSuites: %s\nComponents: stable\nArchitectures: %s\nSigned-By: /etc/apt/keyrings/docker.asc\n' \
  "$task_codename" "$task_arch" > /etc/apt/sources.list.d/docker.sources

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker
usermod -aG docker "$task_user"

git --version
docker --version
docker compose version
docker info --format 'Docker daemon {{.ServerVersion}}'
docker run --rm hello-world
printf '\nGIAI_DOAN_1_INSTALL_OK\n'
printf 'Tai khoan %s da vao nhom docker. Phien SSH moi se nhan quyen nay.\n' "$task_user"
printf 'Trong Terminal Ubuntu hien tai, chay newgrp docker roi bash scripts/check-ubuntu.sh de chup minh chung.\n'
