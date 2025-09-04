#!/usr/bin/env bash
# Mnemosyneos: Memory/Log/History System
set -euo pipefail

# Try to use JB logging if available; fallback to system, then user
JB_DIR="${JB_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
if [[ -f "$JB_DIR/lib/base.sh" ]]; then
  # shellcheck disable=SC1091
  source "$JB_DIR/lib/base.sh"
fi

choose_log_file() {
  local base_dir="${JB_LOG_DIR:-/var/log/jb-vps}"
  local file
  if [[ -d "$base_dir" && ( $EUID -eq 0 || -w "$base_dir" ) ]]; then
    file="$base_dir/mnemosyneos.log"
  else
    local user_dir="${HOME:-/tmp}/.jb-vps/logs"
    mkdir -p "$user_dir"
    file="$user_dir/mnemosyneos.log"
  fi
  echo "$file"
}

LOG_FILE="$(choose_log_file)"

case "${1:-}" in
  view)
    if [[ -f "$LOG_FILE" ]]; then
      cat "$LOG_FILE"
    else
      echo "No Mnemosyneos log found at $LOG_FILE"
    fi
    ;;
  log)
    shift || true
    mkdir -p "$(dirname "$LOG_FILE")"
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$LOG_FILE" || {
      echo "Unable to write to $LOG_FILE. Try running scripts/fix-logs.sh." >&2
      exit 1
    }
    echo "Logged to: $LOG_FILE"
    ;;
  *)
    echo "Usage: $0 [view|log <message>]"
    ;;
esac
