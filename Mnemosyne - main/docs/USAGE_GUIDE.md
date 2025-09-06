# JB-VPS Usage Guide

## Initial Setup
1. Clone the repo and run `setup.sh` as root.
2. Enter your desired admin username when prompted.
3. The menu will guide you through system info, running modules, and viewing logs.

## Menu Options
- **System Info:** Shows basic VPS details.
- **Run Modules:** Executes all scripts in `modules/` (system update, security hardening, etc.).
- **View Mnemosyneos Log:** Shows history of actions and changes.
- **Exit:** Quits the menu.

## Customization
- Add your own `.sh` scripts to `modules/` for new features.
- Edit menu scripts in `menu/` to add more options.
- Use `mnemosyneos/memory.sh log "message"` to record custom events.

## Troubleshooting
- If a module fails, check `/var/log/jb-vps-setup.log` and `/var/log/jb-vps-mnemosyneos.log` for details.
- For help, contact the repo owner or see the README.
