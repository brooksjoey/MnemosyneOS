#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 -m venv "$ROOT/.venv" 2>/dev/null || true
source "$ROOT/.venv/bin/activate"
if [ -f "$ROOT/requirements.txt" ]; then
  pip install --upgrade pip
  pip install -r "$ROOT/requirements.txt"
elif [ -f "$ROOT/pyproject.toml" ]; then
  pip install --upgrade pip
  pip install -e "$ROOT"
fi
python "$ROOT/services/mnemo/main.py" --host "${APP_HOST:-0.0.0.0}" --port "${APP_PORT:-8208}"
