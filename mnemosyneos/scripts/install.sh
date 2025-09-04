#!/usr/bin/env bash
set -euo pipefail
REPO_DIR="${1:-$PWD}"
sudo mkdir -p /opt/mnemosyneos /var/lib/mnemosyneos /var/log/mnemosyneos /etc/mnemosyneos
sudo rsync -a --delete "$REPO_DIR"/ /opt/mnemosyneos/
if [ ! -f /etc/mnemosyneos/.env ]; then
  sudo cp /opt/mnemosyneos/config/.env.example /etc/mnemosyneos/.env
fi
sudo cp /opt/mnemosyneos/packaging/systemd/mnemosyneos.service /etc/systemd/system/mnemosyneos.service
sudo systemctl daemon-reload && sudo systemctl enable mnemosyneos.service
echo "Start with: sudo systemctl start mnemosyneos"
