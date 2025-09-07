#!/usr/bin/env bash
# JB-VPS Enterprise Bootstrap Script
# One-command setup for a new VPS
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}" )" && pwd)"
LOG_FILE="/var/log/jb-vps-setup.log"
MENU_SCRIPT="$REPO_ROOT/menu/main_menu.sh"
MNEMOSYNEOS_SCRIPT="$REPO_ROOT/mnemosyneos/memory.sh"

log() { echo "[JB-VPS] $*" | tee -a "$LOG_FILE"; }

log "Starting JB-VPS setup at $(date) on $(hostname)"

# 1. Detect OS and install dependencies
if [ -f "$REPO_ROOT/core/os_detect.sh" ]; then
  source "$REPO_ROOT/core/os_detect.sh"
else
  log "OS detection script missing. Skipping."
fi

# 2. Create admin user and set up environment
if [ -f "$REPO_ROOT/core/user_setup.sh" ]; then
  sudo bash "$REPO_ROOT/core/user_setup.sh"
else
  log "User setup script missing. Skipping."
fi

# 3. Run all modules
for mod in "$REPO_ROOT/modules/"*.sh; do
  [ -f "$mod" ] && bash "$mod"
done

# 4. Start menu system
if [ -f "$MENU_SCRIPT" ]; then
  bash "$MENU_SCRIPT"
else
  log "Menu system not found. Skipping."
fi

# 5. Start mnemosyneos (memory/log/history)
if [ -f "$MNEMOSYNEOS_SCRIPT" ]; then
  bash "$MNEMOSYNEOS_SCRIPT"
else
  log "Mnemosyneos module not found. Skipping."
fi

log "JB-VPS setup complete."
