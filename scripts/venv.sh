scripts/venv.sh
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.."; pwd)"
cd "$ROOT"

python3 -m venv "$ROOT/venv"
source "$ROOT/venv/bin/activate"
pip install --upgrade pip setuptools wheel
pip install -e .