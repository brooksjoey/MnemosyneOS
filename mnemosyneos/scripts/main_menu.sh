#!/usr/bin/env bash
# JB-VPS Main Menu System
set -euo pipefail

while true; do
  echo -e "\n==== JB-VPS Main Menu ===="
  echo "1) System Info"
  echo "2) Run Modules"
  echo "3) AI Assistant (Lucian Voss)"
  echo "4) View Mnemosyneos Log"
  echo "5) Backup VPS"
  echo "6) Monitor VPS"
  echo "7) Configure Firewall" 
  echo "8) Help"
  echo "9) Exit"
  read -rp "Select an option: " choice
  case "$choice" in
    1)
      uname -a
      ;;
    2)
      for mod in "$(dirname "$0")/../modules/"*.sh; do
        [ -f "$mod" ] && bash "$mod"
      done
      ;;
    3)
      bash "$(dirname "$0")/../areas/ai/menu.sh"
      ;;
    4)
      bash "$(dirname "$0")/../mnemosyneos/memory.sh" view
      ;;
    5)
      bash "$(dirname "$0")/../modules/backup.sh"
      ;;
    6)
      bash "$(dirname "$0")/../modules/monitoring.sh"
      ;;
    7)
      bash "$(dirname "$0")/../modules/firewall.sh"
      ;;
    8)
      bash "$(dirname "$0")/help_menu.sh"
      ;;
    9)
      echo "Exiting JB-VPS menu."
      exit 0
      ;;
    *)
      echo "Invalid option. Try again."
      ;;
  esac
done
