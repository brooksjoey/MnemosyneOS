#!/usr/bin/env bash
set -euo pipefail
sudo systemctl stop mnemosyneos || true
sudo systemctl disable mnemosyneos || true
sudo rm -f /etc/systemd/system/mnemosyneos.service
sudo systemctl daemon-reload
echo "Optionally remove data/logs: sudo rm -rf /var/lib/mnemosyneos /var/log/mnemosyneos"
