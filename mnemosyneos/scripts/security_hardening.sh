#!/usr/bin/env bash
# Security Hardening Module
set -euo pipefail

echo "[Module] Applying security hardening..."
# Example: Disable root SSH login
if [[ -f /etc/ssh/sshd_config ]]; then
  sudo sed -i 's/^PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
  sudo systemctl restart sshd
  echo "Root SSH login disabled."
else
  echo "[WARN] sshd_config not found."
fi
bash "$(dirname "$0")/../mnemosyneos/memory.sh" log "Security hardening applied on $(date)"
