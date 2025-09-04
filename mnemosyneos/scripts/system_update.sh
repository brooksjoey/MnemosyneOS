#!/usr/bin/env bash
# System Update Module
set -euo pipefail

echo "[Module] Updating system packages..."
if [[ -f /etc/os-release ]]; then
  . /etc/os-release
  case "$ID" in
    ubuntu|debian)
      sudo apt update && sudo apt upgrade -y
      ;;
    centos|fedora|rhel)
      sudo yum update -y
      ;;
    *)
      echo "[WARN] Unsupported OS for auto-update."
      ;;
  esac
else
  echo "[WARN] Cannot detect OS. Skipping update."
fi
bash "$(dirname "$0")/../mnemosyneos/memory.sh" log "System updated on $(date)"
