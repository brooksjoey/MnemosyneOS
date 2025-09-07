#!/usr/bin/env bash
# VPS Monitoring Module
set -euo pipefail

echo "[Module] System resource usage:"
free -h
uptime
ps aux --sort=-%mem | head -n 10
bash "$(dirname "$0")/../mnemosyneos/memory.sh" log "Monitoring run on $(date)"
