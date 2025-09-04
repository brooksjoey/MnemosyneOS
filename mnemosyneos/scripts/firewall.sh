#!/usr/bin/env bash
# VPS Firewall Module
set -euo pipefail

echo "[Module] Configuring basic firewall rules..."
if command -v ufw &>/dev/null; then
  sudo ufw allow OpenSSH
  sudo ufw enable
  echo "UFW firewall enabled."
elif command -v firewall-cmd &>/dev/null; then
  sudo firewall-cmd --permanent --add-service=ssh
  sudo firewall-cmd --reload
  echo "firewalld rules applied."
else
  echo "[WARN] No supported firewall found."
fi
bash "$(dirname "$0")/../mnemosyneos/memory.sh" log "Firewall configured on $(date)"
