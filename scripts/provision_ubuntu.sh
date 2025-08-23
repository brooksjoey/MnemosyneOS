scripts/provision_ubuntu.sh
#!/usr/bin/env bash
set -euo pipefail

# Base deps (Ubuntu 22.04+)
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3-pip \
  postgresql postgresql-contrib redis-server \
  build-essential curl ca-certificates pkg-config

# Create service user & directories
sudo useradd -r -m -d /opt/mnemo -s /usr/sbin/nologin mnemo || true
sudo mkdir -p /opt/mnemo /var/lib/mnemo/snapshots /etc/mnemo
sudo chown -R mnemo:mnemo /opt/mnemo /var/lib/mnemo
sudo chmod 700 /var/lib/mnemo/snapshots

echo "Remember to place backup key at /etc/mnemo/backup.key and 'chmod 400' it."