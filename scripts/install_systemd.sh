scripts/install_systemd.sh
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.."; pwd)"

sudo cp "$ROOT/deploy/mnemosyneos.service" /etc/systemd/system/
sudo cp "$ROOT/deploy/mnemo-worker.service" /etc/systemd/system/
sudo cp "$ROOT/deploy/mnemo-beat.service"   /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mnemosyneos mnemo-worker mnemo-beat
echo "systemd units installed. Use: sudo systemctl start mnemosyneos mnemo-worker mnemo-beat"