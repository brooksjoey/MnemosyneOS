#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${1:-$PWD}"

sudo useradd -r -s /usr/sbin/nologin mnemo || true
sudo mkdir -p /opt/mnemosyneos /var/lib/mnemosyneos /var/log/mnemosyneos /etc/mnemosyneos
sudo chown -R mnemo:mnemo /var/lib/mnemosyneos /var/log/mnemosyneos

# Sync code
sudo rsync -a --delete "$REPO_DIR"/ /opt/mnemosyneos/

# Python venv + deps
sudo -u mnemo bash -lc '
  cd /opt/mnemosyneos
  python3 -m venv .venv
  . .venv/bin/activate
  python -m pip install --upgrade pip
  pip install -r "MnemosyneOS/Mnemosyne - main/services/mnemo/requirements.txt"
'

# Env file
if [ ! -f /etc/mnemosyneos/.env ]; then
  sudo cp "/opt/mnemosyneos/MnemosyneOS/Mnemosyne - main/config/.env.example" /etc/mnemosyneos/.env
fi
sudo chown mnemo:mnemo /etc/mnemosyneos/.env

# Systemd unit
sudo cp "/opt/mnemosyneos/MnemosyneOS/Mnemosyne - main/packaging/systemd/mnemosyneos.service" /etc/systemd/system/mnemosyneos.service
sudo systemctl daemon-reload
sudo systemctl enable mnemosyneos.service

echo "Install complete."
echo "Start the service with: sudo systemctl start mnemosyneos"
echo "Check status with:     sudo systemctl status mnemosyneos"