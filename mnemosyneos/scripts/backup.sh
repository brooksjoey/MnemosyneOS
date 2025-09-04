#!/usr/bin/env bash
# VPS Backup Module
set -euo pipefail

BACKUP_DIR="/var/backups/jb-vps"
mkdir -p "$BACKUP_DIR"

echo "[Module] Backing up /etc, /var/log, and home directories..."
sudo tar czf "$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).tar.gz" /etc /var/log /home || echo "[WARN] Some files may not be accessible."
bash "$(dirname "$0")/../mnemosyneos/memory.sh" log "Backup created on $(date)"
